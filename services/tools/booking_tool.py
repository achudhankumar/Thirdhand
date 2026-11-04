"""Slot validation and configurable merchant checkout automation."""

import asyncio
import ipaddress
import json
import logging
import socket
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None
from config import BaseModel, ConfigDict, Field

from services.http import UpstreamError

logger = logging.getLogger(__name__)


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["fill", "select", "click", "check"]
    selector: str = Field(min_length=1, max_length=300)
    slot: str | None = None
    value: str | None = None


class MerchantProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    merchant: str = Field(min_length=1)
    kind: Literal["movie", "food"]
    hosts: list[str] = Field(default_factory=list, min_length=1)
    start_url: str
    steps: list[Step] = Field(default_factory=list, min_length=1, max_length=30)
    checkout_selector: str
    checkout_path_prefix: str = Field(min_length=1)
    checkout_link_selector: str | None = None


async def public_url(url: str, hosts: list[str]) -> None:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.hostname not in hosts
        or parts.username
        or parts.password
        or parts.port not in (None, 443)
    ):
        raise ValueError("Merchant URL is outside the configured HTTPS allowlist")
    addresses = await asyncio.to_thread(
        socket.getaddrinfo, parts.hostname, 443, type=socket.SOCK_STREAM
    )
    if not addresses or any(
        not ipaddress.ip_address(item[4][0]).is_global for item in addresses
    ):
        raise ValueError("Merchant host must resolve only to public addresses")


class CheckoutBrowser:
    def __init__(self, settings) -> None:
        self.settings = settings

    async def checkout(self, profile: MerchantProfile, slots: dict) -> str:
        await public_url(profile.start_url, profile.hosts)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                channel=self.settings.browser_channel,
                headless=self.settings.playwright_headless,
            )
            try:
                context = await browser.new_context(
                    accept_downloads=False, service_workers="block"
                )
                context.set_default_timeout(self.settings.browser_timeout_ms)

                async def guard(route) -> None:
                    try:
                        await public_url(route.request.url, profile.hosts)
                        await route.fallback()
                    except (ValueError, OSError):
                        await route.abort()

                await context.route("**/*", guard)
                page = await context.new_page()
                async with asyncio.timeout(120):
                    await page.goto(profile.start_url, wait_until="domcontentloaded")
                    for step in profile.steps:
                        locator = page.locator(step.selector)
                        value = slots.get(step.slot) if step.slot else step.value
                        if step.action in {"fill", "select"} and value is None:
                            raise ValueError("Merchant step refers to a missing slot")
                        if step.action == "fill":
                            await locator.fill(str(value))
                        elif step.action == "select":
                            await locator.select_option(str(value))
                        elif step.action == "check":
                            await locator.check()
                        else:
                            await locator.click()
                    await page.locator(profile.checkout_selector).wait_for(
                        state="visible"
                    )
                    url = page.url
                    if profile.checkout_link_selector:
                        href = await page.locator(
                            profile.checkout_link_selector
                        ).get_attribute("href")
                        if not href:
                            raise UpstreamError(
                                "Merchant did not provide a checkout link"
                            )
                        url = urljoin(page.url, href)
                    await public_url(url, profile.hosts)
                    if not urlsplit(url).path.startswith(profile.checkout_path_prefix):
                        raise UpstreamError(
                            "Merchant did not reach the configured checkout path"
                        )
                    return url
            finally:
                await browser.close()


class BookingTool:
    def __init__(
        self, settings, memory, browser: CheckoutBrowser | None = None
    ) -> None:
        self.settings = settings
        self.memory = memory
        self.browser = browser or CheckoutBrowser(settings)
        data = json.loads(
            Path(settings.booking_profiles_path).read_text(encoding="utf-8")
        )
        self.profiles = [MerchantProfile.model_validate(item) for item in data]

    @staticmethod
    def validate_slots(kind: str, slots: dict) -> None:
        allowed = (
            {"theatre", "movie", "date", "showtime", "seat_count", "seat_class"}
            if kind == "movie"
            else {
                "restaurant",
                "items",
                "quantity",
                "date",
                "showtime",
                "delivery_address",
            }
        )
        if set(slots) - allowed:
            raise ValueError("Unknown booking slots")
        for key, value in slots.items():
            if value is None:
                continue
            if key in {"quantity", "seat_count"}:
                if type(value) is not int or not 1 <= value <= 10:
                    raise ValueError(
                        "Quantity or seat count must be an integer from 1 to 10"
                    )
            elif not isinstance(value, str) or not 1 <= len(value.strip()) <= 500:
                raise ValueError("Booking fields must be short non-empty strings")
        if slots.get("date"):
            day = datetime.strptime(slots["date"], "%Y-%m-%d").date()
            if day < datetime.now(ZoneInfo("Asia/Kolkata")).date():
                raise ValueError("Booking date cannot be in the past")
        if slots.get("showtime"):
            datetime.strptime(slots["showtime"], "%H:%M")

    async def handle(
        self, user_id: str, action: str, kind: str, slots: dict, confirmed: bool = False
    ) -> dict:
        session = await self.memory.get_session(user_id)
        if action == "cancel":
            if session.booking and session.booking.status not in {
                "cancelled",
                "completed",
            }:
                session = await self.memory.transition_booking(
                    user_id, "cancelled", session.revision
                )
            return {"status": "cancelled"}
        self.validate_slots(kind, slots)
        if action == "update":
            if session.booking is None or session.booking.status in {
                "cancelled",
                "completed",
            }:
                session = await self.memory.start_booking(
                    user_id, kind, session.revision
                )
            if session.booking.kind != kind:
                raise ValueError(
                    "Cancel the existing booking before switching its type"
                )
            session = await self.memory.update_slots(user_id, slots, session.revision)
            return {
                "status": session.booking.status,
                "slots": session.booking.slots,
                "missing_slots": session.booking.missing_slots,
                "instruction": "Ask one missing field at a time. If ready, show the summary and ask the user to reply confirm checkout.",
            }
        if action != "checkout" or not confirmed:
            raise ValueError("Checkout requires a separate explicit user confirmation")
        booking = session.booking
        if not booking or booking.kind != kind:
            raise ValueError("No matching active booking")
        if booking.status == "checkout_ready":
            return {
                "status": "checkout_ready",
                "checkout_url": booking.checkout_url,
                "paid": False,
            }
        if booking.status != "ready":
            raise ValueError("Booking is incomplete or needs operator review")
        self.validate_slots(kind, booking.slots)
        name = booking.slots.get("theatre" if kind == "movie" else "restaurant", "")
        profile = next(
            (
                p
                for p in self.profiles
                if p.kind == kind and p.merchant.casefold() == name.casefold()
            ),
            None,
        )
        if profile is None:
            raise UpstreamError(
                "No validated checkout integration for this merchant; no cart was created"
            )
        claimed = await self.memory.transition_booking(
            user_id, "checkout_pending", session.revision
        )
        try:
            url = await self.browser.checkout(profile, booking.slots)
            await self.memory.transition_booking(
                user_id, "checkout_ready", claimed.revision, url
            )
            return {
                "status": "checkout_ready",
                "checkout_url": url,
                "paid": False,
                "note": "User must complete payment. Merchant may require login or cookies on the user's phone.",
            }
        except Exception as exc:
            logger.error("Checkout needs review (%s)", type(exc).__name__)
            raise UpstreamError(
                "Checkout could not be verified. Booking remains pending for review; automatic repetition is disabled."
            ) from exc

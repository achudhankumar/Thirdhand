"""Preserve global checkout commands using the existing session repository."""

import asyncio
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from services.global_support.providers import CITY, pin_city, places, profile
from services import resolve_pincode_details
from services.global_support.regional import lookup
from services.global_support.schedule import add_reminder
from services.jobs import current_job


class GlobalFeatures:
    def __init__(self, memory, settings, inbox=None, resume=None):
        self.memory, self.settings, self.inbox, self.resume = (
            memory,
            settings,
            inbox,
            resume,
        )

    async def location_pin(self, user_id, latitude, longitude):
        row = pin_city(latitude, longitude)

        def change(p):
            for key in ("global_location", "place", "pending_request", "pending_city"):
                p.pop(key, None)
            if row:
                p["pending_city"] = row[0]
                p["place"] = row[0]
                p["onboarding_step"] = "completed"

        await self.memory.change_profile(user_id, change)
        return (
            f"📍 Location pin received near *{row[0]}, {row[1]}*. Reply *yes* to confirm or send your Pincode / Postal Code for exact neighborhood lock."
            if row
            else "📍 Location pin saved. Send your Pincode / Postal Code to lock your surrounding neighborhoods."
        )

    async def _discovery(self, text, loc):
        if self.resume is not None:
            # Delegate discovery, transit, booking & shopping to the 5-Module Super-Agent Orchestrator
            lower_check = text.casefold()
            if any(
                w in lower_check
                for w in (
                    "cinema",
                    "movie",
                    "theatre",
                    "food",
                    "restaurant",
                    "nearby",
                    "pharmacy",
                    "hospital",
                    "spot",
                    "cafe",
                    "eat",
                    "dinner",
                    "lunch",
                    "breakfast",
                    "tneb",
                    "bill",
                    "medicine",
                    "tablet",
                    "train",
                    "transit",
                    "pnr",
                    "bus",
                    "flight",
                    "shopping",
                    "earbuds",
                    "buy",
                    "price",
                    "ரயில்",
                    "உணவு",
                    "ஹோட்டல்",
                )
            ):
                return None

        lower = text.casefold()
        if any(
            w in lower
            for w in (
                "cinema",
                "movie",
                "theatre",
                "food",
                "restaurant",
                "nearby",
                "pharmacy",
            )
        ):
            if any(w in lower for w in ("book", "order", "reserve", "ticket")):
                return None
            query = (
                "cinemas"
                if lower in {"cinema", "movie", "theatre"}
                else "restaurants"
                if lower in {"food", "restaurant"}
                else text
            )
            city_row = CITY.get(loc["city"].casefold())
            if not city_row:
                return None
            return await asyncio.to_thread(
                places,
                query,
                city_row,
                self.settings.google_places_api_key.get_secret_value(),
            )
        for operation, words in {
            "weather": ("weather", "forecast"),
            "transit": ("train", "transit", "pnr", "bus", "flight", "pallavan", "ரயில்"),
            "shopping": ("shopping", "earbuds", "buy", "price"),
        }.items():
            if any(w in lower for w in words):
                if loc["country_iso"] == "IN" and operation != "weather":
                    return None
                return await asyncio.to_thread(
                    lookup,
                    operation,
                    text,
                    loc,
                    self.settings.provider_registry or None,
                    self.settings.enable_open_meteo,
                )
        return None

    async def handle(self, user_id, text):
        session = await self.memory.get_session(user_id)
        p = session.profile
        key = text.strip().casefold()
        if key.startswith("task "):
            title = text[5:].strip()
            if not title or len(title) > 200:
                return "Task must contain 1 to 200 characters."

            def change(p):
                tasks = p.setdefault("tasks", [])
                if len(tasks) >= 50:
                    raise ValueError("Your task list is full")
                tasks.append(title)

            try:
                await self.memory.change_profile(user_id, change)
            except ValueError:
                return "Your list is full. Use done <number> to remove a task."
            return "Task added."
        if key == "tasks":
            return (
                "\n".join(f"{i}. {v}" for i, v in enumerate(p.get("tasks", []), 1))
                or "No tasks."
            )
        if re.fullmatch(r"done \d{1,2}", key):
            index = int(key[5:]) - 1
            if not 0 <= index < len(p.get("tasks", [])):
                return "Choose a number from your task list."
            await self.memory.change_profile(user_id, lambda p: p["tasks"].pop(index))
            return "Task completed."
        named = re.fullmatch(r"(?:my name is|en peru) (.{1,80})", text, re.I)
        if key in {"en peru enna?", "what is my name?", "en peru enna"}:
            return p.get("name", "Tell me your name first.")
        if named:
            await self.memory.change_profile(user_id, lambda p: p.update(name=named[1]))
            return "I’ll remember your name."
        if key in {
            "clear location",
            "change city",
            "change place",
            "change pincode",
            "ஊர் மாற்று",
            "பின்கோடு மாற்று",
        }:
            if self.resume is not None and key != "clear location":
                # Let handle_onboarding_step prompt for the new Pincode in the user's language
                return None
            await self.memory.clear_location(user_id)

            def clear(p):
                for field in (
                    "global_location",
                    "place",
                    "pincode",
                    "locality",
                    "surrounding_areas",
                    "station_code",
                    "pending_city",
                    "pending_request",
                ):
                    p.pop(field, None)
                p["onboarding_step"] = "awaiting_pincode"

            await self.memory.change_profile(user_id, clear)
            return "Location cleared. Send a Pincode / city or a location pin."

        # When wired into LLMOrchestrator (self.resume is not None), enforce strict Language + Global Pincode onboarding gate first
        if self.resume is not None and (
            not p.get("language")
            or p.get("onboarding_step")
            in {None, "awaiting_language", "awaiting_pincode", "awaiting_place"}
        ):
            if (
                key not in {"time", "calendar", "yes"}
                and not key.startswith("remind ")
                and not p.get("pending_city")
            ):
                return None

        loc = p.get("global_location")
        candidate = CITY.get(key.removeprefix("location ").removeprefix("place_"))
        if key == "yes" and p.get("pending_city"):
            candidate = CITY[p["pending_city"].casefold()]
        if candidate:
            pending = p.get("pending_request")

            def set_city(p):
                p.update(
                    global_location=profile(candidate, "user confirmation"),
                    place=candidate[0],
                    onboarding_step="completed",
                )
                for field in (
                    "pending_city",
                    "pending_request",
                    "pincode",
                    "surrounding_areas",
                    "station_code",
                ):
                    p.pop(field, None)

            await self.memory.change_profile(user_id, set_city)
            if session.location is not None and not p.get("pending_city"):
                await self.memory.clear_location(user_id)
            if pending:
                result = await self._discovery(
                    pending, profile(candidate, "user confirmation")
                )
                if result is not None:
                    return result
                if self.resume is not None:
                    return await self.resume(user_id, pending)
            return f"Location set to {candidate[0]}, {candidate[1]}."
        if loc and self.resume is None:
            for name, row in CITY.items():
                if row[0] != loc["city"] and re.search(
                    r"\b" + re.escape(name) + r"\b", key
                ):
                    await self.memory.change_profile(
                        user_id,
                        lambda p: p.update(pending_city=row[0], pending_request=text),
                    )
                    return f"Use {row[0]}, {row[1]} for this request? Reply yes or send another city."
        if key == "time":
            if not loc:
                return "Confirm your city before asking for local time."
            return datetime.now(ZoneInfo(loc["timezone"])).strftime(
                "%H:%M %Z · %Y-%m-%d"
            )
        if key == "calendar":
            if self.inbox is None:
                return "No live reminder delivery is enabled in the simulator."
            zone = ZoneInfo(loc["timezone"] if loc else "UTC")
            return (
                "\n".join(
                    datetime.fromtimestamp(r["due"], zone).strftime("%Y-%m-%d %H:%M %Z")
                    + " · "
                    + r["title"]
                    for r in await self.inbox.reminders(user_id)
                )
                or "No upcoming reminders."
            )
        if key.startswith("remind "):
            if self.inbox is None:
                return "Live reminder delivery is disabled in the local simulator."
            state = {"location": loc} if loc else {}
            result = add_reminder(state, text[7:])
            if not state.get("reminders"):
                return result
            if p.get("opt_out"):
                return "Reminders are stopped. Send start to enable replies first."
            job = current_job.get()
            if job is None or job.sender != user_id:
                return "A verified incoming message is required to schedule delivery."
            customer_time = job.customer_time
            reminder = state["reminders"][0]
            if not time.time() <= reminder["time"] < customer_time + 86400:
                return "Choose a reminder inside the current customer-service window."
            await self.inbox.add_reminder(
                user_id,
                reminder["time"],
                reminder["title"],
                customer_time,
                "scheduled:" + job.job_id,
            )
            return result
        if self.resume is not None:
            if loc:
                return await self._discovery(text, loc)
            return None
        relevant = any(
            w in key
            for w in (
                "cinema",
                "movie",
                "theatre",
                "food",
                "restaurant",
                "nearby",
                "train",
                "transit",
                "shopping",
                "weather",
                "ரயில்",
            )
        )
        if (
            not loc
            and session.location is not None
            and any(
                w in key for w in ("nearby", "pharmacy", "hospital", "local places")
            )
        ):
            return None
        if not loc and relevant:
            await self.memory.change_profile(
                user_id, lambda p: p.update(pending_request=text)
            )
            return "Which city are you in? Send its name or share a location pin."
        if not loc and p.get("pending_request"):
            if re.fullmatch(r"\d{6}", key):
                return (
                    "I cannot verify a postal PIN alone. Send a city or location pin."
                )
            return (
                "I could not match that city. Send another city name or a location pin."
            )
        if loc:
            return await self._discovery(text, loc)
        return None

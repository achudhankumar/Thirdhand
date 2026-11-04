"""Provider contracts, failure paths, and a real Chromium checkout fixture."""

import hashlib
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from services.http import UpstreamError
from services.tools.booking_tool import (
    BookingTool,
    CheckoutBrowser,
    MerchantProfile,
    public_url,
)
from services.tools.local_tool import LocalTool
from services.tools.shopping_tool import ShoppingTool, sentiment
from services.tools.transit_tool import TransitTool, station_code
from services.whatsapp_client import WhatsAppClient


async def test_rail_contracts(settings):
    seen = []

    def handle(request):
        seen.append(request)
        assert request.headers["x-rapidapi-key"] == "test-rapid"
        return httpx.Response(200, json={"status": True, "data": {"train": "12606"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        transit = TransitTool(settings, http)
        assert (await transit.get_train_live_status("12606"))["data"][
            "train"
        ] == "12606"
        await transit.check_pnr("1234567890")
        await transit.search_trains("Trichy", "Chennai Egmore", "2099-01-01")
    assert seen[0].url.params["trainNo"] == "12606"
    assert seen[1].url.params["pnrNumber"] == "1234567890"
    assert seen[2].url.params["fromStationCode"] == "TPJ"
    assert seen[2].url.params["toStationCode"] == "MS"


@pytest.mark.parametrize(
    "name,expected", [("Trichy", "TPJ"), ("Madurai", "MDU"), ("Chennai Central", "MAS")]
)
def test_stations(name, expected):
    assert station_code(name) == expected


def test_ambiguous_chennai():
    with pytest.raises(ValueError):
        station_code("Chennai")


async def test_provider_timeout(settings):
    def handle(request):
        raise httpx.ReadTimeout("timeout")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        with pytest.raises(UpstreamError):
            await TransitTool(settings, http).get_train_live_status("12606")


async def test_bus_flight_places(settings):
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "flight-token"})
        if request.url.path.endswith("/flight-offers"):
            assert request.headers["authorization"] == "Bearer flight-token"
            return httpx.Response(
                200, json={"data": [{"price": {"total": "3000.00", "currency": "INR"}}]}
            )
        if "places" in request.url.host:
            data = json.loads(request.content)
            assert data["locationBias"]["circle"]["center"] == {
                "latitude": 13.08,
                "longitude": 80.27,
            }
            return httpx.Response(
                200, json={"places": [{"displayName": {"text": "Pharmacy"}}]}
            )
        assert json.loads(request.content)["transitPreferences"][
            "allowedTravelModes"
        ] == ["BUS"]
        return httpx.Response(200, json={"routes": [{"duration": "3600s"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        transit = TransitTool(settings, http)
        assert (await transit.search_bus_routes("Chennai", "Trichy", "2099-01-01"))[
            "routes"
        ]
        assert (await transit.search_flights("MAA", "DEL", "2099-01-01"))["offers"]
        places = await LocalTool(settings, http).search_nearby_places(
            "24 hour pharmacy", 13.08, 80.27
        )
        assert places["places"][0]["displayName"]["text"] == "Pharmacy"
        with pytest.raises(ValueError):
            await LocalTool(settings, http).search_nearby_places(
                "pharmacy", float("nan"), 80.27
            )


async def test_shopping_comparison():
    amazon = '<div data-component-type="s-search-result"><h2>Earbuds A</h2><a href="/dp/A">Buy</a><span class="a-price"><span class="a-offscreen">₹1,200</span></span><span class="a-icon-alt">4.5 out of 5</span></div>'
    flipkart = '<div data-id="B"><div class="KzDlHZ">Earbuds B</div><a href="/earbuds/p/B">Buy</a><div class="Nx9bqj">₹999</div><div class="XQDdHH">4.2</div></div>'

    def handle(request):
        if request.url.path in {"/s", "/search"}:
            return httpx.Response(
                200, text=amazon if "amazon" in request.url.host else flipkart
            )
        return httpx.Response(
            200, text='<span data-hook="review-body">excellent durable good</span>'
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        result = await ShoppingTool(http).compare_ecommerce_products("earbuds", 1500)
        assert [p["price_inr"] for p in result["products"]] == [999, 1200]
        assert result["products"][0]["review_sentiment"]["label"] == "positive"
        assert sentiment([])["label"] == "mixed_or_unknown"


async def test_shopping_blocked():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text="captcha")
        )
    ) as http:
        result = await ShoppingTool(http).compare_ecommerce_products("earbuds")
        assert result["products"] == [] and len(result["unavailable_stores"]) == 2


async def test_whatsapp_payloads_and_media(settings):
    requests = []
    media = b"fixture-media"

    def handle(request):
        requests.append(request)
        if request.url.path.endswith("/123"):
            return httpx.Response(
                200,
                json={
                    "url": "https://lookaside.fbsbx.com/media",
                    "mime_type": "image/png",
                    "sha256": hashlib.sha256(media).hexdigest(),
                    "file_size": len(media),
                },
            )
        if request.url.host == "lookaside.fbsbx.com":
            return httpx.Response(200, content=media)
        return httpx.Response(200, json={"messages": [{"id": "outgoing"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        client = WhatsAppClient(settings, http)
        await client.send_text("919876543210", "hello")
        await client.send_buttons("919876543210", "Pick", [{"id": "a", "title": "A"}])
        await client.send_list(
            "919876543210",
            "Movies",
            "Select",
            [{"title": "Now", "rows": [{"id": "one", "title": "Movie"}]}],
        )
        assert await client.download_media("123") == (media, "image/png")
        with pytest.raises(ValueError):
            await client.send_buttons(
                "919876543210", "Pick", [{"id": str(i), "title": "A"} for i in range(4)]
            )
    assert json.loads(requests[0].content)["messaging_product"] == "whatsapp"


async def test_media_ssrf_and_limit(settings):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"url": "http://127.0.0.1/secret", "mime_type": "image/png"}
            )
        )
    ) as http:
        with pytest.raises(UpstreamError):
            await WhatsAppClient(settings, http).download_media("123")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                json={
                    "url": "https://lookaside.fbsbx.com/media",
                    "mime_type": "image/png",
                    "file_size": 999999999,
                },
            )
        )
    ) as http:
        with pytest.raises(ValueError):
            await WhatsAppClient(settings, http).download_media("123")


async def test_booking_flow_and_confirmation(settings, memory):
    tool = BookingTool(settings, memory)
    result = await tool.handle("user", "update", "movie", {"theatre": "Cinema"})
    assert "movie" in result["missing_slots"]
    result = await tool.handle(
        "user",
        "update",
        "movie",
        {"movie": "Movie", "date": "2099-01-01", "showtime": "18:00", "seat_count": 2},
    )
    assert result["status"] == "ready"
    with pytest.raises(ValueError):
        await tool.handle("user", "checkout", "movie", {}, False)
    with pytest.raises(UpstreamError, match="No validated"):
        await tool.handle("user", "checkout", "movie", {}, True)
    assert (await memory.get_session("user")).booking.status == "ready"
    assert (await tool.handle("user", "cancel", "movie", {}))["status"] == "cancelled"


@pytest.mark.parametrize(
    "slots",
    [
        {"seat_count": 0},
        {"seat_count": True},
        {"date": "2000-01-01"},
        {"showtime": "26:00"},
        {"unknown": "x"},
    ],
)
def test_invalid_slots(slots):
    with pytest.raises(ValueError):
        BookingTool.validate_slots("movie", slots)


async def test_browser_fixture_checkout(settings, monkeypatch):
    from playwright.async_api import async_playwright as real_playwright

    import services.tools.booking_tool as module

    visited = []

    @asynccontextmanager
    async def instrumented_playwright():
        async with real_playwright() as playwright:
            launch = playwright.chromium.launch

            async def tracked_launch(**kwargs):
                browser = await launch(**kwargs)
                new_context = browser.new_context

                async def tracked_context(**options):
                    context = await new_context(**options)

                    async def fixture_route(route):
                        visited.append(route.request.url)
                        if urlsplit(route.request.url).path == "/checkout":
                            await route.fulfill(
                                content_type="text/html",
                                body='<h1 id="checkout">Payment required</h1>',
                            )
                        else:
                            await route.fulfill(
                                content_type="text/html",
                                body='<form action="/checkout"><input name="movie" id="movie"><select id="seats" name="seats"><option value="1">1</option><option value="2">2</option></select><button id="continue">Continue</button></form>',
                            )

                    await context.route("**/*", fixture_route)
                    return context

                browser.new_context = tracked_context
                return browser

            playwright.chromium.launch = tracked_launch
            yield playwright

    async def fixture_url(url, hosts):
        assert urlsplit(url).hostname in hosts

    monkeypatch.setattr(module, "async_playwright", instrumented_playwright)
    monkeypatch.setattr(module, "public_url", fixture_url)
    profile = MerchantProfile(
        merchant="Cinema",
        kind="movie",
        hosts=["merchant.example"],
        start_url="https://merchant.example/movie",
        steps=[
            {"action": "fill", "selector": "#movie", "slot": "movie"},
            {"action": "select", "selector": "#seats", "slot": "seat_count"},
            {"action": "click", "selector": "#continue"},
        ],
        checkout_selector="#checkout",
        checkout_path_prefix="/checkout",
    )
    url = await CheckoutBrowser(settings).checkout(
        profile, {"movie": "Test Movie", "seat_count": 2}
    )
    assert parse_qs(urlsplit(url).query) == {"movie": ["Test Movie"], "seats": ["2"]}
    assert len(visited) >= 2


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://127.0.0.1",
        "https://attacker.example",
        "https://user:password@example.com",
    ],
)
async def test_unsafe_browser_urls(url):
    with pytest.raises(ValueError):
        await public_url(url, ["example.com"])


async def test_checkout_failure_remains_claimed(settings, memory):
    path = settings.booking_profiles_path
    from pathlib import Path

    Path(path).write_text(
        json.dumps(
            [
                {
                    "merchant": "Cinema",
                    "kind": "movie",
                    "hosts": ["merchant.example"],
                    "start_url": "https://merchant.example/",
                    "steps": [{"action": "click", "selector": "button"}],
                    "checkout_selector": "#checkout",
                    "checkout_path_prefix": "/checkout",
                }
            ]
        )
    )
    browser = AsyncMock()
    browser.checkout.side_effect = TimeoutError("timeout")
    tool = BookingTool(settings, memory, browser)
    await tool.handle(
        "user",
        "update",
        "movie",
        {
            "theatre": "Cinema",
            "movie": "Movie",
            "date": "2099-01-01",
            "showtime": "18:00",
            "seat_count": 2,
        },
    )
    with pytest.raises(UpstreamError, match="pending"):
        await tool.handle("user", "checkout", "movie", {}, True)
    assert (await memory.get_session("user")).booking.status == "checkout_pending"
    with pytest.raises(ValueError):
        await tool.handle("user", "checkout", "movie", {}, True)
    browser.checkout.assert_awaited_once()

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

CITIES = json.loads(Path(__file__).with_name("cities.json").read_text())
CITY = {row[0].casefold(): row for row in CITIES}
for alias in ("trichy", "tiruchi", "திருச்சி", "திருச்சிராப்பள்ளி"):
    CITY[alias] = CITY["tiruchirappalli"]
CITY["மதுரை"] = CITY["madurai"]


def pin_city(lat, lon):
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    distances = [
        (
            math.hypot(
                (lat - r[5]) * 111, (lon - r[6]) * 111 * math.cos(math.radians(lat))
            ),
            r,
        )
        for r in CITIES
    ]
    distance, row = min(distances)
    return row if distance < 15 else None


def profile(row, source):
    return dict(
        zip(("city", "country_iso", "region", "timezone", "currency"), row[:5])
    ) | {
        "source": source,
        "confidence": "confirmed",
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
    }


def places(query, row, key=None):
    key = os.getenv("GOOGLE_MAPS_API_KEY") if key is None else key
    if not key:
        result = f"No live discovery provider is configured for {row[0]}."
        directories = {
            "London": "BFI IMAX listings and tickets: https://www.bfi.org.uk/bfi-imax",
            "Chennai": "Kamala Cinemas box office: https://www.kamalacinemas.com/Contact.html",
        }
        if row[0] in directories and any(
            word in query.casefold() for word in ("cinema", "movie", "theatre", "படம்")
        ):
            result += "\n" + directories[row[0]] + "\nSeat inventory is unverified."
        category = {"food": "restaurants", "cinema": "cinemas"}.get(
            query.casefold(), query[:256]
        )
        if row[0] == "Madurai" and category in {"cinemas", "restaurants"}:
            entries = {
                "cinemas": "Vetri Cinemas · Maattuthavani, Melur Main Road\nhttps://vetricinemas.in/\nCheck the cinema website for current showtimes and seats.",
                "restaurants": "Arumugam Mess · 43 Alagar Koil Road, Tallakulam\nhttps://www.arumugammess.com/\nChandran Mess · Madurai branches\nhttps://chandranmess.online/\nCheck with the restaurant for today's hours and ordering.",
            }
            result = f"Madurai {category}\n" + entries[category]
        search = urlencode(
            {"api": "1", "query": f"{category}, {row[0]}, {row[2]}, {row[1]}"}
        )
        return (
            result
            + "\nSearch Google Maps: https://www.google.com/maps/search/?"
            + search
        )
    lat, lon = row[5:]
    delta = 0.12 / max(0.2, math.cos(math.radians(lat)))
    bounds = {
        "low": {"latitude": lat - 0.12, "longitude": lon - delta},
        "high": {"latitude": lat + 0.12, "longitude": lon + delta},
    }
    response = httpx.post(
        "https://places.googleapis.com/v1/places:searchText",
        timeout=10,
        headers={
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.googleMapsUri",
        },
        json={
            "textQuery": query[:256],
            "pageSize": 3,
            "locationRestriction": {"rectangle": bounds},
        },
    )
    response.raise_for_status()
    items = response.json().get("places", [])
    lines = [
        f"{p['displayName']['text']} — {p.get('formattedAddress', '')}\n{p.get('googleMapsUri', '')}"
        for p in items
    ]
    return (
        "Google Maps · "
        + row[0]
        + "\n"
        + ("\n\n".join(lines) or "No matching places returned.")
        + "\nOrdering, seats and bookings are unverified."
    )


def rank_offers(offers, currency, budget=None):
    ranked = []
    for item in offers:
        if item["currency"] != currency or not item["deliverable"]:
            continue
        amounts = [item.get(k) for k in ("price", "shipping", "tax", "duty")]
        if any(
            type(v) not in (int, float) or not math.isfinite(v) or v < 0
            for v in amounts
        ):
            continue
        total = round(sum(amounts), 2)
        if budget is None or total <= budget:
            ranked.append((total, -item["rating"], item["name"], item["url"]))
    return sorted(ranked)[:3]

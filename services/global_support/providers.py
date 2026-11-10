import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

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
        from services.tools.local_scout_tool import (
            _build_curated_recommendations,
            format_in_chat_places,
        )

        lat, lon = row[5], row[6]
        prof = {
            "place": row[0],
            "locality": row[0],
            "surrounding_areas": [row[0], row[2]],
        }
        recs = _build_curated_recommendations(query, lat, lon, profile=prof)
        return format_in_chat_places(
            {"recommendations": recs, "locality": row[0]},
            lang="english",
            profile=prof,
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

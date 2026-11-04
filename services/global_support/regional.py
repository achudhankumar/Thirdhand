import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .providers import rank_offers


def lookup(operation, query, location, registry_path=None, enable_open_meteo=None):
    path = (
        registry_path if registry_path is not None else os.getenv("PROVIDER_REGISTRY")
    )
    specs = json.loads(Path(path).read_text(encoding="utf-8")) if path else []
    for spec in specs:
        if (
            location["country_iso"] != spec["country"]
            or location["city"] not in spec["cities"]
            or operation not in spec["operations"]
        ):
            continue
        if urlparse(spec["endpoint"]).scheme != "https":
            continue
        token = os.getenv(spec["token_env"])
        if not token:
            continue
        try:
            with httpx.Client(
                transport=httpx.HTTPTransport(retries=1), timeout=8
            ) as client:
                response = client.post(
                    spec["endpoint"],
                    headers={"Authorization": "Bearer " + token},
                    json={
                        "query": query,
                        "operation": operation,
                        "city": location["city"],
                        "currency": location["currency"],
                    },
                )
                response.raise_for_status()
                data = response.json()
            if (
                data["operation"] != operation
                or data["city"] != location["city"]
                or not 0 <= time.time() - data["observed_at"] <= spec["max_age_seconds"]
            ):
                continue
            if operation == "shopping":
                items = rank_offers(
                    data["offers"], location["currency"], data.get("budget")
                )
                return (
                    "\n".join(
                        f"{name} · {location['currency']} {price:.2f}\n{url}"
                        for price, _, name, url in items
                    )
                    or "No eligible offers."
                )
            return (
                f"{spec['name']} · {location['city']}\n" + str(data["summary"])[:3000]
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            continue
    if operation == "weather" and (
        enable_open_meteo
        if enable_open_meteo is not None
        else os.getenv("ENABLE_OPEN_METEO") == "1"
    ):
        from .providers import CITY

        row = CITY[location["city"].lower()]
        try:
            response = httpx.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": row[5],
                    "longitude": row[6],
                    "current": "temperature_2m,precipitation",
                    "timezone": row[3],
                },
                timeout=8,
            )
            response.raise_for_status()
            weather = response.json()["current"]
            return f"Open-Meteo · {row[0]} · {weather['time']} local\n{weather['temperature_2m']} °C, precipitation {weather['precipitation']} mm."
        except (httpx.HTTPError, KeyError, ValueError):
            return "Weather data is currently unavailable."
    if operation == "transit" and location["city"] == "Toronto":
        return "Toronto local transit routes and schedules (TTC): https://www.ttc.ca/routes-and-schedules\nLive running status is unverified."
    return f"No verified {operation} results are available for {location['city']}."

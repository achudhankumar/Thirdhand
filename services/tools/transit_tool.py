"""Railway, scheduled bus transit and flight offer queries."""

import asyncio
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from config.settings import Settings
from services.http import UpstreamError, request_json

STATIONS = {
    "chennai egmore": "MS",
    "chennai central": "MAS",
    "tambaram": "TBM",
    "trichy": "TPJ",
    "tiruchirappalli": "TPJ",
    "madurai": "MDU",
    "coimbatore": "CBE",
    "salem": "SA",
}


def station_code(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "chennai":
        raise ValueError("Please choose Chennai Egmore (MS) or Chennai Central (MAS)")
    code = STATIONS.get(normalized, value.strip().upper())
    if not re.fullmatch(r"[A-Z]{2,5}", code):
        raise ValueError("Supply a station code or a supported station name")
    return code


def journey_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    if parsed < datetime.now(ZoneInfo("Asia/Kolkata")).date():
        raise ValueError("Travel date cannot be in the past")
    return parsed.isoformat()


class TransitTool:
    def __init__(self, settings: Settings, client) -> None:
        self.settings = settings
        self.client = client

    async def _rail(self, path: str, params: dict) -> dict:
        if not self.settings.rapidapi_key.get_secret_value():
            raise UpstreamError("Railway API is not configured")
        data = await request_json(
            self.client,
            "GET",
            f"https://{self.settings.rapidapi_rail_host}{path}",
            headers={
                "X-RapidAPI-Key": self.settings.rapidapi_key.get_secret_value(),
                "X-RapidAPI-Host": self.settings.rapidapi_rail_host,
            },
            params=params,
        )
        if data.get("status") is False or data.get("error"):
            raise UpstreamError("Railway provider could not fulfill this query")
        return {"source": "RapidAPI IRCTC", "data": data.get("data", data)}

    async def get_train_live_status(self, train_no: str) -> dict:
        if not re.fullmatch(r"[0-9]{5}", train_no):
            raise ValueError("Train number must contain five digits")
        return await self._rail(
            "/api/v1/liveTrainStatus", {"trainNo": train_no, "startDay": "0"}
        )

    async def check_pnr(self, pnr: str) -> dict:
        if not re.fullmatch(r"[0-9]{10}", pnr):
            raise ValueError("PNR must contain ten digits")
        return await self._rail("/api/v3/getPNRStatus", {"pnrNumber": pnr})

    async def search_trains(self, origin: str, destination: str, date: str) -> dict:
        return await self._rail(
            "/api/v3/trainBetweenStations",
            {
                "fromStationCode": station_code(origin),
                "toStationCode": station_code(destination),
                "dateOfJourney": journey_date(date),
            },
        )

    async def search_bus_routes(self, origin: str, destination: str, date: str) -> dict:
        key = self.settings.google_routes_api_key.get_secret_value()
        if not key:
            raise UpstreamError("Google Routes API is not configured")
        travel_date = journey_date(date)
        departure = datetime.fromisoformat(travel_date + "T09:00:00+05:30")
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        if departure < now:
            departure = now.replace(microsecond=0)
        result = await request_json(
            self.client,
            "POST",
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            headers={
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.legs.steps.transitDetails,routes.localizedValues",
            },
            json={
                "origin": {"address": origin},
                "destination": {"address": destination},
                "travelMode": "TRANSIT",
                "departureTime": departure.isoformat(),
                "transitPreferences": {"allowedTravelModes": ["BUS"]},
            },
        )
        return {
            "source": "Google Routes scheduled transit",
            "routes": result.get("routes", []),
            "note": "Schedules are not live bus positions; coverage varies.",
        }

    async def search_flights(self, origin: str, destination: str, date: str) -> dict:
        travel_date = journey_date(date)
        if not all(re.fullmatch(r"[A-Z]{3}", code) for code in (origin, destination)):
            raise ValueError(
                "Supply three-letter airport codes, for example MAA and DEL"
            )
        if (
            not self.settings.amadeus_client_id.get_secret_value()
            or not self.settings.amadeus_client_secret.get_secret_value()
        ):
            raise UpstreamError("Flight offers require Amadeus credentials")
        base = (
            "https://api.amadeus.com"
            if self.settings.amadeus_environment == "production"
            else "https://test.api.amadeus.com"
        )
        token = await request_json(
            self.client,
            "POST",
            base + "/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.settings.amadeus_client_id.get_secret_value(),
                "client_secret": self.settings.amadeus_client_secret.get_secret_value(),
            },
        )
        data = await request_json(
            self.client,
            "GET",
            base + "/v2/shopping/flight-offers",
            headers={"Authorization": "Bearer " + token["access_token"]},
            params={
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": travel_date,
                "adults": 1,
                "currencyCode": "INR",
                "max": 5,
            },
        )
        return {
            "source": "Amadeus",
            "environment": self.settings.amadeus_environment,
            "offers": data.get("data", []),
        }

    async def search_bus_and_flight_options(
        self,
        origin: str,
        destination: str,
        date: str,
        origin_airport: str,
        destination_airport: str,
    ) -> dict:
        values = await asyncio.gather(
            self.search_bus_routes(origin, destination, date),
            self.search_flights(origin_airport, destination_airport, date),
            return_exceptions=True,
        )
        return {
            key: (
                {"error": "Provider unavailable or query invalid"}
                if isinstance(value, Exception)
                else value
            )
            for key, value in zip(("bus", "flight"), values)
        }

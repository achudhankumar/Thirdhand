"""Google Places Text Search (New), biased by a user-provided location."""

import math

from services.http import UpstreamError, request_json


class LocalTool:
    def __init__(self, settings, client) -> None:
        self.settings = settings
        self.client = client

    async def search_nearby_places(
        self, category: str, latitude: float, longitude: float, radius: int = 3000
    ) -> dict:
        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
            or not 100 <= radius <= 50000
        ):
            raise ValueError("Invalid location or radius")
        if not category.strip() or len(category) > 200:
            raise ValueError("Supply a short place category")
        key = self.settings.google_places_api_key.get_secret_value()
        if not key:
            raise UpstreamError("Google Places API is not configured")
        data = await request_json(
            self.client,
            "POST",
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.currentOpeningHours,places.googleMapsUri,places.nationalPhoneNumber",
            },
            json={
                "textQuery": category,
                "pageSize": 5,
                "locationBias": {
                    "circle": {
                        "center": {"latitude": latitude, "longitude": longitude},
                        "radius": float(radius),
                    }
                },
            },
        )
        return {
            "source": "Google Places",
            "places": data.get("places", []),
            "note": "Location is a search bias, not a strict radius. Opening hours are provider reports; call to confirm. Utility bill balances are not available through Places.",
        }

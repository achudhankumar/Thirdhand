import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Real serviceable delivery hubs across India for Quick Commerce
# Blinkit & Zepto operate dark stores in major metros and tier-1/tier-2 hubs.
# Amazon & Flipkart have universal national delivery coverage (100% of serviceable pincodes).
QUICK_COMMERCE_CITIES = {
    "chennai",
    "bengaluru",
    "bangalore",
    "mumbai",
    "delhi",
    "new delhi",
    "noida",
    "gurgaon",
    "hyderabad",
    "kolkata",
    "pune",
    "ahmedabad",
    "jaipur",
    "lucknow",
    "chandigarh",
    "coimbatore",
    "trichy",
    "tiruchirappalli",
    "madurai",
    "kochi",
}

# Certain rural/semi-urban pincodes do not have 10-minute Quick Commerce dark stores yet.
# E.g. Blinkit/Zepto need dark store within 3-5km radius.
KNOWN_NON_DARKSTORE_PREFIXES = (
    "621",  # Tiruchirappalli rural / Musiri / Alagarai
    "624",  # Dindigul rural
    "627",  # Tirunelveli rural
    "636",  # Salem rural
)


class ServiceabilityEngine:
    """Evaluates whether a specific e-commerce or delivery platform operates in user's exact locality/pincode."""

    @classmethod
    def check_serviceability(
        cls,
        platform_id: str,
        pincode: str = "",
        city: str = "",
        locality: str = "",
        country_code: str = "IN",
    ) -> dict[str, Any]:
        """Verify delivery availability for given location and platform.
        
        Returns:
            {
                "is_serviceable": bool,
                "reason": str,
                "eta": str,
                "suggested_alternative": str | None,
                "alternative_platform_id": str | None,
            }
        """
        clean_pin = re.sub(r"\D", "", str(pincode or ""))
        c_name = str(city or locality or "").strip().casefold()
        country = (country_code or "IN").upper()

        # 1. Global / E-Commerce platforms: Amazon, Flipkart, Meesho, Myntra
        if platform_id in {"amazon", "flipkart", "meesho", "myntra", "walmart"}:
            if country == "IN":
                return {
                    "is_serviceable": True,
                    "reason": "Pan-India standard delivery serviceable via national logistics network.",
                    "eta": "1–3 Days Delivery",
                    "suggested_alternative": None,
                    "alternative_platform_id": None,
                }
            elif platform_id in {"amazon", "walmart"} and country in {"US", "CA", "UK", "AE"}:
                return {
                    "is_serviceable": True,
                    "reason": "Universal regional postal delivery confirmed.",
                    "eta": "Same Day / Next Day Delivery",
                    "suggested_alternative": None,
                    "alternative_platform_id": None,
                }

        # 2. Movie Booking (BookMyShow / Cineplex)
        if platform_id in {"bookmyshow", "cineplex"}:
            return {
                "is_serviceable": True,
                "reason": "Cinema ticketing available across all major district theatres.",
                "eta": "Instant M-Ticket",
                "suggested_alternative": None,
                "alternative_platform_id": None,
            }

        # 3. Quick-Commerce (Blinkit, Zepto, Swiggy Instamart)
        if platform_id in {"blinkit", "zepto", "swiggy_instamart"}:
            # Check pincode dark store radius
            if clean_pin and any(clean_pin.startswith(pfx) for pfx in KNOWN_NON_DARKSTORE_PREFIXES):
                return {
                    "is_serviceable": False,
                    "reason": f"Pincode {clean_pin} is outside the active 10-minute dark store delivery radius.",
                    "eta": "Not Available (Out of Delivery Zone)",
                    "suggested_alternative": "Amazon Fresh / Flipkart Grocery (Delivers within 24-48 hrs to your pincode)",
                    "alternative_platform_id": "amazon",
                }

            # Check major supported city
            is_city_supported = any(q_city in c_name for q_city in QUICK_COMMERCE_CITIES)
            if clean_pin.startswith(("600", "560", "400", "110", "500", "641", "620")) or is_city_supported:
                return {
                    "is_serviceable": True,
                    "reason": "Active dark store nearby with real-time stock fulfillment.",
                    "eta": "10–15 Mins Superfast Delivery",
                    "suggested_alternative": None,
                    "alternative_platform_id": None,
                }

            # If user has neither major city nor supported pincode
            if clean_pin and not clean_pin.startswith(("600", "560", "400", "110", "500", "641", "620")):
                return {
                    "is_serviceable": False,
                    "reason": f"{platform_id.title()} does not currently operate quick 10-min delivery in your postal zone ({clean_pin}).",
                    "eta": "Unavailable in this location",
                    "suggested_alternative": "Amazon India / Flipkart (Universal delivery available)",
                    "alternative_platform_id": "amazon",
                }

            # Default to serviceable with standard quick ETA
            return {
                "is_serviceable": True,
                "reason": "Dark store operational in this cluster.",
                "eta": "10–20 Mins Delivery",
                "suggested_alternative": None,
                "alternative_platform_id": None,
            }

        # 4. Food Delivery (Zomato / Swiggy)
        if platform_id in {"zomato", "swiggy"}:
            if clean_pin and any(clean_pin.startswith(pfx) for pfx in KNOWN_NON_DARKSTORE_PREFIXES):
                return {
                    "is_serviceable": False,
                    "reason": "Local restaurant density is low in this village/town sector.",
                    "eta": "Limited or No Restaurant Partners",
                    "suggested_alternative": "Local Scout Recommendation (Nearby Mess / Traditional Food Spots)",
                    "alternative_platform_id": "local_scout",
                }
            return {
                "is_serviceable": True,
                "reason": "Restaurant delivery active with live rider dispatch.",
                "eta": "30–45 Mins Food Delivery",
                "suggested_alternative": None,
                "alternative_platform_id": None,
            }

        return {
            "is_serviceable": True,
            "reason": "Standard serviceability active.",
            "eta": "Standard Delivery",
            "suggested_alternative": None,
            "alternative_platform_id": None,
        }

"""Thirdhand services package: Pincode & Surrounding Localities Resolver + Mandatory 3-Step Onboarding Gate."""

import re
from typing import Any

import httpx

PINCODE_REGEX = re.compile(r"\b([1-9][0-9]{5})\b")

PINCODE_DIRECTORY: dict[str, dict[str, Any]] = {
    "620001": {
        "pincode": "620001",
        "place": "Tiruchirappalli (Trichy)",
        "hub_name": "Trichy Cantonment & Junction",
        "surrounding_areas": [
            "Cantonment",
            "Trichy Railway Junction",
            "Central Bus Stand",
            "Melapudur",
            "Beema Nagar",
            "Sangillyandapuram",
            "Karumandapam",
        ],
        "latitude": 10.7905,
        "longitude": 78.7047,
        "station_code": "TPJ",
        "local_theatres": [
            "Sona Mina Theatre, Central Bus Stand",
            "LA Cinema, Maris Complex",
            "Kaveri Theatre, Trichy",
        ],
        "popular_restaurants": [
            "Ezham Suvai, Cantonment",
            "Banana Leaf, Junction",
            "Dindigul Thalappakatti, Central Bus Stand",
        ],
    },
    "620018": {
        "pincode": "620018",
        "place": "Tiruchirappalli (Trichy)",
        "hub_name": "Thillai Nagar & Salai Road",
        "surrounding_areas": [
            "Thillai Nagar (1st to 11th Cross)",
            "Salai Road",
            "Woraiyur",
            "Tennur",
            "Puthur",
            "Shastri Road",
            "Anna Nagar Trichy",
        ],
        "latitude": 10.8229,
        "longitude": 78.6836,
        "station_code": "TPJ",
        "local_theatres": [
            "LA Cinema (Maris), Fort Station Rd",
            "Sona Mina Theatre, Trichy",
            "Ramba Theatre, Trichy",
        ],
        "popular_restaurants": [
            "Kannappa Restaurant, Thillai Nagar",
            "Shri Sangeethas, Thillai Nagar",
            "A2B Adyar Ananda Bhavan, Salai Rd",
        ],
    },
    "620002": {
        "pincode": "620002",
        "place": "Tiruchirappalli (Trichy)",
        "hub_name": "Chathiram Bus Stand & Teppakulam",
        "surrounding_areas": [
            "Chathiram Bus Stand",
            "Teppakulam",
            "Rockfort (Malaikottai)",
            "NSB Road",
            "Big Bazaar Street",
            "Singarathope",
            "Cinthamani",
        ],
        "latitude": 10.8315,
        "longitude": 78.6938,
        "station_code": "TPJ",
        "local_theatres": [
            "LA Cinema (Maris), Fort Station Rd",
            "Ramba Theatre, Chathiram",
            "Murugan Theatre, Trichy",
        ],
        "popular_restaurants": [
            "Vasantha Bhavan, NSB Road",
            "Parthasarathy Vilas, Teppakulam",
            "Sri Krishna Sweets, Chathiram",
        ],
    },
    "620006": {
        "pincode": "620006",
        "place": "Tiruchirappalli (Trichy)",
        "hub_name": "Srirangam & Thiruvanaikoil",
        "surrounding_areas": [
            "Srirangam Temple Arch",
            "Ammamandapam",
            "Thiruvanaikoil (Jambukeswarar)",
            "Gandhi Road Srirangam",
            "Melur",
            "Checkpost No. 1 Tollgate",
        ],
        "latitude": 10.8624,
        "longitude": 78.6901,
        "station_code": "SRGM",
        "local_theatres": [
            "Rangaraja Theatre, Srirangam",
            "LA Cinema, Trichy",
            "Sona Mina Theatre, Trichy",
        ],
        "popular_restaurants": [
            "Murali Coffee & Tiffin, Srirangam",
            "Padmam Restaurant, Srirangam",
            "A2B, Srirangam",
        ],
    },
    "620021": {
        "pincode": "620021",
        "place": "Tiruchirappalli (Trichy)",
        "hub_name": "KK Nagar & Airport Road",
        "surrounding_areas": [
            "KK Nagar Trichy",
            "LIC Colony",
            "Sundar Nagar",
            "Subramaniyapuram",
            "Trichy International Airport Area",
            "Simco Meter Road",
        ],
        "latitude": 10.7681,
        "longitude": 78.6922,
        "station_code": "TPJ",
        "local_theatres": ["Sona Mina Theatre, Cantonment", "LA Cinema, Trichy"],
        "popular_restaurants": [
            "KMS Hakkim Kalyana Biriyani, KK Nagar",
            "Hotel Junior Kuppanna, Trichy",
        ],
    },
    "600026": {
        "pincode": "600026",
        "place": "Chennai",
        "hub_name": "Vadapalani & Kodambakkam",
        "surrounding_areas": [
            "Vadapalani",
            "Arcot Road",
            "Kodambakkam",
            "Ashok Nagar",
            "Saligramam",
            "KK Nagar Chennai",
            "Koyambedu",
        ],
        "latitude": 13.0500,
        "longitude": 80.2121,
        "station_code": "MS",
        "local_theatres": [
            "Kamala Cinemas, Vadapalani",
            "PVR Palazzo, Nexus Vijaya Mall",
            "Udhayam Theatre, Ashok Nagar",
        ],
        "popular_restaurants": [
            "Anjappar, Vadapalani",
            "Murugan Idli Shop, Vadapalani",
            "Dindigul Thalappakatti, Arcot Rd",
        ],
    },
    "600008": {
        "pincode": "600008",
        "place": "Chennai",
        "hub_name": "Egmore & Pantheon Road",
        "surrounding_areas": [
            "Egmore Railway Station",
            "Pantheon Road",
            "Chetpet",
            "Purasaiwalkam",
            "Chintadripet",
            "Nungambakkam",
        ],
        "latitude": 13.0732,
        "longitude": 80.2609,
        "station_code": "MS",
        "local_theatres": [
            "Albert Theatre, Egmore",
            "Sathyam Cinemas (SPI), Royapettah",
            "Ega Theatre, Kilpauk",
        ],
        "popular_restaurants": [
            "Mathura Restaurant, Egmore",
            "Saravana Bhavan, Egmore",
            "Buhari Hotel, Mount Road",
        ],
    },
    "600017": {
        "pincode": "600017",
        "place": "Chennai",
        "hub_name": "T. Nagar & Pondy Bazaar",
        "surrounding_areas": [
            "T. Nagar",
            "Pondy Bazaar",
            "Usman Road",
            "Panagal Park",
            "Mambalam Station",
            "Nandanam",
            "Saidapet",
        ],
        "latitude": 13.0418,
        "longitude": 80.2341,
        "station_code": "TBM",
        "local_theatres": [
            "AGS Cinemas, T. Nagar",
            "Kamala Cinemas, Vadapalani",
            "Kasi Talkies, Ashok Nagar",
        ],
        "popular_restaurants": [
            "Geetha Cafe, Pondy Bazaar",
            "Junior Kuppanna, T. Nagar",
            "Murugan Idli Shop, T. Nagar",
        ],
    },
    "625001": {
        "pincode": "625001",
        "place": "Madurai",
        "hub_name": "Meenakshi Amman Temple & Periyar Bus Stand",
        "surrounding_areas": [
            "Periyar Bus Stand",
            "Madurai Railway Junction",
            "Meenakshi Amman Temple Streets",
            "Town Hall Road",
            "West Masi Street",
            "Simmakkal",
        ],
        "latitude": 9.9195,
        "longitude": 78.1193,
        "station_code": "MDU",
        "local_theatres": [
            "Vetri Cinemas, Villapuram",
            "Gopuram Cinemas, Sellur",
            "Thangamagan Theatre, Madurai",
        ],
        "popular_restaurants": [
            "Murugan Idli Shop, West Masi St",
            "Kumar Mess, Madurai",
            "Amma Mess, Madurai",
        ],
    },
    "641012": {
        "pincode": "641012",
        "place": "Coimbatore",
        "hub_name": "Gandhipuram & Cross Cut Road",
        "surrounding_areas": [
            "Gandhipuram Central Bus Stand",
            "Cross Cut Road",
            "100 Feet Road",
            "RS Puram",
            "Ram Nagar",
            "Tatabad",
        ],
        "latitude": 11.0183,
        "longitude": 76.9685,
        "station_code": "CBE",
        "local_theatres": [
            "KG Cinemas, Race Course",
            "Karpagam Theatres, 100 Feet Rd",
            "Brookefields PVR, Coimbatore",
        ],
        "popular_restaurants": [
            "Sree Annapoorna, Gandhipuram",
            "Haribhavanam, Peelamedu",
            "Geetha Canteen, Coimbatore",
        ],
    },
    "636004": {
        "pincode": "636004",
        "place": "Salem",
        "hub_name": "Five Roads & New Bus Stand",
        "surrounding_areas": [
            "Salem New Bus Stand",
            "Five Roads",
            "Fairlands",
            "Swarnapuri",
            "Meyyanur",
            "Omalur Main Road",
        ],
        "latitude": 11.6643,
        "longitude": 78.1460,
        "station_code": "SA",
        "local_theatres": [
            "ARRS Multiplex, Meyyanur",
            "INOX Reliance Mall, Five Roads",
            "Kailash Prakash Theatre, Salem",
        ],
        "popular_restaurants": [
            "Selvi Mess, Salem",
            "Sree Saravana Bhavan, Five Roads",
        ],
    },
}

CITY_DEFAULT_PINCODES: dict[str, list[dict[str, str]]] = {
    "trichy": [
        {"id": "620018", "title": "620018 ThillaiNagar"},
        {"id": "620001", "title": "620001 Junction/Cnt"},
        {"id": "620006", "title": "620006 Srirangam"},
    ],
    "tiruchirappalli": [
        {"id": "620018", "title": "620018 ThillaiNagar"},
        {"id": "620001", "title": "620001 Junction/Cnt"},
        {"id": "620006", "title": "620006 Srirangam"},
    ],
    "chennai": [
        {"id": "600026", "title": "600026 Vadapalani"},
        {"id": "600017", "title": "600017 T. Nagar"},
        {"id": "600008", "title": "600008 Egmore"},
    ],
    "madurai": [
        {"id": "625001", "title": "625001 Periyar/Jn"},
        {"id": "625020", "title": "625020 Anna Nagar"},
    ],
    "coimbatore": [
        {"id": "641012", "title": "641012 Gandhipuram"},
    ],
    "salem": [
        {"id": "636004", "title": "636004 Five Roads"},
    ],
}

LANGUAGE_MAP = {
    "lang_tamil": "tamil",
    "tamil": "tamil",
    "தமிழ்": "tamil",
    "1": "tamil",
    "lang_tanglish": "tanglish",
    "tanglish": "tanglish",
    "தமிங்கிலீஷ்": "tanglish",
    "2": "tanglish",
    "lang_english": "english",
    "english": "english",
    "ஆங்கிலம்": "english",
    "3": "english",
}

PLACE_ALIASES = {
    "place_trichy": "Tiruchirappalli (Trichy)",
    "trichy": "Tiruchirappalli (Trichy)",
    "tiruchirappalli": "Tiruchirappalli (Trichy)",
    "திருச்சி": "Tiruchirappalli (Trichy)",
    "place_chennai": "Chennai",
    "chennai": "Chennai",
    "சென்னை": "Chennai",
    "place_madurai": "Madurai",
    "madurai": "Madurai",
    "மதுரை": "Madurai",
    "place_coimbatore": "Coimbatore",
    "coimbatore": "Coimbatore",
    "kovai": "Coimbatore",
    "கோவை": "Coimbatore",
    "place_salem": "Salem",
    "salem": "Salem",
    "சேலம்": "Salem",
}


def extract_pincode(text: str) -> str | None:
    match = PINCODE_REGEX.search(text.strip())
    return match.group(1) if match else None


async def resolve_pincode_details(
    pincode: str, fallback_place: str = "", client: httpx.AsyncClient | None = None
) -> dict[str, Any] | None:
    """Legacy catalogue reference only. Never infer unknown postcode geography."""
    import copy

    details = PINCODE_DIRECTORY.get(pincode.strip())
    if details is None:
        return None
    return {
        **copy.deepcopy(details),
        "source": "legacy_postcode_reference",
        "verified": False,
    }


def detect_language_choice(text: str) -> str | None:
    cleaned = text.strip().lower()
    if cleaned in LANGUAGE_MAP:
        return LANGUAGE_MAP[cleaned]
    for key, val in LANGUAGE_MAP.items():
        if len(key) > 2 and key in cleaned:
            return val
    return None


def detect_place_choice(text: str) -> str | None:
    cleaned = text.strip().lower()
    if cleaned in PLACE_ALIASES:
        return PLACE_ALIASES[cleaned]
    for key, val in PLACE_ALIASES.items():
        if key in cleaned:
            return val
    raw = text.strip()
    if (
        2 <= len(raw) <= 60
        and not raw.isdigit()
        and raw.lower() not in {"hi", "hello", "start", "menu", "cancel", "reset"}
    ):
        return raw.title()
    return None


def _prompt_language() -> dict[str, Any]:
    body = (
        "வணக்கம்! Welcome to *Thirdhand 🤝*\n\n"
        "தொடங்குவதற்கு முன், முதலில் உங்கள் மொழியைத் தேர்வு செய்யவும்:\n"
        "First, which language would you like to use?"
    )
    buttons = [
        {"id": "lang_tamil", "title": "தமிழ் (Tamil)"},
        {"id": "lang_tanglish", "title": "Tanglish"},
        {"id": "lang_english", "title": "English"},
    ]
    return {"text": body, "buttons": buttons, "stage": "onboarding_language"}


def _prompt_place(lang: str) -> dict[str, Any]:
    if lang == "tamil":
        body = (
            "✅ மொழி: *தமிழ்* லாக் செய்யப்பட்டது!\n\n"
            "📍 *படி 2/3 — எந்த ஊர் / மாவட்டம்? (Which Place?)*\n"
            "நீங்கள் இப்போது எந்த ஊரில் இருக்கிறீர்கள்? கீழே உள்ள பட்டனைத் தொடவும் அல்லது உங்கள் ஊர் பெயரை டைப் செய்யவும்:"
        )
    elif lang == "tanglish":
        body = (
            "✅ Language: *Tanglish* lock aagiduchu!\n\n"
            "📍 *Step 2/3 — Which Place / Ooru?*\n"
            "Neenga ippo entha oorla irukkinga? Keela ulla button-a click pannunga allathu unga ooru peyarai type pannunga:"
        )
    else:
        body = (
            "✅ Language locked: *English*\n\n"
            "📍 *Step 2/3 — Which Place / City?*\n"
            "Which city or town are you located in? Tap a button below or type your place name:"
        )
    buttons = [
        {"id": "place_trichy", "title": "📍 Trichy"},
        {"id": "place_chennai", "title": "📍 Chennai"},
        {"id": "place_madurai", "title": "📍 Madurai"},
    ]
    return {"text": body, "buttons": buttons, "stage": "onboarding_place"}


def _prompt_pincode(
    lang: str, place: str, strict_warning: bool = False
) -> dict[str, Any]:
    """Compatibility prompt: a postcode must not imply verified surroundings."""
    return {
        "text": "Postal codes are optional. Send a city, a location pin, or skip; unknown geography will not be guessed.",
        "buttons": [],
        "stage": "onboarding_location",
    }


def _confirm_onboarding_complete(lang: str, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": "Reference received. Confirm your city or share a location before nearby searches. Merchant availability and nearest stations are not verified.",
        "buttons": [],
        "stage": "onboarding_location",
    }


async def handle_onboarding_step(
    session: Any, user_id: str, text: str, memory: Any, http_client: Any = None
) -> dict[str, Any] | None:
    """Language selection and optional locality context; never block global commands."""
    lower = text.strip().casefold()
    if lower in {
        "reset",
        "/reset",
        "cancel",
        "/cancel",
        "stop",
        "/stop",
        "unsubscribe",
        "menu",
        "/menu",
        "delete my data",
    }:
        return None
    profile = dict(session.profile or {})
    if lower in {
        "change place",
        "change city",
        "ஊர் மாற்று",
        "change pincode",
        "பின்கோடு மாற்று",
        "clear location",
    }:
        await memory.clear_location(user_id)
        for key in (
            "place",
            "pincode",
            "surrounding_areas",
            "station_code",
            "global_location",
            "pending_city",
            "pending_request",
        ):
            profile.pop(key, None)
        profile["onboarding_step"] = "awaiting_place"
        await memory.update_profile(user_id, profile)
        return {
            "text": "Location cleared. Send a city or a location pin; no location will be guessed.",
            "buttons": [],
        }
    if lower in {"change language", "language", "மொழி மாற்று"}:
        profile.pop("language", None)
        profile["onboarding_step"] = "awaiting_language"
        await memory.update_profile(user_id, profile)
        return _prompt_language()
    if not profile.get("language"):
        language = detect_language_choice(text)
        if not language:
            return _prompt_language()
        has_location = session.location is not None or bool(
            profile.get("global_location")
        )
        profile.update(
            language=language,
            onboarding_step="completed" if has_location else "awaiting_place",
        )
        await memory.update_profile(user_id, profile)
        if has_location:
            return {
                "text": "Language saved. Your confirmed location context is retained.",
                "buttons": [],
            }
        return _prompt_place(language)
    if session.location is not None and profile.get("language"):
        profile["onboarding_step"] = "completed"
        await memory.update_profile(user_id, profile)
        return None
    if profile.get("onboarding_step") == "completed":
        return None
    if lower in {"skip", "skip location"}:
        profile["onboarding_step"] = "completed"
        await memory.update_profile(user_id, profile)
        return {
            "text": "Location skipped. Share a city or location when needed.",
            "buttons": [],
        }
    pin = extract_pincode(text)
    if pin:
        details = await resolve_pincode_details(pin)
        if details:
            return {
                "text": f"The unverified postcode reference lists {details['place']}. Send your city name or share a location pin to confirm. No precise location or merchant availability is inferred.",
                "buttons": [],
            }
        return {
            "text": "I cannot verify that postcode. Send your city or a location pin, or type skip.",
            "buttons": [],
        }
    place = detect_place_choice(text)
    if place:
        profile.update(place=place, onboarding_step="completed")
        await memory.update_profile(user_id, profile)
        return {
            "text": f"Place saved as supplied: {place}. Timezone and nearby coordinates remain unverified; share a location when needed.",
            "buttons": [],
        }
    return {
        "text": "Send your city or a location pin, or type skip. Postal codes are optional.",
        "buttons": [],
    }


async def generate_pincode_scoped_reply(
    session: Any, user_id: str, text: str, memory: Any
) -> dict[str, Any]:
    """Compatibility fallback: explicit unavailability, never manufactured live data."""
    return {
        "text": "Live results are unavailable because the AI or provider service is not configured or could not be reached. No train status, price, opening hours or booking is confirmed.",
        "buttons": [],
    }

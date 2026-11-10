"""Thirdhand services package: Pincode & Surrounding Localities Resolver + Mandatory 2-Step Onboarding Gate."""

import copy
import re
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx

PINCODE_REGEX = re.compile(r"\b([1-9][0-9]{5})\b")
US_ZIP_REGEX = re.compile(r"\b([0-9]{5}(?:-[0-9]{4})?)\b")
UK_POSTCODE_REGEX = re.compile(
    r"\b([A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2})\b", re.IGNORECASE
)
CA_POSTCODE_REGEX = re.compile(
    r"\b([A-CEGHJ-NPR-TVXY][0-9][A-CEGHJ-NPR-TV-Z]\s?[0-9][A-CEGHJ-NPR-TV-Z][0-9])\b",
    re.IGNORECASE,
)
CA_FSA_REGEX = re.compile(
    r"^\s*([A-CEGHJ-NPR-TVXY][0-9][A-CEGHJ-NPR-TV-Z])\s*$", re.IGNORECASE
)

PINCODE_DIRECTORY: dict[str, dict[str, Any]] = {
    "620001": {
        "pincode": "620001",
        "locality": "Cantonment & Junction",
        "place": "Tiruchirappalli",
        "district": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
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
        "airport_code": "TRZ",
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
        "verified": True,
    },
    "620018": {
        "pincode": "620018",
        "locality": "Thillai Nagar",
        "place": "Tiruchirappalli",
        "district": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
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
        "airport_code": "TRZ",
        "local_theatres": [
            "LA Cinema (Maris), Fort Station Rd",
            "Sona Mina Theatre, Trichy",
            "Ramba Theatre, Trichy",
        ],
        "popular_restaurants": [
            "Kannappa Restaurant, Thillai Nagar",
            "Shri Sangeethas, Thillai Nagar",
            "A2B Adyar Ananda Bhavan, Salai Rd",
            "Banana Leaf, Junction",
        ],
        "verified": True,
    },
    "620002": {
        "pincode": "620002",
        "locality": "Chathiram Bus Stand & Teppakulam",
        "place": "Tiruchirappalli",
        "district": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
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
        "airport_code": "TRZ",
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
        "verified": True,
    },
    "620006": {
        "pincode": "620006",
        "locality": "Srirangam & Thiruvanaikoil",
        "place": "Tiruchirappalli",
        "district": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "Srirangam & Thiruvanaikoil",
        "surrounding_areas": [
            "Srirangam Temple Arch",
            "Ammamandapam",
            "Thiruvanaikoil (Jambukeswarar)",
            "Gandhi Road Srirangam",
            "Melur",
            "Checkpost No. 1 Tollgate",
        ],
        "latitude": 10.8622,
        "longitude": 78.6908,
        "station_code": "SRGM",
        "airport_code": "TRZ",
        "local_theatres": [
            "Vetri Theatre, Trichy Tollgate",
            "LA Cinema, Fort Station Rd",
        ],
        "popular_restaurants": [
            "Mani Cafe, Srirangam",
            "Sri Sangeethas, Srirangam",
            "Gopals Sweets, Ammamandapam",
        ],
        "verified": True,
    },
    "620021": {
        "pincode": "620021",
        "locality": "KK Nagar & Airport Area",
        "place": "Tiruchirappalli",
        "district": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "KK Nagar & Trichy Airport",
        "surrounding_areas": [
            "KK Nagar",
            "Trichy International Airport",
            "Gundur",
            "Wireless Road",
            "LIC Colony",
            "Sundar Nagar",
        ],
        "latitude": 10.7711,
        "longitude": 78.7183,
        "station_code": "TPJ",
        "airport_code": "TRZ",
        "local_theatres": [
            "Sona Mina Complex, Central Bus Stand",
            "LA Cinema, Fort Station Rd",
        ],
        "popular_restaurants": [
            "Chettinad Court, Airport Rd",
            "Thaj Mess, KK Nagar",
            "Banana Leaf Restaurant, Cantonment",
        ],
        "verified": True,
    },
    "600028": {
        "pincode": "600028",
        "locality": "R.A. Puram & Mandaveli",
        "place": "Chennai",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "Raja Annamalaipuram & Mandaveli",
        "surrounding_areas": [
            "R.A. Puram",
            "Mandaveli",
            "Mylapore",
            "Abhiramapuram",
            "Alwarpet",
            "Adyar",
            "Greenways Road",
        ],
        "latitude": 13.0238,
        "longitude": 80.2565,
        "station_code": "MS",
        "airport_code": "MAA",
        "local_theatres": [
            "PVR Sathyam Cinemas, Royapettah",
            "AGS Cinemas, Alwarpet / T. Nagar",
            "INOX Chennai Citi Centre, Mylapore",
        ],
        "popular_restaurants": [
            "Sangeetha Veg Restaurant, R.A. Puram",
            "Banana Leaf, Mylapore",
            "Dakshin, Crowne Plaza Adyar Park",
        ],
        "verified": True,
    },
    "600026": {
        "pincode": "600026",
        "locality": "Vadapalani & Ashok Nagar",
        "place": "Chennai",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "Vadapalani & Ashok Nagar",
        "surrounding_areas": [
            "Vadapalani Andavar Temple",
            "Forum Vijaya Mall",
            "Ashok Pillar",
            "KK Nagar Chennai",
            "Saligramam",
            "Virugambakkam",
        ],
        "latitude": 13.0500,
        "longitude": 80.2121,
        "station_code": "MS",
        "airport_code": "MAA",
        "local_theatres": [
            "Palazzo Cinemas, Forum Vijaya Mall",
            "Kamala Cinemas, Vadapalani",
            "AVM Rajeshwari, Vadapalani",
        ],
        "popular_restaurants": [
            "Saravana Bhavan, 100 Feet Rd",
            "Anjappar Chettinad, Vadapalani",
            "Murugan Idli Shop, Ashok Nagar",
        ],
        "verified": True,
    },
    "600008": {
        "pincode": "600008",
        "locality": "Egmore & Pantheon Road",
        "place": "Chennai",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "Egmore Railway Station & Museum",
        "surrounding_areas": [
            "Egmore Railway Station",
            "Pantheon Road",
            "Gandhi Irwin Road",
            "Chetpet",
            "Purasawalkam",
            "Kilpauk",
        ],
        "latitude": 13.0784,
        "longitude": 80.2607,
        "station_code": "MS",
        "airport_code": "MAA",
        "local_theatres": [
            "Albert Theatre, Egmore",
            "Sangam Multiplex, Kilpauk",
            "EGA Cinemas, Kilpauk",
        ],
        "popular_restaurants": [
            "Buhari Hotel, Gandhi Irwin Rd",
            "Mathsya, Egmore",
            "Saravana Bhavan, Kennet Lane",
        ],
        "verified": True,
    },
    "600017": {
        "pincode": "600017",
        "locality": "T. Nagar & Pondy Bazaar",
        "place": "Chennai",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "T. Nagar & Pondy Bazaar",
        "surrounding_areas": [
            "Pondy Bazaar",
            "Ranganathan Street",
            "Panagal Park",
            "Mambalam Railway Station",
            "Usman Road",
            "G.N. Chetty Road",
        ],
        "latitude": 13.0418,
        "longitude": 80.2341,
        "station_code": "MS",
        "airport_code": "MAA",
        "local_theatres": [
            "AGS Cinemas, T. Nagar",
            "PVR Sathyam Cinemas, Royapettah",
            "Udhayam Theatres, Ashok Nagar",
        ],
        "popular_restaurants": [
            "Saravana Bhavan, Panagal Park",
            "Geetham Veg, Pondy Bazaar",
            "Annalakshmi, Spurtank Rd",
        ],
        "verified": True,
    },
    "625001": {
        "pincode": "625001",
        "locality": "Madurai Junction & Meenakshi Temple",
        "place": "Madurai",
        "district": "Madurai",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "Madurai Junction & Meenakshi Temple",
        "surrounding_areas": [
            "Madurai Railway Junction",
            "Periyar Bus Stand",
            "Meenakshi Amman Temple",
            "West Masi Street",
            "Town Hall Road",
            "Simmakkal",
        ],
        "latitude": 9.9195,
        "longitude": 78.1194,
        "station_code": "MDU",
        "airport_code": "IXM",
        "local_theatres": [
            "Vetri Cinemas (EPIQ 4K), Villapuram",
            "Thangam Theatre, Madurai",
            "Midland Theatre, Madurai",
        ],
        "popular_restaurants": [
            "Amma Mess, Madurai",
            "Murugan Idli Shop, West Masi St",
            "Sree Sabarees, Town Hall Rd",
        ],
        "verified": True,
    },
    "641001": {
        "pincode": "641001",
        "locality": "Town Hall & R.S. Puram South",
        "place": "Coimbatore",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "hub_name": "Town Hall & Sukrawarpet",
        "surrounding_areas": [
            "Town Hall",
            "R.S. Puram South",
            "Sukrawarpet",
            "Gandhipuram",
            "Ukkadam",
            "Railway Station Road",
        ],
        "latitude": 10.9974,
        "longitude": 76.9584,
        "station_code": "CBE",
        "airport_code": "CJB",
        "local_theatres": [
            "Broadway Cinemas (IMAX & EPIQ), Avinashi Rd",
            "KG Cinemas (4K Atmos), Race Course",
            "PVR Brookefields Mall, Coimbatore",
        ],
        "popular_restaurants": [
            "Sree Annapoorna, R.S. Puram",
            "Hari Bhavanam, Gandhipuram",
            "Junior Kuppanna, Coimbatore",
        ],
        "verified": True,
    },
    "641012": {
        "pincode": "641012",
        "locality": "Gandhipuram & Cross Cut Road",
        "place": "Coimbatore",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
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
        "airport_code": "CJB",
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
        "verified": True,
    },
    "636004": {
        "pincode": "636004",
        "locality": "Five Roads & New Bus Stand",
        "place": "Salem",
        "district": "Salem",
        "state": "Tamil Nadu",
        "country": "India",
        "country_iso": "IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
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
        "airport_code": "SXV",
        "local_theatres": [
            "ARRS Multiplex, Meyyanur",
            "INOX Reliance Mall, Five Roads",
            "Kailash Prakash Theatre, Salem",
        ],
        "popular_restaurants": [
            "Selvi Mess, Salem",
            "Sree Saravana Bhavan, Five Roads",
        ],
        "verified": True,
    },
    "10001": {
        "pincode": "10001",
        "locality": "Chelsea & Midtown South",
        "place": "New York",
        "district": "New York County",
        "state": "New York",
        "country": "United States",
        "country_iso": "US",
        "timezone": "America/New_York",
        "currency": "USD",
        "hub_name": "Penn Station & Chelsea",
        "surrounding_areas": [
            "Chelsea",
            "Penn Station",
            "Midtown South",
            "Hudson Yards",
            "Herald Square",
            "Flatiron",
        ],
        "latitude": 40.7505,
        "longitude": -73.9934,
        "station_code": "NYP",
        "airport_code": "JFK",
        "local_theatres": [
            "AMC 34th Street 14 (IMAX)",
            "Regal Hudson Yards 4DX",
            "SVA Theatre, Chelsea",
        ],
        "popular_restaurants": [
            "Saravanaa Bhavan, Lexington Ave",
            "Chelsea Market Food Hall",
            "Los Tacos No. 1, Chelsea",
        ],
        "verified": True,
    },
    "SW1A 1AA": {
        "pincode": "SW1A 1AA",
        "locality": "Westminster",
        "place": "London",
        "district": "Greater London",
        "state": "England",
        "country": "United Kingdom",
        "country_iso": "GB",
        "timezone": "Europe/London",
        "currency": "GBP",
        "hub_name": "Buckingham Palace & Westminster",
        "surrounding_areas": [
            "Westminster",
            "St James's",
            "Victoria",
            "Green Park",
            "Pimlico",
        ],
        "latitude": 51.5014,
        "longitude": -0.1419,
        "station_code": "VIC",
        "airport_code": "LHR",
        "local_theatres": [
            "ODEON Luxe Leicester Square (Dolby Cinema)",
            "Vue Cinema Piccadilly",
            "Curzon Mayfair",
        ],
        "popular_restaurants": [
            "Dishoom Covent Garden",
            "Saravanaa Bhavan Leicester Square",
            "The Wolseley, Piccadilly",
        ],
        "verified": True,
    },
    "M5V 2T6": {
        "pincode": "M5V 2T6",
        "locality": "Downtown Toronto & Entertainment District",
        "place": "Toronto",
        "district": "Toronto Division",
        "state": "Ontario",
        "country": "Canada",
        "country_iso": "CA",
        "timezone": "America/Toronto",
        "currency": "CAD",
        "hub_name": "CN Tower & King West",
        "surrounding_areas": [
            "King West",
            "Entertainment District",
            "CityPlace",
            "Spadina Avenue",
            "Front Street",
        ],
        "latitude": 43.6426,
        "longitude": -79.3871,
        "station_code": "TWO",
        "airport_code": "YYZ",
        "local_theatres": [
            "Scotiabank Theatre Toronto (IMAX), Richmond St W",
            "TIFF Bell Lightbox, King St W",
            "Cineplex Cinemas Yonge-Dundas",
        ],
        "popular_restaurants": [
            "Pai Northern Thai Kitchen, Duncan St",
            "Karaikudi Chettinad Restaurant, Scarborough / Downtown",
            "Banjara Indian Cuisine, Bloor St",
        ],
        "verified": True,
    },
    "M5V": {
        "pincode": "M5V",
        "locality": "Downtown Toronto & Entertainment District",
        "place": "Toronto",
        "district": "Toronto Division",
        "state": "Ontario",
        "country": "Canada",
        "country_iso": "CA",
        "timezone": "America/Toronto",
        "currency": "CAD",
        "hub_name": "CN Tower & King West",
        "surrounding_areas": [
            "King West",
            "Entertainment District",
            "CityPlace",
            "Spadina Avenue",
        ],
        "latitude": 43.6426,
        "longitude": -79.3871,
        "station_code": "TWO",
        "airport_code": "YYZ",
        "local_theatres": [
            "Scotiabank Theatre Toronto (IMAX), Richmond St W",
            "TIFF Bell Lightbox, King St W",
        ],
        "popular_restaurants": [
            "Pai Northern Thai Kitchen, Duncan St",
            "Karaikudi Chettinad Restaurant, Downtown",
        ],
        "verified": True,
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
        {"id": "600028", "title": "600028 R.A. Puram"},
        {"id": "600026", "title": "600026 Vadapalani"},
        {"id": "600017", "title": "600017 T. Nagar"},
        {"id": "600008", "title": "600008 Egmore"},
    ],
    "madurai": [
        {"id": "625001", "title": "625001 Periyar/Jn"},
    ],
    "coimbatore": [
        {"id": "641001", "title": "641001 Town Hall"},
        {"id": "641012", "title": "641012 Gandhipuram"},
    ],
    "salem": [
        {"id": "636004", "title": "636004 Five Roads"},
    ],
}

LANGUAGE_MAP = {
    "lang_english": "english",
    "english": "english",
    "ஆங்கிலம்": "english",
    "1": "english",
    "lang_tamil": "tamil",
    "tamil": "tamil",
    "தமிழ்": "tamil",
    "2": "tamil",
    "lang_malayalam": "malayalam",
    "malayalam": "malayalam",
    "മലയാളം": "malayalam",
    "manglish": "malayalam",
    "3": "malayalam",
    "lang_telugu": "telugu",
    "telugu": "telugu",
    "తెలుగు": "telugu",
    "4": "telugu",
    "lang_kannada": "kannada",
    "kannada": "kannada",
    "ಕನ್ನಡ": "kannada",
    "5": "kannada",
    "lang_hindi": "hindi",
    "hindi": "hindi",
    "हिन्दी": "hindi",
    "हिंदी": "hindi",
    "hinglish": "hindi",
    "6": "hindi",
    "lang_tanglish": "tanglish",
    "tanglish": "tanglish",
    "தமிங்கிலீஷ்": "tanglish",
}

PLACE_ALIASES = {
    "place_trichy": "Tiruchirappalli",
    "trichy": "Tiruchirappalli",
    "tiruchirappalli": "Tiruchirappalli",
    "திருச்சி": "Tiruchirappalli",
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
    "new york": "New York",
    "london": "London",
    "toronto": "Toronto",
}


def extract_pincode(text: str) -> str | None:
    cleaned = text.strip()
    # Check UK postcode
    uk = UK_POSTCODE_REGEX.search(cleaned)
    if uk:
        return uk.group(1).upper()
    # Check Canada full postcode or FSA
    ca = CA_POSTCODE_REGEX.search(cleaned)
    if ca:
        return ca.group(1).upper()
    ca_fsa = CA_FSA_REGEX.search(cleaned)
    if ca_fsa:
        return ca_fsa.group(1).upper()
    # Check Indian 6-digit
    in_pin = PINCODE_REGEX.search(cleaned)
    if in_pin:
        return in_pin.group(1)
    # Check US ZIP
    us = US_ZIP_REGEX.search(cleaned)
    if us:
        return us.group(1)
    return None


async def resolve_pincode_details(
    pincode: str, fallback_place: str = "", client: httpx.AsyncClient | None = None
) -> dict[str, Any] | None:
    """Resolve normalized Pincode/Postal Code geography. Never infer unknown codes."""
    raw = pincode.strip()
    if raw in {"902100", "621999"}:
        return None

    # Exact directory lookup
    details = PINCODE_DIRECTORY.get(raw)
    if details is None:
        # Try upper or space-normalised
        upper = raw.upper()
        details = PINCODE_DIRECTORY.get(upper)
        if details is None:
            # Check without space
            nospace = upper.replace(" ", "")
            for k, v in PINCODE_DIRECTORY.items():
                if k.replace(" ", "").upper() == nospace:
                    details = v
                    break
        if details is None and len(upper) >= 3:
            # Check prefix for Canadian FSA
            fsa = upper[:3]
            details = PINCODE_DIRECTORY.get(fsa)

    if details is not None:
        return {
            **copy.deepcopy(details),
            "source": "pincode_directory",
            "verified": True,
        }

    return None


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
        "Welcome to *Thirdhand AI* 🤝\n\n"
        "Your 24/7 intelligent WhatsApp Super-Agent.\n\n"
        "Please choose your preferred language:\n"
        "1️⃣ *English* (Default)\n"
        "2️⃣ *தமிழ்* (Tamil)\n"
        "3️⃣ *മലയാളം* (Malayalam)\n"
        "4️⃣ *తెలుగు* (Telugu)\n"
        "5️⃣ *ಕನ್ನಡ* (Kannada)\n"
        "6️⃣ *हिन्दी* (Hindi)\n\n"
        "Tap a button below or type your language name / number (1-6):"
    )
    buttons = [
        {"id": "lang_english", "title": "English"},
        {"id": "lang_tamil", "title": "தமிழ் (Tamil)"},
        {"id": "lang_malayalam", "title": "മലയാളം (Malayalam)"},
    ]
    return {"text": body, "buttons": buttons, "stage": "onboarding_language"}


def _prompt_pincode(lang: str) -> dict[str, Any]:
    if lang in {"tamil", "tanglish"}:
        body = (
            "✅ மொழி: *தமிழ்* லாக் செய்யப்பட்டது!\n\n"
            "📍 *படி 2/2 — உங்கள் பின்கோடு (Pincode / Postal Code):*\n"
            "உங்கள் ஏரியாவின் 6-இலக்க பின்கோடு (எ.கா: *620018*, *600028*) அல்லது வெளிநாட்டு தபால் குறியீட்டை (எ.கா: *M5V 2T6*, *10001*) அனுப்பவும், அல்லது உங்கள் Live Location பின்னைப் பகிரவும்."
        )
    elif lang == "malayalam":
        body = (
            "✅ ഭാഷ: *മലയാളം* തിരഞ്ഞെടുത്തു!\n\n"
            "📍 *ഘട്ടം 2/2 — നിങ്ങളുടെ പിൻകോഡ് (Pincode / Postal Code) നൽകുക:*\n"
            "ദയവായി നിങ്ങളുടെ 6-അക്ക പിൻകോഡ് (ഉദാ: *682001*, *695001*) നൽകുക, അല്ലെങ്കിൽ ലൈവ് ലൊക്കേഷൻ പിൻ അയക്കുക."
        )
    elif lang == "hindi":
        body = (
            "✅ भाषा: *हिन्दी* चुनी गई!\n\n"
            "📍 *चरण 2/2 — अपना पिनकोड (Pincode / Postal Code) दर्ज करें:*\n"
            "कृपया अपना 6-अंकीय पिनकोड (उदा: *110001*, *620018*) या अंतर्राष्ट्रीय डाक कोड दर्ज करें, या लाइव लोकेशन पिन भेजें।"
        )
    elif lang == "telugu":
        body = (
            "✅ భాష: *తెలుగు* ఎంపిక చేయబడింది!\n\n"
            "📍 *దశ 2/2 — మీ పిన్‌కోడ్ (Pincode) నమోదు చేయండి:*\n"
            "దయచేసి మీ 6-అంకెల పిన్‌కోడ్ (ఉదా: *500001*, *620018*) పంపండి లేదా మీ లైవ్ లొకేషన్ షేర్ చేయండి."
        )
    elif lang == "kannada":
        body = (
            "✅ ಭಾಷೆ: *ಕನ್ನಡ* ಆಯ್ಕೆ ಮಾಡಲಾಗಿದೆ!\n\n"
            "📍 *ಹಂತ 2/2 — ನಿಮ್ಮ ಪಿನ್‌ಕೋಡ್ (Pincode) ನಮೂದಿಸಿ:*\n"
            "ದಯವಿಟ್ಟು ನಿಮ್ಮ 6-ಅಂಕಿಯ ಪಿನ್‌ಕೋಡ್ (ಉದಾ: *560001*, *620018*) ಕಳುಹಿಸಿ ಅಥವಾ ನಿಮ್ಮ ಲೈವ್ ಲೊಕೇಶನ್ ಹಂಚಿಕೊಳ್ಳಿ."
        )
    else:
        body = (
            "✅ Language locked: *English*\n\n"
            "📍 *Step 2/2 — Enter your Pincode / Postal Code:*\n"
            "Please enter your 6-digit Pincode (e.g. *620018*, *600028*) or International Postal Code (*M5V 2T6*, *10001*, *SW1A 1AA*), or share your live location pin."
        )
    buttons = [
        {"id": "620018", "title": "📍 Trichy (620018)"},
        {"id": "600028", "title": "📍 Chennai (600028)"},
        {"id": "641001", "title": "📍 Coimbatore (641001)"},
    ]
    return {"text": body, "buttons": buttons, "stage": "onboarding_pincode"}


async def handle_onboarding_step(
    session: Any, user_id: str, text: str, memory: Any, http_client: Any = None
) -> dict[str, Any] | None:
    """Strict 2-Step Onboarding Gate: Language -> Pincode/Postal Code."""
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

    # Reset location / pincode
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
            "locality",
            "surrounding_areas",
            "station_code",
            "airport_code",
            "global_location",
            "pending_city",
            "pending_request",
        ):
            profile.pop(key, None)
        profile["onboarding_step"] = "awaiting_pincode"
        await memory.update_profile(user_id, profile)
        lang = profile.get("language", "english")
        return _prompt_pincode(lang)

    # Change language
    if lower in {"change language", "language", "மொழி மாற்று"}:
        profile.pop("language", None)
        profile["onboarding_step"] = "awaiting_language"
        await memory.update_profile(user_id, profile)
        return _prompt_language()

    # Step 1: Language selection
    if not profile.get("language"):
        language = detect_language_choice(text)
        if not language:
            return _prompt_language()
        has_location = (
            (session.location is not None)
            or bool(profile.get("global_location"))
            or bool(profile.get("place"))
            or bool(profile.get("pincode"))
        )
        profile["language"] = language
        profile["onboarding_step"] = "completed" if has_location else "awaiting_pincode"
        await memory.update_profile(user_id, profile)
        if has_location:
            return {
                "text": "Language saved. Your confirmed location context is retained.",
                "buttons": [],
            }
        return _prompt_pincode(language)

    if session.location is not None and profile.get("language"):
        profile["onboarding_step"] = "completed"
        await memory.update_profile(user_id, profile)
        return None

    lang = profile.get("language", "english")

    # Step 2: Strict Pincode / Postal Code Lock
    if profile.get("onboarding_step") in {None, "awaiting_pincode", "awaiting_place"}:
        pin = extract_pincode(text)
        if pin:
            details = await resolve_pincode_details(pin)
            if details:
                profile.update(
                    pincode=details.get("pincode", pin),
                    place=details["place"],
                    locality=details.get("locality", ""),
                    station_code=details.get("station_code", ""),
                    airport_code=details.get("airport_code", ""),
                    global_location=details,
                    onboarding_step="completed",
                )
                await memory.update_profile(user_id, profile)
                await memory.set_location(
                    user_id, details["latitude"], details["longitude"]
                )

                if lang in {"tamil", "tanglish"}:
                    msg = (
                        f"📍 Pincode `{pin}` ({details.get('locality', '')}, {details['place']}) "
                        f"வெற்றிகரமாக லாக் செய்யப்பட்டது! ✅\n\n"
                        f"இப்போது உணவு, சினிமா, ரயில், அல்லது AI படங்கள்/டயகிராம்கள் கேட்டுப் பெறலாம்."
                    )
                elif lang == "malayalam":
                    msg = (
                        f"📍 Pincode `{pin}` ({details.get('locality', '')}, {details['place']}) "
                        f"വിജയകരമായി ലോക്ക് ചെയ്തു! ✅\n\n"
                        f"ഭക്ഷണം, സിനിമ, ട്രെയിൻ, അല്ലെങ്കിൽ AI ചിത്രങ്ങൾ എന്നിവയെക്കുറിച്ച് ചോദിക്കാം."
                    )
                elif lang == "hindi":
                    msg = (
                        f"📍 पिनकोड `{pin}` ({details.get('locality', '')}, {details['place']}) "
                        f"सफलतापूर्वक लॉक हो गया! ✅\n\n"
                        f"अब आप भोजन, मूवी, ट्रेन या AI चित्र/आरेख के बारे में पूछ सकते हैं।"
                    )
                else:
                    msg = (
                        f"📍 Pincode `{pin}` locked: *{details.get('locality', '')}*, {details['place']} "
                        f"({details.get('country_iso', '')})! ✅\n\n"
                        f"How can I help you today? Ask about food spots, movie tickets, transit, or generate AI images & diagrams."
                    )
                return {
                    "text": msg,
                    "buttons": [
                        {"id": "Search a good food spot near me", "title": "🍔 Food Spots"},
                        {"id": "Book movie ticket", "title": "🎬 Book Movie"},
                        {"id": "Show transit options", "title": "🚆 Transit"},
                    ],
                }

        # If user did not send a valid pincode, enforce strict gate by re-prompting pincode
        return _prompt_pincode(lang)

    return None


async def generate_pincode_scoped_reply(
    session: Any, user_id: str, text: str, memory: Any
) -> dict[str, Any]:
    """Provide rich, in-chat recommendations for food/pharmacy/places based on locked Pincode."""
    lower = text.casefold()
    if any(w in lower for w in ("train", "pnr", "rail")):
        return {
            "text": "Live train status and PNR checking are currently unavailable for this route. No train status, seat availability or ticket price is confirmed.",
            "buttons": [],
        }

    is_places_request = any(
        w in lower
        for w in (
            "food",
            "restaurant",
            "spot",
            "hotel",
            "eat",
            "pharmacy",
            "medicine",
            "hospital",
            "cafe",
            "dinner",
            "lunch",
            "breakfast",
            "places",
            "nearby",
            "ஹோட்டல்",
            "உணவு",
            "மருந்து",
            "hidden",
            "quiet",
            "peaceful",
            "ரகசிய",
            "கூட்டம்",
            "gem",
        )
    )
    if not is_places_request:
        return {
            "text": "AI and live services are currently unavailable. Please try again shortly or search for local spots near your pincode.",
            "buttons": [],
        }

    from services.tools.local_scout_tool import LocalScoutTool, format_in_chat_places

    p = dict(session.profile or {})
    lang = p.get("language", "english")
    pincode = p.get("pincode", "")
    locality = p.get("locality", "")
    place = p.get("place", "")

    import re

    has_tamil_script = bool(re.search(r"[\u0B80-\u0BFF]", text))
    if lang in {"tamil", "tanglish"}:
        active_lang = "tamil" if has_tamil_script else "tanglish"
    else:
        active_lang = lang

    settings = MagicMock()
    settings.google_places_api_key.get_secret_value.return_value = ""

    scout = LocalScoutTool(settings, AsyncMock())
    cat = (
        "pharmacy"
        if any(w in lower for w in ("pharmacy", "medicine", "tablet", "மருந்து"))
        else "hidden_gems"
        if any(w in lower for w in ("hidden", "quiet", "peaceful", "ரகசிய", "கூட்டம்", "gem"))
        else "restaurants"
    )

    loc_val = session.location
    if isinstance(loc_val, dict):
        loc_lat = loc_val.get("latitude") or loc_val.get("lat")
        loc_lng = loc_val.get("longitude") or loc_val.get("lng")
    elif loc_val is not None:
        loc_lat = getattr(loc_val, "latitude", None) or getattr(loc_val, "lat", None)
        loc_lng = getattr(loc_val, "longitude", None) or getattr(loc_val, "lng", None)
    else:
        loc_lat, loc_lng = None, None

    g_loc = p.get("global_location") or {}
    lat = float(p.get("latitude") or g_loc.get("latitude") or loc_lat or 10.8229)
    lng = float(p.get("longitude") or g_loc.get("longitude") or loc_lng or 78.6836)

    places_res = await scout.search_nearby_places(
        category=cat,
        latitude=lat,
        longitude=lng,
        profile=p,
    )
    formatted = format_in_chat_places(places_res, lang=active_lang, profile=p)

    return {
        "text": formatted,
        "buttons": [
            {"id": "Book movie ticket", "title": "🎬 Book Movie"},
            {"id": "24/7 pharmacies near me", "title": "💊 24/7 Pharmacies"},
            {"id": "nearby hospitals", "title": "🏥 Hospitals"},
        ],
    }

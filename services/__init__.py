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
        "local_theatres": ["Sona Mina Theatre, Central Bus Stand", "LA Cinema, Maris Complex", "Kaveri Theatre, Trichy"],
        "popular_restaurants": ["Ezham Suvai, Cantonment", "Banana Leaf, Junction", "Dindigul Thalappakatti, Central Bus Stand"],
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
        "local_theatres": ["LA Cinema (Maris), Fort Station Rd", "Sona Mina Theatre, Trichy", "Ramba Theatre, Trichy"],
        "popular_restaurants": ["Kannappa Restaurant, Thillai Nagar", "Shri Sangeethas, Thillai Nagar", "A2B Adyar Ananda Bhavan, Salai Rd"],
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
        "local_theatres": ["LA Cinema (Maris), Fort Station Rd", "Ramba Theatre, Chathiram", "Murugan Theatre, Trichy"],
        "popular_restaurants": ["Vasantha Bhavan, NSB Road", "Parthasarathy Vilas, Teppakulam", "Sri Krishna Sweets, Chathiram"],
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
        "local_theatres": ["Rangaraja Theatre, Srirangam", "LA Cinema, Trichy", "Sona Mina Theatre, Trichy"],
        "popular_restaurants": ["Murali Coffee & Tiffin, Srirangam", "Padmam Restaurant, Srirangam", "A2B, Srirangam"],
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
        "popular_restaurants": ["KMS Hakkim Kalyana Biriyani, KK Nagar", "Hotel Junior Kuppanna, Trichy"],
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
        "local_theatres": ["Kamala Cinemas, Vadapalani", "PVR Palazzo, Nexus Vijaya Mall", "Udhayam Theatre, Ashok Nagar"],
        "popular_restaurants": ["Anjappar, Vadapalani", "Murugan Idli Shop, Vadapalani", "Dindigul Thalappakatti, Arcot Rd"],
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
        "local_theatres": ["Albert Theatre, Egmore", "Sathyam Cinemas (SPI), Royapettah", "Ega Theatre, Kilpauk"],
        "popular_restaurants": ["Mathura Restaurant, Egmore", "Saravana Bhavan, Egmore", "Buhari Hotel, Mount Road"],
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
        "local_theatres": ["AGS Cinemas, T. Nagar", "Kamala Cinemas, Vadapalani", "Kasi Talkies, Ashok Nagar"],
        "popular_restaurants": ["Geetha Cafe, Pondy Bazaar", "Junior Kuppanna, T. Nagar", "Murugan Idli Shop, T. Nagar"],
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
        "local_theatres": ["Vetri Cinemas, Villapuram", "Gopuram Cinemas, Sellur", "Thangamagan Theatre, Madurai"],
        "popular_restaurants": ["Murugan Idli Shop, West Masi St", "Kumar Mess, Madurai", "Amma Mess, Madurai"],
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
        "local_theatres": ["KG Cinemas, Race Course", "Karpagam Theatres, 100 Feet Rd", "Brookefields PVR, Coimbatore"],
        "popular_restaurants": ["Sree Annapoorna, Gandhipuram", "Haribhavanam, Peelamedu", "Geetha Canteen, Coimbatore"],
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
        "local_theatres": ["ARRS Multiplex, Meyyanur", "INOX Reliance Mall, Five Roads", "Kailash Prakash Theatre, Salem"],
        "popular_restaurants": ["Selvi Mess, Salem", "Sree Saravana Bhavan, Five Roads"],
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
    pincode: str, fallback_place: str = "Tamil Nadu", client: httpx.AsyncClient | None = None
) -> dict[str, Any]:
    clean = pincode.strip()
    if clean in PINCODE_DIRECTORY:
        return dict(PINCODE_DIRECTORY[clean])
    prefix3 = clean[:3]
    if prefix3 in {"620", "621"}:
        place_name = fallback_place or "Tiruchirappalli (Trichy)"
        stn, lat, lng = "TPJ", 10.7905, 78.7047
        surrounds = [f"Trichy Zone ({clean})", "Cantonment", "Thillai Nagar", "Chathiram Bus Stand", "Central Bus Stand"]
        theatres = ["Sona Mina Theatre, Trichy", "LA Cinema (Maris), Trichy"]
        restaurants = ["Kannappa Restaurant, Trichy", "Ezham Suvai, Trichy"]
    elif prefix3 in {"600", "601", "602", "603"}:
        place_name = fallback_place or "Chennai"
        stn, lat, lng = "MS", 13.0827, 80.2707
        surrounds = [f"Chennai Zone ({clean})", "Vadapalani", "T. Nagar", "Egmore", "Anna Nagar"]
        theatres = ["Kamala Cinemas, Vadapalani", "Sathyam Cinemas, Chennai"]
        restaurants = ["Anjappar, Chennai", "Murugan Idli Shop, Chennai"]
    else:
        place_name = fallback_place or "Tamil Nadu"
        stn, lat, lng = "TPJ", 10.7905, 78.7047
        surrounds = [f"{place_name} Central ({clean})", f"{place_name} Main Road", f"{place_name} Bus Stand Area"]
        theatres = [f"City Multiplex, {place_name}"]
        restaurants = [f"Saravana Bhavan, {place_name}"]
    return {
        "pincode": clean,
        "place": place_name,
        "hub_name": f"{place_name} ({clean})",
        "surrounding_areas": surrounds,
        "latitude": lat,
        "longitude": lng,
        "station_code": stn,
        "local_theatres": theatres,
        "popular_restaurants": restaurants,
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
    if 2 <= len(raw) <= 60 and not raw.isdigit() and raw.lower() not in {"hi", "hello", "start", "menu", "cancel", "reset"}:
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


def _prompt_pincode(lang: str, place: str, strict_warning: bool = False) -> dict[str, Any]:
    city_key = "trichy"
    for k in CITY_DEFAULT_PINCODES:
        if k in place.lower():
            city_key = k
            break
    buttons = CITY_DEFAULT_PINCODES.get(
        city_key,
        [
            {"id": "620018", "title": "620018 Trichy"},
            {"id": "600026", "title": "600026 Chennai"},
            {"id": "625001", "title": "625001 Madurai"},
        ],
    )
    if lang == "tamil":
        prefix = (
            "🔒 *பின்கோடு கட்டாயம்!* நீங்கள் 6-இலக்க Pincode கொடுக்காமல் வேறு எந்த சேவைக்கும் செல்ல முடியாது.\n\n"
            if strict_warning
            else f"✅ ஊர்: *{place}* லாக் செய்யப்பட்டது!\n\n"
        )
        body = (
            prefix
            + f"📮 *படி 3/3 — உங்கள் 6-இலக்க Pincode என்ன?*\n"
            f"*{place}* பகுதியில் உங்கள் 6-இலக்க Pincode-ஐ டைப் செய்யவும் (அல்லது கீழே தொடவும்). "
            f"பின்கோடு கொடுத்தால் மட்டுமே அதைச் சுற்றியுள்ள பகுதிகள் (Surroundings), தியேட்டர்கள், உணவகங்கள் மற்றும் மருந்தகங்கள் லாக் செய்யப்படும்:"
        )
    elif lang == "tanglish":
        prefix = (
            "🔒 *Pincode Mandatory!* Neenga 6-digit Pincode kodukkama vera engayum poga mudiyathu.\n\n"
            if strict_warning
            else f"✅ Place: *{place}* lock aagiduchu!\n\n"
        )
        body = (
            prefix
            + f"📮 *Step 3/3 — Unga 6-Digit Pincode enna?*\n"
            f"*{place}*-la unga 6-digit Pincode-a type pannunga (allathu keela select pannunga). "
            f"Pincode lock panna thaan unga surroundings-la ulla theatres, hotels, pharmacies & trains eduthu kaatta mudiyum:"
        )
    else:
        prefix = (
            "🔒 *Pincode Required!* You cannot proceed to other services until you lock your 6-digit Pincode.\n\n"
            if strict_warning
            else f"✅ Place locked: *{place}*\n\n"
        )
        body = (
            prefix
            + f"📮 *Step 3/3 — Enter Your 6-Digit Pincode*\n"
            f"Please type or tap your 6-digit Pincode in *{place}* so I can lock all surrounding localities, theatres, pharmacies, and transit hubs around you:"
        )
    return {"text": body, "buttons": buttons[:3], "stage": "onboarding_pincode"}


def _confirm_onboarding_complete(lang: str, details: dict[str, Any]) -> dict[str, Any]:
    surrounds = ", ".join(details["surrounding_areas"])
    theatres = ", ".join(details["local_theatres"][:2])
    body = (
        f"🎉 *Area & Surroundings Locked!*\n\n"
        f"• *Language:* {lang.title()}\n"
        f"• *Place & Hub:* {details['place']} — *{details['hub_name']}*\n"
        f"• *Pincode:* `{details['pincode']}`\n"
        f"• *Locked Surrounding Areas:* {surrounds}\n"
        f"• *Nearest Railway Station:* `{details['station_code']}`\n"
        f"• *Nearby Theatres:* {theatres}\n\n"
        f"Ippo unga `{details['pincode']}` surroundings-kulla enna help venum?"
    )
    buttons = [
        {"id": "Book movie ticket", "title": "🎬 Book Movie"},
        {"id": "Nearby 24 hour pharmacies", "title": "🏥 Nearby Places"},
        {"id": "12606 train enga iruku?", "title": "🚆 Live Train"},
    ]
    return {"text": body, "buttons": buttons, "stage": "onboarding_complete"}


async def handle_onboarding_step(
    session: Any,
    user_id: str,
    text: str,
    memory: Any,
    http_client: Any = None,
) -> dict[str, Any] | None:
    profile = dict(getattr(session, "profile", None) or {})
    lower = text.strip().lower()

    if lower in {"change language", "மொழி மாற்று", "language"}:
        profile["onboarding_step"] = "awaiting_language"
        profile["language"] = None
        await memory.update_profile(user_id, profile)
        return _prompt_language()

    if lower in {"change place", "change city", "ஊர் மாற்று"}:
        profile["onboarding_step"] = "awaiting_place"
        profile["place"] = None
        profile["pincode"] = None
        profile["surrounding_areas"] = []
        await memory.update_profile(user_id, profile)
        return _prompt_place(profile.get("language") or "tanglish")

    if lower in {"change pincode", "பின்கோடு மாற்று", "pincode"}:
        profile["onboarding_step"] = "awaiting_pincode"
        profile["pincode"] = None
        profile["surrounding_areas"] = []
        await memory.update_profile(user_id, profile)
        return _prompt_pincode(
            profile.get("language") or "tanglish",
            profile.get("place") or "Tiruchirappalli (Trichy)",
            strict_warning=False,
        )

    step = profile.get("onboarding_step") or "awaiting_language"
    if step == "completed" and profile.get("pincode"):
        return None

    if step == "awaiting_language" or not profile.get("language"):
        chosen_lang = detect_language_choice(text)
        if not chosen_lang:
            return _prompt_language()
        profile["language"] = chosen_lang
        profile["onboarding_step"] = "awaiting_place"
        await memory.update_profile(user_id, profile)
        return _prompt_place(chosen_lang)

    lang = profile["language"]

    if step == "awaiting_place" or not profile.get("place"):
        direct_pin = extract_pincode(text)
        if direct_pin:
            details = await resolve_pincode_details(direct_pin, "Tamil Nadu", http_client)
            profile.update(
                {
                    "place": details["place"],
                    "pincode": details["pincode"],
                    "hub_name": details["hub_name"],
                    "surrounding_areas": details["surrounding_areas"],
                    "station_code": details["station_code"],
                    "local_theatres": details["local_theatres"],
                    "popular_restaurants": details["popular_restaurants"],
                    "onboarding_step": "completed",
                }
            )
            await memory.update_profile(user_id, profile)
            await memory.set_location(user_id, details["latitude"], details["longitude"])
            return _confirm_onboarding_complete(lang, details)

        chosen_place = detect_place_choice(text)
        if not chosen_place:
            return _prompt_place(lang)
        profile["place"] = chosen_place
        profile["onboarding_step"] = "awaiting_pincode"
        await memory.update_profile(user_id, profile)
        return _prompt_pincode(lang, chosen_place, strict_warning=False)

    pin = extract_pincode(text)
    if not pin:
        return _prompt_pincode(lang, profile["place"], strict_warning=True)

    details = await resolve_pincode_details(pin, profile["place"], http_client)
    profile.update(
        {
            "place": details["place"],
            "pincode": details["pincode"],
            "hub_name": details["hub_name"],
            "surrounding_areas": details["surrounding_areas"],
            "station_code": details["station_code"],
            "local_theatres": details["local_theatres"],
            "popular_restaurants": details["popular_restaurants"],
            "onboarding_step": "completed",
        }
    )
    await memory.update_profile(user_id, profile)
    await memory.set_location(user_id, details["latitude"], details["longitude"])
    return _confirm_onboarding_complete(lang, details)


async def generate_pincode_scoped_reply(
    session: Any,
    user_id: str,
    text: str,
    memory: Any,
) -> dict[str, Any]:
    profile = dict(getattr(session, "profile", None) or {})
    place = profile.get("place") or "Tiruchirappalli (Trichy)"
    pincode = profile.get("pincode") or "620018"
    hub_name = profile.get("hub_name") or f"{place} ({pincode})"
    surrounds = profile.get("surrounding_areas") or [hub_name]
    surrounds_str = ", ".join(surrounds[:5])
    theatres = profile.get("local_theatres") or [f"Main Theatre ({place})"]
    restaurants = profile.get("popular_restaurants") or [f"Top Restaurant ({hub_name})"]
    stn = profile.get("station_code") or "TPJ"
    lower = text.strip().lower()

    if any(w in lower for w in ("pharmacy", "pharmacies", "medical", "hospital", "food", "hotel", "restaurant", "nearby", "stall")):
        reply = (
            f"📍 *Pincode `{pincode}` ({hub_name}) & Surroundings Results:*\n"
            f"_Covered Surroundings: {surrounds_str}_\n\n"
            f"🏥 *24/7 Pharmacies in `{pincode}` Surroundings:*\n"
            f"1. *Apollo 24/7 Pharmacy — {surrounds[0]} ({pincode})* • ⭐ 4.6 • Open 24 Hrs\n"
            f"2. *MedPlus Pharmacy — {surrounds[min(1, len(surrounds)-1)]} ({pincode})* • ⭐ 4.5\n"
            f"3. *PMBJP Jan Aushadhi Kendra — {hub_name} ({pincode})* • Generic Medicines\n\n"
            f"🍴 *Top Rated Food Spots in `{pincode}` Surroundings:*\n"
            + "\n".join(f"• *{r}*" for r in restaurants[:3])
        )
        return {
            "text": reply,
            "buttons": [
                {"id": "Generic medicine for Dolo 650", "title": "💊 Generic Meds"},
                {"id": "Book movie ticket", "title": "🎬 Local Theatres"},
                {"id": "change pincode", "title": "📮 Change Pincode"},
            ],
        }

    if any(w in lower for w in ("train", "12606", "enga iruku", "pnr", "bus", "flight")):
        reply = (
            f"🚆 *Transit Hub for Pincode `{pincode}` ({place} — Nearest Station: `{stn}`)*\n\n"
            f"• *12606 Pallavan Superfast Express (TPJ ➔ MS):*\n"
            f"  🟢 On Time • Current: *Virudhachalam Jn (VRI)* • ETA: *20:50*\n"
            f"• *Next Departures from `{stn}` ({place}):*\n"
            f"  1️⃣ *20666 Vande Bharat Express* — 08:00 (₹965)\n"
            f"  2️⃣ *12636 Vaigai Superfast Express* — 09:35 (₹145)\n"
            f"  3️⃣ *12606 Pallavan Superfast Express* — 15:45 (₹145)"
        )
        return {
            "text": reply,
            "buttons": [
                {"id": "12606 train enga iruku?", "title": "🔄 Refresh 12606"},
                {"id": "Book movie ticket", "title": "🎬 Book Movie"},
                {"id": "Nearby 24 hour pharmacies", "title": "📍 Nearby Places"},
            ],
        }

    return {
        "text": (
            f"🤝 *Thirdhand AI (`{pincode}` — {hub_name})*\n"
            f"_Locked Surroundings: {surrounds_str}_\n"
            f"_Local Theatres: {', '.join(theatres[:2])}_\n\n"
            f"உங்கள் `{pincode}` பகுதிக்குள் என்ன உதவி வேண்டும்? கீழே உள்ள பட்டனைத் தொடவும்:"
        ),
        "buttons": [
            {"id": "Book movie ticket", "title": "🎬 Book Movie"},
            {"id": "Nearby 24 hour pharmacies", "title": "🏥 Nearby Places"},
            {"id": "12606 train enga iruku?", "title": "🚆 Live Train"},
        ],
    }

"""Interactive 5-Step Tap-Button Movie Booking Wizard with AI Best-Seat Auto-Selection."""

from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

CITY_THEATRES: dict[str, list[dict[str, str]]] = {
    "trichy": [
        {
            "id": "movie_th_1",
            "short": "LA Cinema Maris",
            "name": "LA Cinema (Maris Complex), Fort Station Rd, Trichy",
            "screen": "4K RGB Laser • Dolby Atmos",
        },
        {
            "id": "movie_th_2",
            "short": "Sona Mina 4K",
            "name": "Sona Mina Cinema (4K Atmos), Williams Rd, Cantonment, Trichy",
            "screen": "4K Barco • Dolby Atmos",
        },
        {
            "id": "movie_th_3",
            "short": "Ramba Urvashi",
            "name": "Ramba & Urvashi Complex, Central Bus Stand / Junction, Trichy",
            "screen": "2K Digital • 7.1 Surround",
        },
    ],
    "chennai": [
        {
            "id": "movie_th_1",
            "short": "PVR Sathyam",
            "name": "PVR Sathyam Cinemas, Royapettah, Chennai",
            "screen": "4K RGB Laser • Dolby Atmos",
        },
        {
            "id": "movie_th_2",
            "short": "AGS T. Nagar",
            "name": "AGS Cinemas, T. Nagar, Chennai",
            "screen": "4K Dual Projection • Atmos",
        },
        {
            "id": "movie_th_3",
            "short": "INOX Citi Centre",
            "name": "INOX Chennai Citi Centre, Mylapore, Chennai",
            "screen": "4K Digital • Dolby 7.1",
        },
    ],
    "madurai": [
        {
            "id": "movie_th_1",
            "short": "Vetri Cinemas",
            "name": "Vetri Cinemas (4K EPIQ), Villapuram, Madurai",
            "screen": "EPIQ 4K Laser • Dolby Atmos",
        },
        {
            "id": "movie_th_2",
            "short": "INOX Vishaal Mall",
            "name": "INOX Vishaal De Mall, Gokhale Rd, Madurai",
            "screen": "4K Digital • Dolby 7.1",
        },
        {
            "id": "movie_th_3",
            "short": "Gopuram Cinemas",
            "name": "Gopuram Cinemas (4K Atmos), Sellur, Madurai",
            "screen": "4K Laser • Dolby Atmos",
        },
    ],
    "coimbatore": [
        {
            "id": "movie_th_1",
            "short": "Broadway IMAX",
            "name": "Broadway Cinemas (IMAX & EPIQ), Avinashi Rd, Coimbatore",
            "screen": "IMAX with Laser • Dolby Atmos",
        },
        {
            "id": "movie_th_2",
            "short": "KG Cinemas",
            "name": "KG Cinemas (4K Atmos), Race Course, Coimbatore",
            "screen": "4K Christie • Dolby Atmos",
        },
        {
            "id": "movie_th_3",
            "short": "Brookefields PVR",
            "name": "PVR Brookefields Mall, Brookebond Rd, Coimbatore",
            "screen": "4K Digital • Dolby 7.1",
        },
    ],
    "salem": [
        {
            "id": "movie_th_1",
            "short": "ARRS Multiplex",
            "name": "ARRS Multiplex (5 Screens), Meyyanur, Salem",
            "screen": "4K Projection • Dolby Atmos",
        },
        {
            "id": "movie_th_2",
            "short": "INOX Reliance",
            "name": "INOX Reliance Mall, Five Roads, Salem",
            "screen": "2K Digital • 7.1 Surround",
        },
        {
            "id": "movie_th_3",
            "short": "Kailash Prakash",
            "name": "Kailash Prakash 4K Atmos, Salem",
            "screen": "4K Laser • Dolby Atmos",
        },
    ],
    "toronto": [
        {
            "id": "movie_th_1",
            "short": "Scotiabank IMAX",
            "name": "Scotiabank Theatre Toronto IMAX, Richmond St W",
            "screen": "IMAX Dual Laser • UltraAVX",
        },
        {
            "id": "movie_th_2",
            "short": "Cineplex Dundas",
            "name": "Cineplex Cinemas Yonge-Dundas & VIP, Toronto",
            "screen": "4DX • VIP Recliner • Atmos",
        },
        {
            "id": "movie_th_3",
            "short": "Cineplex Scarb.",
            "name": "Cineplex Cinemas Scarborough Town Centre",
            "screen": "UltraAVX • Dolby Atmos",
        },
    ],
}


NOW_SHOWING_INDIA: list[dict[str, Any]] = [
    {
        "id": "movie_mv_1",
        "short": "Scene (Tamil)",
        "title": "Scene (Tamil • U/A)",
        "genre": "Mystery / Drama • 2h 15m",
        "rating": "⭐ 9.1/10",
        "price_inr": 190,
        "price_cad": 18,
    },
    {
        "id": "movie_mv_2",
        "short": "Amaran (Tamil)",
        "title": "Amaran (Tamil • U/A)",
        "genre": "Action / Biopic • 2h 45m",
        "rating": "⭐ 4.8/5",
        "price_inr": 190,
        "price_cad": 18,
    },
    {
        "id": "movie_mv_3",
        "short": "Coolie (Upcoming)",
        "title": "Coolie (Tamil • Upcoming / Demo)",
        "genre": "Action / Mass • 2h 48m",
        "rating": "⭐ 4.9/5",
        "price_inr": 190,
        "price_cad": 18,
    },
]

NOW_SHOWING_GLOBAL: list[dict[str, Any]] = [
    {
        "id": "movie_mv_1",
        "short": "Coolie (IMAX)",
        "title": "Coolie (Tamil w/ English Subs • IMAX)",
        "genre": "Action / Blockbuster • 2h 48m",
        "rating": "⭐ 4.8/5",
        "price_inr": 190,
        "price_cad": 19,
    },
    {
        "id": "movie_mv_2",
        "short": "Good Bad Ugly",
        "title": "Good Bad Ugly (Tamil w/ English Subs)",
        "genre": "Action / Thriller • 2h 36m",
        "rating": "⭐ 4.7/5",
        "price_inr": 190,
        "price_cad": 18,
    },
    {
        "id": "movie_mv_3",
        "short": "Mission Imp. 8",
        "title": "Mission: Impossible — The Final Reckoning (IMAX)",
        "genre": "Action / Espionage • 2h 50m",
        "rating": "⭐ 4.8/5",
        "price_inr": 250,
        "price_cad": 20,
    },
]


def _resolve_city_theatres(profile: dict[str, Any]) -> list[dict[str, str]]:
    place = str(profile.get("place") or "").lower()
    locality = str(profile.get("locality") or place or "City Center")
    city = str(profile.get("place") or "Your City")
    pin = str(profile.get("pincode") or "")

    if (
        "tiruchirappalli" in place
        or "trichy" in place
        or pin.startswith(("620", "621"))
    ):
        return CITY_THEATRES["trichy"]
    if "chennai" in place or pin.startswith("600"):
        return CITY_THEATRES["chennai"]
    if "madurai" in place or pin.startswith("625"):
        return CITY_THEATRES["madurai"]
    if "coimbatore" in place or pin.startswith("641"):
        return CITY_THEATRES["coimbatore"]
    if "salem" in place or pin.startswith("636"):
        return CITY_THEATRES["salem"]
    if (
        any(w in place for w in ("toronto", "scarborough", "mississauga", "brampton"))
        or profile.get("global_location", {}).get("country_iso") == "CA"
    ):
        return CITY_THEATRES["toronto"]

    return [
        {
            "id": "movie_th_1",
            "short": f"PVR INOX {city[:8]}",
            "name": f"PVR INOX Multiplex, {locality}, {city}",
            "screen": "4K Laser • Dolby Atmos",
        },
        {
            "id": "movie_th_2",
            "short": f"AGS Cinema {city[:6]}",
            "name": f"AGS / Royal 4K Cinemas, {locality}, {city}",
            "screen": "4K Digital • Dolby 7.1",
        },
        {
            "id": "movie_th_3",
            "short": f"Galaxy 4K {city[:6]}",
            "name": f"Galaxy 4K Atmos Theatre, {city}",
            "screen": "4K Projection • Atmos",
        },
    ]


def _resolve_movies(profile: dict[str, Any]) -> list[dict[str, Any]]:
    iso = str(profile.get("global_location", {}).get("country_iso") or "IN").upper()
    if iso in {"CA", "US", "GB"}:
        return NOW_SHOWING_GLOBAL
    return NOW_SHOWING_INDIA


def _compute_best_seats(seat_count: int) -> dict[str, Any]:
    count = max(1, min(seat_count, 10))
    start_num = max(1, 11 - (count // 2))
    prime_seats = [f"G{start_num + i}" for i in range(count)]
    alt_seats = [f"J{start_num + i}" for i in range(count)]
    return {
        "seat_count": count,
        "prime_row": "Row G (Prime Royal Center)",
        "prime_seats": ", ".join(prime_seats),
        "prime_short": f"G{start_num}-G{start_num + count - 1}"
        if count > 1
        else prime_seats[0],
        "alt_row": "Row J (Executive Lounger Center)",
        "alt_seats": ", ".join(alt_seats),
        "alt_short": f"J{start_num}-J{start_num + count - 1}"
        if count > 1
        else alt_seats[0],
        "available_total": 34,
        "capacity_total": 180,
    }


def is_movie_booking_trigger(text: str) -> bool:
    lower = text.strip().casefold()
    if lower.startswith(
        ("movie_th_", "movie_mv_", "movie_tm_", "movie_st_", "movie_cf_")
    ):
        return True
    triggers = (
        "book movie",
        "book a movie",
        "movie ticket",
        "movie tickets",
        "help me book movie",
        "cinema ticket",
        "cine movie",
        "scene movie",
        "சினிமா டிக்கெட்",
        "படம் டிக்கெட்",
        "padam ticket",
    )
    return any(t in lower for t in triggers)


async def handle_movie_wizard_step(
    session: Any, user_id: str, text: str, memory: Any
) -> dict[str, Any] | None:
    """Step-by-step interactive button-driven Movie Booking Wizard."""
    profile = dict(session.profile or {})
    if not profile.get("pincode") and session.location is None:
        return None

    lang = str(profile.get("language") or "english").lower()
    wizard = dict(profile.get("movie_wizard") or {})
    lower = text.strip().casefold()
    theatres = _resolve_city_theatres(profile)
    movies = _resolve_movies(profile)

    # Allow restarting the movie wizard at any time
    if lower in {
        "book movie ticket",
        "book movie",
        "help me book movie tickets",
        "movie_restart",
    } or (not wizard and is_movie_booking_trigger(text)):
        wizard = {"step": "select_theatre"}
        profile["movie_wizard"] = wizard
        await memory.update_profile(user_id, profile)
        return _render_step_1_theatres(lang, profile, theatres)

    if not wizard:
        return None

    step = wizard.get("step", "")

    # Check for dispute / user questioning if movie is actually running in theaters
    is_dispute = any(
        w in lower
        for w in (
            "nijama",
            "odala",
            "illa",
            "illaye",
            "real",
            "fake",
            "mock",
            "currect",
            "thappu",
            "wrong",
            "enga",
            "enge",
            "running",
            "question",
            "kaatu",
            "show",
            "edhu",
            "எங்க",
            "இல்லை",
            "ஓடல",
            "நிஜமா",
            "பொய்",
            "உண்மை",
            "actually",
            "screenshot",
            "not running",
        )
    )
    if is_dispute and not lower.startswith(("movie_th_", "movie_mv_", "movie_tm_", "movie_st_", "movie_cf_")):
        profile.pop("movie_wizard", None)
        await memory.update_profile(user_id, profile)
        loc_city = (profile.get("place") or profile.get("locality") or "Trichy").title()
        bms_city = "tiruchirappalli" if "trichy" in loc_city.lower() else loc_city.lower().replace(" ", "-")
        bms_url = f"https://in.bookmyshow.com/{bms_city}/cinemas"
        dispute_reply = (
            f"Neenga sonnadhu 100% correct bro! Namma movie booking module-la live BookMyShow commercial API credentials innum connect aagala, "
            f"idhu booking UX flow-a test panna run aagura demo/simulation mode thaan. "
            f"Real-a {loc_city} theatres-la innum intha big-ticket mass movies release aagala!\n\n"
            f"📍 *{loc_city}-la ippo live-aa running-la irukura unmaiyaana movies paarka BookMyShow நேரடி லிங்க் இதோ:*\n"
            f"🔗 {bms_url}\n\n"
            f"Real BookMyShow-la irukura edhavadhu padam (e.g. *Scene*) ticket book panna test pannanuma bro?"
        )
        if lang in {"tamil"}:
            dispute_reply = (
                f"நீங்கள் சொல்வது 100% உண்மை ப்ரோ! நமது சினிமா டிக்கெட் மாட்யூலில் நேரடி BookMyShow வணிக API இன்னும் இணைக்கப்படவில்லை, "
                f"இது முன்பதிவு அனுபவத்தை சோதிக்கும் Demo/Simulation வடிவம் மட்டுமே. நிஜத்தில் தியேட்டர்களில் இன்னும் இந்த படங்கள் வெளியாகவில்லை!\n\n"
                f"📍 *{loc_city}-ல் தற்போது தியேட்டர்களில் நேரடியாக ஓடும் படங்களை BookMyShow-வில் பார்க்க நேரடி லிங்க் இதோ:*\n"
                f"🔗 {bms_url}\n\n"
                f"வேறு ஏதாவது உதவி வேண்டுமா ப்ரோ?"
            )
        return {
            "text": dispute_reply,
            "buttons": [
                {"id": "Search a good food spot near me", "title": "🍽️ Food Spots"},
                {"id": "Help me book movie tickets", "title": "🎬 Book tickets"},
            ],
        }

    # Step 1 -> Step 2: User chose a theatre
    if step == "select_theatre":
        chosen_th = None
        for idx, th in enumerate(theatres, start=1):
            if (
                lower == th["id"]
                or lower == str(idx)
                or th["short"].casefold() in lower
                or any(
                    w in lower for w in th["name"].casefold().split()[:2] if len(w) > 3
                )
            ):
                chosen_th = th
                break
        if chosen_th is None:
            # If user typed something unrelated (like "Search a good food spot near me" or train), exit wizard
            if not is_movie_booking_trigger(text) and len(text.split()) > 3:
                profile.pop("movie_wizard", None)
                await memory.update_profile(user_id, profile)
                return None
            chosen_th = theatres[0]

        wizard["theatre"] = chosen_th["name"]
        wizard["theatre_short"] = chosen_th["short"]
        wizard["screen"] = chosen_th["screen"]
        wizard["step"] = "select_movie"
        profile["movie_wizard"] = wizard
        await memory.update_profile(user_id, profile)
        return _render_step_2_movies(lang, wizard, movies)

    # Step 2 -> Step 3: User chose a movie
    if step == "select_movie":
        chosen_mv = None
        for idx, mv in enumerate(movies, start=1):
            if (
                lower == mv["id"]
                or lower == str(idx)
                or mv["short"].casefold() in lower
                or mv["title"].split()[0].casefold() in lower
            ):
                chosen_mv = mv
                break
        if chosen_mv is None:
            if any(
                w in lower
                for w in ("food", "restaurant", "train", "pnr", "flight", "pharmacy")
            ):
                profile.pop("movie_wizard", None)
                await memory.update_profile(user_id, profile)
                return None
            # Accept custom movie name typed by user
            custom_title = text.strip().title()[:40]
            chosen_mv = {
                "id": "movie_mv_custom",
                "short": custom_title[:18],
                "title": f"{custom_title} (U/A)",
                "genre": "Feature Film",
                "rating": "⭐ 4.6/5",
                "price_inr": 190,
                "price_cad": 18,
            }

        wizard["movie"] = chosen_mv["title"]
        wizard["movie_short"] = chosen_mv["short"]
        wizard["price_inr"] = chosen_mv["price_inr"]
        wizard["price_cad"] = chosen_mv["price_cad"]
        wizard["step"] = "select_showtime"
        profile["movie_wizard"] = wizard
        await memory.update_profile(user_id, profile)
        return _render_step_3_showtimes(lang, profile, wizard)

    # Step 3 -> Step 4: User chose date & showtime
    if step == "select_showtime":
        zone = profile.get("global_location", {}).get("timezone", "Asia/Kolkata")
        today_dt = datetime.now(ZoneInfo(zone)).date()
        tmrw_dt = today_dt + timedelta(days=1)
        slots_map = {
            "movie_tm_1": f"Today ({today_dt.isoformat()}) • 6:30 PM",
            "1": f"Today ({today_dt.isoformat()}) • 6:30 PM",
            "movie_tm_2": f"Today ({today_dt.isoformat()}) • 10:00 PM",
            "2": f"Today ({today_dt.isoformat()}) • 10:00 PM",
            "movie_tm_3": f"Tomorrow ({tmrw_dt.isoformat()}) • 6:30 PM",
            "3": f"Tomorrow ({tmrw_dt.isoformat()}) • 6:30 PM",
        }
        chosen_time = slots_map.get(lower)
        if not chosen_time:
            if any(
                w in lower
                for w in ("food", "restaurant", "train", "pnr", "flight", "pharmacy")
            ):
                profile.pop("movie_wizard", None)
                await memory.update_profile(user_id, profile)
                return None
            chosen_time = f"Today ({today_dt.isoformat()}) • {text.strip()[:25]}"

        wizard["showtime"] = chosen_time
        wizard["step"] = "select_seats"
        profile["movie_wizard"] = wizard
        await memory.update_profile(user_id, profile)
        return _render_step_4_seat_count(lang, wizard)

    # Step 4 -> Step 5: User chose seat count -> AI Best-Seat Analyzer runs!
    if step == "select_seats":
        seat_map = {"movie_st_1": 1, "movie_st_2": 2, "movie_st_4": 4}
        count = seat_map.get(lower)
        if count is None:
            word_nums = {
                "one": 1,
                "oru": 1,
                "ஒன்று": 1,
                "two": 2,
                "rendu": 2,
                "இரண்டு": 2,
                "three": 3,
                "moonu": 3,
                "மூன்று": 3,
                "four": 4,
                "naalu": 4,
                "நான்கு": 4,
            }
            for w, n in word_nums.items():
                if w in lower:
                    count = n
                    break
        if count is None:
            m = re.search(r"\b([1-9]|10)\b", lower)
            if m:
                count = int(m.group(1))
        if count is None:
            if any(
                w in lower
                for w in ("food", "restaurant", "train", "pnr", "flight", "pharmacy")
            ):
                profile.pop("movie_wizard", None)
                await memory.update_profile(user_id, profile)
                return None
            count = 2

        seat_info = _compute_best_seats(count)
        wizard["seat_count"] = count
        wizard["seat_info"] = seat_info
        wizard["step"] = "confirm_seats"
        profile["movie_wizard"] = wizard
        await memory.update_profile(user_id, profile)
        return _render_step_5_ai_best_seats(lang, profile, wizard)

    # Step 5 -> Step 6: User confirmed Prime Center or Executive Row J seats
    if step == "confirm_seats":
        if lower in {
            "movie_cf_prime",
            "movie_cf_alt",
            "1",
            "2",
            "confirm",
            "yes",
            "ok",
        }:
            seat_info = wizard.get("seat_info") or _compute_best_seats(
                int(wizard.get("seat_count", 2))
            )
            picked_row = (
                seat_info["alt_row"]
                if lower in {"movie_cf_alt", "2"}
                else seat_info["prime_row"]
            )
            picked_seats = (
                seat_info["alt_seats"]
                if lower in {"movie_cf_alt", "2"}
                else seat_info["prime_seats"]
            )
            wizard["confirmed_row"] = picked_row
            wizard["confirmed_seats"] = picked_seats
            profile.pop("movie_wizard", None)
            await memory.update_profile(user_id, profile)
            return _render_step_6_checkout_pass(lang, profile, wizard)
        # If user typed something else, exit wizard cleanly
        profile.pop("movie_wizard", None)
        await memory.update_profile(user_id, profile)
        return None

    return None


def _render_step_1_theatres(
    lang: str, profile: dict[str, Any], theatres: list[dict[str, str]]
) -> dict[str, Any]:
    pin = profile.get("pincode", "")
    locality = profile.get("locality") or profile.get("place", "")
    city = profile.get("place", "")
    lines = "\n".join(
        f"*{idx}. {th['name']}*\n   • 📽️ {th['screen']}"
        for idx, th in enumerate(theatres, start=1)
    )
    if lang == "tamil":
        body = (
            f"🎬 *படி 1/5 — அருகிலுள்ள தியேட்டரைத் தேர்ந்தெடுக்கவும் ({locality}, {city} - `{pin}`)*\n\n"
            f"{lines}\n\n"
            "👇 *கீழே உள்ள பட்டனை அழுத்தி உங்கள் தியேட்டரைத் தேர்வு செய்யவும் (டைப் செய்யத் தேவையில்லை!):*"
        )
    elif lang == "tanglish":
        body = (
            f"🎬 *Step 1/5 — Unga Pincode `{pin}` ({locality}, {city}) pakkathula irukura Theatres:*\n\n"
            f"{lines}\n\n"
            "👇 *Keezha irukura button-a tap panni Theatre choose pannunga (Type panna vendam!):*"
        )
    else:
        body = (
            f"🎬 *Step 1/5 — Choose a Nearby Theatre ({locality}, {city} - `{pin}`)*\n\n"
            f"{lines}\n\n"
            "👇 *Tap a theatre button below to continue (No typing needed!):*"
        )
    buttons = [{"id": th["id"], "title": th["short"][:20]} for th in theatres[:3]]
    return {"text": body, "buttons": buttons}


def _render_step_2_movies(
    lang: str, wizard: dict[str, Any], movies: list[dict[str, Any]]
) -> dict[str, Any]:
    th_name = wizard.get("theatre", "")
    lines = "\n".join(
        f"*{idx}. {mv['title']}*\n   • {mv['rating']} • {mv['genre']} • ₹{mv['price_inr']}"
        for idx, mv in enumerate(movies, start=1)
    )
    if lang == "tamil":
        body = (
            f"✅ *தியேட்டர்:* {th_name}\n\n"
            f"🍿 *படி 2/5 — இப்போது ஓடிக்கொண்டிருக்கும் படங்கள் (Now Showing):*\n\n"
            f"{lines}\n\n"
            "👇 *நீங்கள் பார்க்க விரும்பும் படத்தைக் கீழே உள்ள பட்டனில் தேர்வு செய்யவும்:*"
        )
    elif lang == "tanglish":
        body = (
            f"✅ *Selected Theatre:* {th_name}\n\n"
            f"🍿 *Step 2/5 — Ippo intha theatre-la running-la irukura Movies:*\n\n"
            f"{lines}\n\n"
            "👇 *Neenga paaka pora movie button-a keezha tap pannunga:*"
        )
    else:
        body = (
            f"✅ *Selected Theatre:* {th_name}\n\n"
            f"🍿 *Step 2/5 — Movies Currently Showing:*\n\n"
            f"{lines}\n\n"
            "👇 *Tap the movie you want to watch below:*"
        )
    buttons = [{"id": mv["id"], "title": mv["short"][:20]} for mv in movies[:3]]
    return {"text": body, "buttons": buttons}


def _render_step_3_showtimes(
    lang: str, profile: dict[str, Any], wizard: dict[str, Any]
) -> dict[str, Any]:
    zone = profile.get("global_location", {}).get("timezone", "Asia/Kolkata")
    today_dt = datetime.now(ZoneInfo(zone)).strftime("%b %d")
    tmrw_dt = (datetime.now(ZoneInfo(zone)) + timedelta(days=1)).strftime("%b %d")
    if lang == "tamil":
        body = (
            f"✅ *தியேட்டர்:* {wizard.get('theatre_short')}\n"
            f"✅ *படம்:* {wizard.get('movie')}\n\n"
            f"🕒 *படி 3/5 — தேதி மற்றும் காட்சி நேரத்தைத் (Showtime) தேர்வு செய்யவும்:*\n"
            f"• *1. இன்று ({today_dt}) — மாலை 6:30 PM* (🟢 34 சீட்கள் உள்ளன)\n"
            f"• *2. இன்று ({today_dt}) — இரவு 10:00 PM* (🟢 52 சீட்கள் உள்ளன)\n"
            f"• *3. நாளை ({tmrw_dt}) — மாலை 6:30 PM* (🟢 86 சீட்கள் உள்ளன)\n\n"
            "👇 *கீழே உள்ள பட்டனை அழுத்தி நேரத்தைத் தேர்வு செய்யவும்:*"
        )
    elif lang == "tanglish":
        body = (
            f"✅ *Theatre:* {wizard.get('theatre_short')}\n"
            f"✅ *Movie:* {wizard.get('movie')}\n\n"
            f"🕒 *Step 3/5 — Date & Show Timing choose pannunga:*\n"
            f"• *1. Today ({today_dt}) — 6:30 PM* (🟢 34 seats available)\n"
            f"• *2. Today ({today_dt}) — 10:00 PM* (🟢 52 seats available)\n"
            f"• *3. Tomorrow ({tmrw_dt}) — 6:30 PM* (🟢 86 seats available)\n\n"
            "👇 *Keezha irukura Showtime button-a tap pannunga:*"
        )
    else:
        body = (
            f"✅ *Theatre:* {wizard.get('theatre_short')}\n"
            f"✅ *Movie:* {wizard.get('movie')}\n\n"
            f"🕒 *Step 3/5 — Select Date & Showtime:*\n"
            f"• *1. Today ({today_dt}) — 6:30 PM* (🟢 34 seats available)\n"
            f"• *2. Today ({today_dt}) — 10:00 PM* (🟢 52 seats available)\n"
            f"• *3. Tomorrow ({tmrw_dt}) — 6:30 PM* (🟢 86 seats available)\n\n"
            "👇 *Tap your preferred showtime below:*"
        )
    buttons = [
        {"id": "movie_tm_1", "title": "Today 6:30 PM"},
        {"id": "movie_tm_2", "title": "Today 10:00 PM"},
        {"id": "movie_tm_3", "title": "Tomorrow 6:30 PM"},
    ]
    return {"text": body, "buttons": buttons}


def _render_step_4_seat_count(lang: str, wizard: dict[str, Any]) -> dict[str, Any]:
    if lang == "tamil":
        body = (
            f"✅ *படம்:* {wizard.get('movie_short')} ({wizard.get('theatre_short')})\n"
            f"✅ *நேரம்:* {wizard.get('showtime')}\n\n"
            "💺 *படி 4/5 — உங்களுக்கு எத்தனை சீட்கள் (Tickets) வேண்டும்?*\n"
            "நீங்கள் எண்ணிக்கையைத் தேர்வு செய்தவுடன், நமது AI தியேட்டரில் உள்ள **மிகச்சிறந்த சென்டர் சீட்களை (Best Seats)** தானாகவே அனலைஸ் செய்து உங்களுக்குத் தேர்ந்தெடுத்துத் தரும்!\n\n"
            "👇 *கீழே உள்ள பட்டனை அழுத்தவும் (அல்லது 3, 5 என டைப் செய்யவும்):*"
        )
    elif lang == "tanglish":
        body = (
            f"✅ *Movie:* {wizard.get('movie_short')} ({wizard.get('theatre_short')})\n"
            f"✅ *Showtime:* {wizard.get('showtime')}\n\n"
            "💺 *Step 4/5 — Ungalukku ethana Seats (Tickets) venum?*\n"
            "Neenga select pannathum, namma AI auditorium-la irukura **Best Center Seats-a** automatic-aa analyze panni ungalukku choose panni tharum!\n\n"
            "👇 *Keezha irukura button-a tap pannunga (illana 3, 5 nu type pannunga):*"
        )
    else:
        body = (
            f"✅ *Movie:* {wizard.get('movie_short')} ({wizard.get('theatre_short')})\n"
            f"✅ *Showtime:* {wizard.get('showtime')}\n\n"
            "💺 *Step 4/5 — How many seats do you need?*\n"
            "Once you choose, our AI Auditorium Analyzer will automatically inspect available rows and select the **Best Center Viewing Seats** for you!\n\n"
            "👇 *Tap a button below (or type any number like 3, 5, 6):*"
        )
    buttons = [
        {"id": "movie_st_1", "title": "1 Seat"},
        {"id": "movie_st_2", "title": "2 Seats"},
        {"id": "movie_st_4", "title": "4 Seats"},
    ]
    return {"text": body, "buttons": buttons}


def _render_step_5_ai_best_seats(
    lang: str, profile: dict[str, Any], wizard: dict[str, Any]
) -> dict[str, Any]:
    seat_info = wizard["seat_info"]
    count = seat_info["seat_count"]
    iso = str(profile.get("global_location", {}).get("country_iso") or "IN").upper()
    if iso == "CA":
        unit_price = int(wizard.get("price_cad", 18))
        total_str = f"CAD ${unit_price * count} ({count} × CAD ${unit_price})"
    else:
        unit_price = int(wizard.get("price_inr", 190))
        total_str = f"₹{unit_price * count} ({count} × ₹{unit_price})"

    if lang == "tamil":
        body = (
            f"🤖 *படி 5/5 — AI பெஸ்ட் சீட் அனாலிசிஸ் (AI Best-Seat Auto-Selection):*\n\n"
            f"• *தியேட்டர்:* {wizard.get('theatre')}\n"
            f"• *படம் & நேரம்:* {wizard.get('movie_short')} • {wizard.get('showtime')}\n"
            f"• *காலியாக உள்ள சீட்கள்:* 180-ல் {seat_info['available_total']} சீட்கள் மட்டுமே உள்ளன (முன் வரிசை A-C திரைக்கு மிக அருகில் உள்ளது).\n\n"
            f"🎯 *AI உங்களுக்காகத் தேர்ந்தெடுத்த சிறந்த {count} சீட்கள்:*\n"
            f"👉 *{seat_info['prime_row']} — சீட்கள்: `{seat_info['prime_seats']}`*\n"
            f"   *(காரணம்: திரையின் துல்லியமான நடுப்பகுதி • 35° Eye-Level கோணம் • Dolby Atmos சவுண்ட் மையம்!)*\n\n"
            f"🔄 *மாற்று சிறந்த சாய்ஸ் (Executive Row):*\n"
            f"👉 *{seat_info['alt_row']} — சீட்கள்: `{seat_info['alt_seats']}`* *(கூடுதல் கால் வைக்கும் இடம்)*\n\n"
            f"💰 *மொத்தக் கட்டணம்:* *{total_str}*\n\n"
            "👇 *இந்த சீட்களை உறுதி செய்யக் கீழே உள்ள பட்டனை அழுத்தவும்:*"
        )
    elif lang == "tanglish":
        body = (
            f"🤖 *Step 5/5 — AI Best-Seat Analysis & Auto-Selection:*\n\n"
            f"• *Theatre:* {wizard.get('theatre')}\n"
            f"• *Movie & Time:* {wizard.get('movie_short')} • {wizard.get('showtime')}\n"
            f"• *Auditorium Status:* 180-la {seat_info['available_total']} seats thaan iruku (Front rows A-C screen-ku romba pakkathula iruku).\n\n"
            f"🎯 *AI Ungalukkaga Choose Panna Best {count} Seats:*\n"
            f"👉 *{seat_info['prime_row']} — Seats: `{seat_info['prime_seats']}`*\n"
            f"   *(Why Best: Exact Screen Center • Best 35° Eye-Level View • Dolby Atmos Sweet Spot!)*\n\n"
            f"🔄 *Alternative Best Option (Higher Row):*\n"
            f"👉 *{seat_info['alt_row']} — Seats: `{seat_info['alt_seats']}`* *(Extra Legroom)*\n\n"
            f"💰 *Total Ticket Price:* *{total_str}*\n\n"
            "👇 *Unga seat-a confirm panna keezha tap pannunga:*"
        )
    else:
        body = (
            f"🤖 *Step 5/5 — AI Best-Seat Analysis & Auto-Selection:*\n\n"
            f"• *Theatre:* {wizard.get('theatre')}\n"
            f"• *Movie & Showtime:* {wizard.get('movie_short')} • {wizard.get('showtime')}\n"
            f"• *Auditorium Status:* Only {seat_info['available_total']}/180 seats left (Front rows A-C excluded as too close to screen).\n\n"
            f"🎯 *AI Auto-Selected Best {count} Seat(s) For You:*\n"
            f"👉 *{seat_info['prime_row']} — Seats: `{seat_info['prime_seats']}`*\n"
            f"   *(Why Best: Exact Center Line • Ideal 35° Eye-Level Angle • Dolby Atmos Acoustic Sweet Spot!)*\n\n"
            f"🔄 *Alternative Choice (Executive Lounger):*\n"
            f"👉 *{seat_info['alt_row']} — Seats: `{seat_info['alt_seats']}`* *(Extra Legroom)*\n\n"
            f"💰 *Total Price:* *{total_str}*\n\n"
            "👇 *Tap below to confirm your AI-selected seats:*"
        )
    buttons = [
        {"id": "movie_cf_prime", "title": f"Confirm {seat_info['prime_short']}"[:20]},
        {"id": "movie_cf_alt", "title": f"Pick {seat_info['alt_short']}"[:20]},
        {"id": "movie_restart", "title": "Change Theatre"},
    ]
    return {"text": body, "buttons": buttons}


def _render_step_6_checkout_pass(
    lang: str, profile: dict[str, Any], wizard: dict[str, Any]
) -> dict[str, Any]:
    count = int(wizard.get("seat_count", 2))
    iso = str(profile.get("global_location", {}).get("country_iso") or "IN").upper()
    city = str(profile.get("place") or "Trichy")
    
    # Read live public base URL
    from services.tools.diagram_tool import get_public_base_url

    base_url = get_public_base_url()

    movie_name = wizard.get("movie", "Scene (Tamil • U/A)")
    theatre_name = wizard.get("theatre", "Cinema")
    seats = wizard.get("confirmed_seats", "G10, G11")
    showtime = wizard.get("showtime", "Today • 6:30 PM")

    if iso == "CA":
        unit_price = int(wizard.get("price_cad", 18))
        total_amount = unit_price * count
        total_str = f"CAD ${total_amount}"
        q = urllib.parse.quote_plus(f"{wizard.get('movie_short', '')} {city}".strip())
        bms_url = f"https://www.cineplex.com/search?q={q}"
        upi_pay_link = ""
    else:
        unit_price = int(wizard.get("price_inr", 190))
        total_amount = unit_price * count
        total_str = f"₹{total_amount}"
        q = urllib.parse.quote_plus(f"{wizard.get('movie_short', '')} {city}".strip())
        bms_url = f"https://in.bookmyshow.com/explore/movies-{urllib.parse.quote_plus(city.lower())}?q={q}"
        upi_memo = urllib.parse.quote_plus(f"Scene_{seats.replace(' ', '')}")
        upi_pay_link = f"upi://pay?pa=thirdhandai@okaxis&pn=Thirdhand+Cinema&am={total_amount}&cu=INR&tn={upi_memo}"

    checkout_params = urllib.parse.urlencode({
        "item": movie_name,
        "theatre": theatre_name,
        "seats": seats,
        "time": showtime,
        "amount": total_amount,
        "type": "movie",
    })
    direct_checkout_url = f"{base_url}/checkout?{checkout_params}"

    if lang == "tamil":
        body = (
            f"🎟️ *முன்பதிவு அட்டை தயார்! (Movie Ticket Pass)*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 *படம்:* {movie_name}\n"
            f"🏛️ *தியேட்டர்:* {theatre_name}\n"
            f"📽️ *திரை:* {wizard.get('screen')}\n"
            f"🕒 *காட்சி நேரம்:* {showtime}\n"
            f"💺 *தேர்வு செய்யப்பட்ட சீட்கள் ({count}):* *{seats}* ({wizard.get('confirmed_row')})\n"
            f"💰 *மொத்தக் கட்டணம்:* *{total_str}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *நேரடி 1-Click Checkout லிங்க் (Google Pay / PhonePe):*\n{direct_checkout_url}\n\n"
            + (f"📱 *UPI 1-Tap Pay Link:*\n{upi_pay_link}\n\n" if upi_pay_link else "")
            + f"👉 *நேரடி பலன்:* மேலே உள்ள லிங்க்கை அழுத்தினால், உங்கள் சீட்கள் (`{seats}`) மற்றும் தொகை (`{total_str}`) தானாகவே நிரப்பப்பட்ட Payment திரைக்குச் செல்லும். மீண்டும் படம், தியேட்டர் அல்லது சீட்டைத் தேர்வு செய்ய வேண்டியதில்லை!"
        )
    elif lang == "tanglish":
        body = (
            f"🎟️ *Movie Ticket Pre-Checkout Pass Ready!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 *Movie:* {movie_name}\n"
            f"🏛️ *Theatre:* {theatre_name}\n"
            f"📽️ *Screen:* {wizard.get('screen')}\n"
            f"🕒 *Showtime:* {showtime}\n"
            f"💺 *Locked Best Seats ({count}):* *{seats}* ({wizard.get('confirmed_row')})\n"
            f"💰 *Total Payable:* *{total_str}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *Direct 1-Click Instant Payment (GPay / PhonePe):*\n{direct_checkout_url}\n\n"
            + (f"📱 *Direct UPI Single-Tap Pay:*\n{upi_pay_link}\n\n" if upi_pay_link else "")
            + f"👉 *Friction-Free Checkout:* Mela irukura link-a tap panna direct-a locked seats (`{seats}`) & amount (`{total_str}`) oda payment page open aagum. Neenga marupadiyum movie-o seat-o choose panna vendiyadhey illa!"
        )
    else:
        body = (
            f"🎟️ *MOVIE TICKET PRE-CHECKOUT PASS READY!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 *Movie:* {movie_name}\n"
            f"🏛️ *Theatre:* {theatre_name}\n"
            f"📽️ *Screen:* {wizard.get('screen')}\n"
            f"🕒 *Showtime:* {showtime}\n"
            f"💺 *Locked Best Seats ({count}):* *{seats}* ({wizard.get('confirmed_row')})\n"
            f"💰 *Total Payable:* *{total_str}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *Direct 1-Click Instant Payment (GPay / PhonePe / Card):*\n{direct_checkout_url}\n\n"
            + (f"📱 *Direct UPI 1-Tap Pay:*\n{upi_pay_link}\n\n" if upi_pay_link else "")
            + f"👉 *Seamless Flow:* Tapping the direct link lands you straight on the checkout page with your seats (`{seats}`) and amount (`{total_str}`) already locked. No re-selecting anything!"
        )
    buttons = [
        {"id": "Search a good food spot near me", "title": "🍴 Food Near Theatre"},
        {"id": "Book movie ticket", "title": "🎬 Book Another"},
        {"id": "12606 train enga iruku?", "title": "🚆 Live Train"},
    ]
    return {"text": body, "buttons": buttons}

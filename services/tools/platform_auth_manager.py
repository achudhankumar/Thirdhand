import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PLATFORM_CATALOG: dict[str, dict[str, Any]] = {
    "blinkit": {
        "name": "Blinkit",
        "category": "quick_commerce",
        "regions": ["IN"],
        "icon": "⚡",
        "web_url": "https://blinkit.com",
        "login_instructions": "Open Blinkit Web/App, enter your mobile number and complete OTP verification.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "zepto": {
        "name": "Zepto",
        "category": "quick_commerce",
        "regions": ["IN"],
        "icon": "🛒",
        "web_url": "https://www.zeptonow.com",
        "login_instructions": "Open Zepto Web/App and sign in with your phone number.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "swiggy_instamart": {
        "name": "Swiggy Instamart",
        "category": "quick_commerce",
        "regions": ["IN"],
        "icon": "🍊",
        "web_url": "https://www.swiggy.com/instamart",
        "login_instructions": "Sign in to Swiggy using your phone number and OTP.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "zomato": {
        "name": "Zomato",
        "category": "food_delivery",
        "regions": ["IN"],
        "icon": "🍽️",
        "web_url": "https://www.zomato.com",
        "login_instructions": "Log in to Zomato to access your saved address and payment preferences.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "amazon": {
        "name": "Amazon",
        "category": "e_commerce",
        "regions": ["IN", "US", "CA", "UK", "AE", "GLOBAL"],
        "icon": "📦",
        "web_url": "https://amazon.com",
        "login_instructions": "Sign in to your Amazon account to link your 1-Click Buy / Cart & Prime address.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "flipkart": {
        "name": "Flipkart",
        "category": "e_commerce",
        "regions": ["IN"],
        "icon": "🛍️",
        "web_url": "https://flipkart.com",
        "login_instructions": "Log in to Flipkart with mobile number and OTP to enable automated cart and SuperCoins.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "myntra": {
        "name": "Myntra",
        "category": "fashion",
        "regions": ["IN"],
        "icon": "👗",
        "web_url": "https://myntra.com",
        "login_instructions": "Sign in to Myntra with phone number to save size & order bag.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "meesho": {
        "name": "Meesho",
        "category": "e_commerce",
        "regions": ["IN"],
        "icon": "🏷️",
        "web_url": "https://meesho.com",
        "login_instructions": "Log in to Meesho for lowest prices and Cash on Delivery order placement.",
        "requires_auth_for_cart": True,
        "supports_cod": True,
    },
    "bookmyshow": {
        "name": "BookMyShow",
        "category": "entertainment",
        "regions": ["IN", "AE"],
        "icon": "🎬",
        "web_url": "https://in.bookmyshow.com",
        "login_instructions": "Sign in with Google or Phone Number on BookMyShow for seat lock and M-Tickets.",
        "requires_auth_for_cart": True,
        "supports_cod": False,
    },
    "walmart": {
        "name": "Walmart",
        "category": "e_commerce",
        "regions": ["US", "CA"],
        "icon": "🛒",
        "web_url": "https://walmart.com",
        "login_instructions": "Sign in to your Walmart account for store pickup and delivery slot reservation.",
        "requires_auth_for_cart": True,
        "supports_cod": False,
    },
    "ubereats": {
        "name": "Uber Eats",
        "category": "food_delivery",
        "regions": ["US", "CA", "UK", "EU", "GLOBAL"],
        "icon": "🍔",
        "web_url": "https://ubereats.com",
        "login_instructions": "Sign in to Uber Eats for real-time restaurant cart sync.",
        "requires_auth_for_cart": True,
        "supports_cod": False,
    },
    "cineplex": {
        "name": "Cineplex",
        "category": "entertainment",
        "regions": ["CA"],
        "icon": "🍿",
        "web_url": "https://cineplex.com",
        "login_instructions": "Sign in to Cineplex SCENE+ account to redeem points and lock seats.",
        "requires_auth_for_cart": True,
        "supports_cod": False,
    },
}

DATA_DIR = Path("data/whatsapp")
AUTH_STORE_FILE = DATA_DIR / "platform_sessions.json"


def _load_auth_store() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not AUTH_STORE_FILE.exists():
        return {}
    try:
        with open(AUTH_STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load platform auth store (%s)", exc)
        return {}


def _save_auth_store(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = AUTH_STORE_FILE.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp_path.replace(AUTH_STORE_FILE)


class PlatformAuthManager:
    """Manages multi-platform login state and session tokens per user."""

    @staticmethod
    def identify_platform(query: str, user_region: str = "IN") -> dict[str, Any]:
        """Detect platform from user text (e.g. 'Blinkit-la paal podu', 'Amazon shoes')."""
        q = query.casefold()
        for key, meta in PLATFORM_CATALOG.items():
            if key in q or meta["name"].casefold() in q:
                return {"platform_id": key, **meta}

        # Contextual inference by intent keywords
        if any(w in q for w in ("blinkit", "groceries", "milk", "paal", "bread", "10 min")):
            return {"platform_id": "blinkit", **PLATFORM_CATALOG["blinkit"]}
        if any(w in q for w in ("zepto", "quick commerce")):
            return {"platform_id": "zepto", **PLATFORM_CATALOG["zepto"]}
        if any(w in q for w in ("swiggy", "instamart")):
            return {"platform_id": "swiggy_instamart", **PLATFORM_CATALOG["swiggy_instamart"]}
        if any(w in q for w in ("zomato", "restaurant food", "mess", "biryani", "food delivery")):
            return {"platform_id": "zomato", **PLATFORM_CATALOG["zomato"]}
        if any(w in q for w in ("flipkart", "big billion")):
            return {"platform_id": "flipkart", **PLATFORM_CATALOG["flipkart"]}
        if any(w in q for w in ("myntra", "clothes", "shirt", "tshirt", "dress", "fashion")):
            return {"platform_id": "myntra", **PLATFORM_CATALOG["myntra"]}
        if any(w in q for w in ("meesho", "saree")):
            return {"platform_id": "meesho", **PLATFORM_CATALOG["meesho"]}
        if any(w in q for w in ("ticket", "movie", "theatre", "cinema", "padam")):
            if user_region == "CA":
                return {"platform_id": "cineplex", **PLATFORM_CATALOG["cineplex"]}
            return {"platform_id": "bookmyshow", **PLATFORM_CATALOG["bookmyshow"]}
        if any(w in q for w in ("amazon", "buy", "order", "price check")):
            return {"platform_id": "amazon", **PLATFORM_CATALOG["amazon"]}

        # Default fallback to Amazon for general shopping, Blinkit for quick items
        return {"platform_id": "amazon", **PLATFORM_CATALOG["amazon"]}

    @staticmethod
    def is_logged_in(user_id: str, platform_id: str) -> bool:
        """Check if user has an active, non-expired session for the platform."""
        store = _load_auth_store()
        user_platforms = store.get(str(user_id), {})
        session = user_platforms.get(platform_id)
        if not session or not session.get("is_authenticated"):
            return False
        # Optional expiry check
        expires_at = session.get("expires_at")
        if expires_at:
            try:
                exp_dt = datetime.fromisoformat(expires_at)
                if exp_dt < datetime.now(timezone.utc):
                    return False
            except Exception:
                pass
        return True

    @staticmethod
    def get_session(user_id: str, platform_id: str) -> dict[str, Any] | None:
        """Retrieve stored cookies/tokens for headless browser automation."""
        store = _load_auth_store()
        return store.get(str(user_id), {}).get(platform_id)

    @staticmethod
    def save_session(
        user_id: str,
        platform_id: str,
        cookies: list[dict] | None = None,
        auth_token: str | None = None,
        account_name: str = "",
        phone: str = "",
    ) -> None:
        """Store verified session token / cookies after user logs in."""
        store = _load_auth_store()
        if str(user_id) not in store:
            store[str(user_id)] = {}

        store[str(user_id)][platform_id] = {
            "is_authenticated": True,
            "account_name": account_name or "Verified User",
            "phone": phone,
            "cookies": cookies or [],
            "auth_token": auth_token or "",
            "linked_at": datetime.now(timezone.utc).isoformat(),
        }
        _save_auth_store(store)
        logger.info("Saved platform session: user=%s, platform=%s", user_id, platform_id)

    @staticmethod
    def revoke_session(user_id: str, platform_id: str) -> None:
        """Revoke a platform session when user explicitly unlinks or resets."""
        store = _load_auth_store()
        if str(user_id) in store and platform_id in store[str(user_id)]:
            store[str(user_id)].pop(platform_id, None)
            _save_auth_store(store)
            logger.info("Revoked platform session: user=%s, platform=%s", user_id, platform_id)

    @staticmethod
    def build_login_prompt(
        user_id: str,
        platform_meta: dict[str, Any],
        user_lang: str = "tamil",
        original_query: str = "",
    ) -> dict[str, Any]:
        """Generate clear, action-oriented WhatsApp response requesting 1-time login."""
        platform_name = platform_meta.get("name", "Platform")
        icon = platform_meta.get("icon", "🛍️")
        url = platform_meta.get("web_url", "https://blinkit.com")

        if user_lang in {"tamil", "tanglish"}:
            body = (
                f"{icon} *{platform_name} கணக்கு இன்னும் இணைக்கப்படவில்லை!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"ப்ரோ, உங்கள் வாட்ஸ்அப் ஆர்டரை {platform_name}-ல் தானாக (Background-ல்) முடிக்க, "
                f"உங்கள் கணக்கு ஒருமுறை இணைக்கப்பட வேண்டும்.\n\n"
                f"🔑 *காரணம்:* அப்போதுதான் உங்கள் முகவரி (Saved Address), கார்ட் கிளியரிங், "
                f"மற்றும் கேஷ் ஆன் டெலிவரி (COD) ஆர்டரை AI-ஆல் நேரடியாக பிளேஸ் செய்ய முடியும்.\n\n"
                f"📲 *1-முறை லாகின் செய்ய:*\n"
                f"1. கீழே உள்ள '{platform_name} Login' பட்டனைத் தொடவும்.\n"
                f"2. உங்கள் மொபைல் எண்ணை உள்ளிட்டு OTP உறுதி செய்யவும்.\n\n"
                f"✅ லாகின் முடிந்ததும், மீண்டும் ஒரு 'Hi' அல்லது உங்கள் பொருளைச் சொன்னால் போதும் — "
                f"AI உடனே உங்கள் கார்ட்டை ரெடி செய்துவிடும்!"
            )
        else:
            body = (
                f"{icon} *{platform_name} Account Not Linked Yet!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"To autonomously process your order and place items into your personal cart, "
                f"we need a one-time login handshake with {platform_name}.\n\n"
                f"🔑 *Why is this needed?*\n"
                f"This allows the AI to securely access your saved delivery address, clear any stale cart, "
                f"and configure Cash on Delivery (COD) seamlessly.\n\n"
                f"📲 *How to connect:*\n"
                f"1. Tap '{platform_name} Login' below to authenticate via your mobile number.\n"
                f"2. Once verified, reply with your shopping request and the AI agent will fulfill it!"
            )

        buttons = [
            {"id": f"auth_login_{platform_meta.get('platform_id')}", "title": f"🔑 {platform_name} Login"[:20]},
            {"id": f"auth_mock_demo_{platform_meta.get('platform_id')}", "title": "⚡ Quick Test (Demo)"[:20]},
            {"id": "btn_clear_chat", "title": "🧹 Clear Chat"},
        ]
        return {
            "reply": body,
            "buttons": buttons,
            "platform_id": platform_meta.get("platform_id"),
            "status": "awaiting_login",
        }

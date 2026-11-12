"""Zepto Quick-Commerce Family Cart & Guardian Approval Workflow."""

import random
import re
from typing import Any

ZEPTO_CATALOG = {
    "milk": ("Aavin Green Magic Milk (500ml)", 27),
    "பால்": ("Aavin Green Magic Milk (500ml)", 27),
    "bread": ("Modern Daily Fresh White Bread (400g)", 45),
    "பிரெட்": ("Modern Daily Fresh White Bread (400g)", 45),
    "egg": ("Farm Fresh White Eggs (6 pcs)", 48),
    "eggs": ("Farm Fresh White Eggs (6 pcs)", 48),
    "முட்டை": ("Farm Fresh White Eggs (6 pcs)", 48),
    "curd": ("Aavin Fresh Thick Curd (500g)", 35),
    "தயிர்": ("Aavin Fresh Thick Curd (500g)", 35),
    "tomato": ("Country Fresh Tomatoes (1 kg)", 36),
    "தக்காளி": ("Country Fresh Tomatoes (1 kg)", 36),
    "onion": ("Sambar / Red Onions (1 kg)", 42),
    "வெங்காயம்": ("Sambar / Red Onions (1 kg)", 42),
    "potato": ("Fresh Farm Potatoes (1 kg)", 38),
    "உருளைக்கிழங்கு": ("Fresh Farm Potatoes (1 kg)", 38),
    "tea": ("Tata Tea Gold Premium (250g)", 145),
    "டீ": ("Tata Tea Gold Premium (250g)", 145),
    "coffee": ("Bru Instant Coffee (50g)", 95),
    "காபி": ("Bru Instant Coffee (50g)", 95),
    "biscuit": ("Parle-G Gold Biscuits (1 kg)", 90),
    "பிஸ்கட்": ("Parle-G Gold Biscuits (1 kg)", 90),
    "maggi": ("Maggi 2-Minute Masala Noodles (Pack of 4)", 56),
    "மேகி": ("Maggi 2-Minute Masala Noodles (Pack of 4)", 56),
    "oil": ("Fortune Sunlite Sunflower Oil (1L Pouch)", 135),
    "எண்ணெய்": ("Fortune Sunlite Sunflower Oil (1L Pouch)", 135),
    "atta": ("Aashirvaad Shudh Chakki Atta (1 kg)", 58),
    "ஆட்டா": ("Aashirvaad Shudh Chakki Atta (1 kg)", 58),
    "rice": ("Deccan Ponni Raw Rice (1 kg)", 65),
    "அரிசி": ("Deccan Ponni Raw Rice (1 kg)", 65),
}


def parse_zepto_cart_items(text: str) -> list[dict[str, Any]]:
    """Extract grocery items, quantities and prices from natural language request."""
    lower = text.lower()
    items = []
    seen = set()

    # Search for known catalog items
    for key, (display_name, unit_price) in ZEPTO_CATALOG.items():
        if key in lower and display_name not in seen:
            seen.add(display_name)
            # Try to find quantity (e.g., '2 milk', 'milk 2 packets', '3 bread')
            qty_match = re.search(rf"(\d+)\s*(?:packet|pkt|kg|pack|nos|peices)?\s*{re.escape(key)}", lower) or \
                        re.search(rf"{re.escape(key)}\s*(\d+)", lower)
            qty = int(qty_match.group(1)) if qty_match else 1
            qty = min(max(qty, 1), 10)
            items.append({
                "name": display_name,
                "unit_price": unit_price,
                "quantity": qty,
                "subtotal": unit_price * qty
            })

    if not items:
        # Default essential grocery basket if user just says 'Zepto-la order podu'
        items = [
            {"name": "Aavin Green Magic Milk (500ml)", "unit_price": 27, "quantity": 2, "subtotal": 54},
            {"name": "Modern Daily Fresh White Bread (400g)", "unit_price": 45, "quantity": 1, "subtotal": 45},
            {"name": "Farm Fresh White Eggs (6 pcs)", "unit_price": 48, "quantity": 1, "subtotal": 48},
        ]
    return items


def format_zepto_approval_card(items: list[dict[str, Any]], profile: dict[str, Any], lang: str = "tanglish") -> dict[str, Any]:
    """Generate the Family Guardian / Admin Approval notification card."""
    total = sum(i["subtotal"] for i in items)
    pin = profile.get("pincode", "620018")
    locality = profile.get("locality") or profile.get("place") or "Your Locality"
    eta = random.randint(10, 14)

    item_lines = []
    for idx, item in enumerate(items, 1):
        item_lines.append(f"  {idx}. *{item['name']}* × {item['quantity']} — ₹{item['subtotal']}")
    items_block = "\n".join(item_lines)

    if lang in {"tamil", "tanglish"}:
        text = (
            f"🛒 *Zepto 10-Min Quick-Commerce Cart Ready!* ⚡\n\n"
            f"👨‍👩‍👧 *Family Guardian / Admin Approval Request:*\n"
            f"அம்மா / குடும்பத்தினர் கீழ்கண்ட மளிகைப் பொருட்களை Zepto-ல் ஆர்டர் செய்யக் கேட்டுள்ளனர்:\n\n"
            f"📦 *பொருட்கள் (Cart Items):*\n{items_block}\n\n"
            f"💰 *மொத்தத் தொகை (Total):* ₹{total} _(Free 10-Min Delivery)_\n"
            f"📍 *டெலிவரி இடம்:* {locality} (Pincode `{pin}`)\n"
            f"⏱️ *டெலிவரி நேரம் (ETA):* {eta} நிமிடங்களில் கதவருகில்!\n\n"
            f"❓ *ஆர்டரை உறுதி செய்ய ஒப்புதல் (Approval) தருகிறீர்களா?*\n"
            f"கீழே உள்ள பட்டனை கிளிக் செய்யவும் அல்லது *'Approve'* என்று பதிலளிக்கவும்."
        )
    else:
        text = (
            f"🛒 *Zepto 10-Min Quick-Commerce Cart Created!* ⚡\n\n"
            f"👨‍👩‍👧 *Family Guardian / Admin Approval Request:*\n"
            f"Your family member requested to order these grocery items via Zepto:\n\n"
            f"📦 *Cart Items:*\n{items_block}\n\n"
            f"💰 *Total Amount:* ₹{total} _(Free 10-Min Delivery)_\n"
            f"📍 *Delivery To:* {locality} (Pincode `{pin}`)\n"
            f"⏱️ *ETA:* {eta} Minutes\n\n"
            f"❓ *Do you approve placing this order?*\n"
            f"Tap a button below or reply *'Approve'* to confirm."
        )

    buttons = [
        {"id": "approve_zepto_order", "title": "✅ Place Order"},
        {"id": "reject_zepto_order", "title": "❌ Decline Order"},
        {"id": "open_zepto_cart", "title": "🛒 View on Zepto"},
    ]

    return {
        "reply": text,
        "buttons": buttons,
        "order_data": {
            "items": items,
            "total": total,
            "pincode": pin,
            "locality": locality,
            "status": "pending_approval"
        }
    }


def format_zepto_confirmed_card(order_data: dict[str, Any], lang: str = "tanglish") -> dict[str, Any]:
    """Generate the live dispatched & tracking card after Guardian approval."""
    order_id = f"ZEP-{random.randint(100000, 999999)}"
    riders = ["Rajesh Kumar", "Suresh M", "Vignesh K", "Praveen Raj"]
    rider = random.choice(riders)
    mins = random.randint(9, 12)
    total = order_data.get("total", 147)
    locality = order_data.get("locality", "Your Doorstep")

    if lang in {"tamil", "tanglish"}:
        text = (
            f"🎉 *Zepto Order Confirmed & Approved!* 🚀\n\n"
            f"✅ *Approval Status:* Family Admin Approved\n"
            f"🆔 *Order ID:* `#{order_id}`\n"
            f"🛵 *Delivery Partner:* {rider} (Zepto Super Rider)\n"
            f"📍 *Delivery To:* {locality}\n"
            f"⏱️ *Live ETA:* *{mins} நிமிடங்களில்* உங்கள் வீட்டை வந்தடையும்!\n"
            f"💰 *Paid via:* Family UPI / Cash on Delivery (₹{total})\n\n"
            f"🔗 *Live Delivery Map Tracking:* https://www.zeptonow.com/order/{order_id}\n\n"
            f"அம்மாவிடம் சொல்லிவிடுங்கள் ப்ரோ, பொருள் இன்னும் 10 நிமிஷத்துல வீட்டுக்கு வந்துடும்! ✨"
        )
    else:
        text = (
            f"🎉 *Zepto Order Confirmed & Approved!* 🚀\n\n"
            f"✅ *Approval Status:* Family Admin Approved\n"
            f"🆔 *Order ID:* `#{order_id}`\n"
            f"🛵 *Delivery Partner:* {rider} (Zepto Rider)\n"
            f"📍 *Delivery To:* {locality}\n"
            f"⏱️ *Live ETA:* Arriving in *{mins} minutes*!\n"
            f"💰 *Total Amount:* ₹{total}\n\n"
            f"🔗 *Live Tracking Link:* https://www.zeptonow.com/order/{order_id}\n\n"
            f"The delivery partner has picked up your items and is on the way! ✨"
        )

    buttons = [
        {"id": f"track_{order_id}", "title": "📍 Live Map Track"},
        {"id": "Search a good food spot near me", "title": "🍽️ Food Spots"},
        {"id": "Book movie ticket", "title": "🎬 Book Movie"},
    ]

    return {
        "reply": text,
        "buttons": buttons
    }

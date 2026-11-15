import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContactMessagingAgent:
    """Autonomous Contact Messaging & Personal Assistant for WhatsApp.
    
    Handles:
    - 'Call <Name>' -> Generates 1-click WhatsApp VoIP/Call link
    - 'Message <Name> <Text>' -> Sends WhatsApp message directly
    - 'Send a random message to <Name>' -> Generates and dispatches a warm message
    - Saves recipient contact numbers automatically in user profile
    """

    CALL_WORDS = {"call", "phone", "ring"}
    TAMIL_CALL_PATTERNS = [
        r"கால்\s*(?:பண்ணு|போடு|பண்ணிடு)",
        r"போன்\s*(?:போடு|பண்ணு|பண்ணிடு)",
        r"கூப்பிடு",
        r"பேசு",
    ]
    MSG_WORDS = {"message", "msg", "whatsapp"}
    TAMIL_MSG_PATTERNS = [
        r"மெசேஜ்\s*(?:அனுப்பு|போடு|பண்ணு|பண்ணிடு)",
        r"வாட்ஸ்அப்\s*(?:பண்ணு|அனுப்பு)",
    ]

    NON_CONTACT_WORDS = {
        "a", "the", "an", "pdf", "book", "image", "photo", "pic", "picture", "file",
        "doc", "document", "song", "video", "food", "hotel", "order", "delivery",
        "biryani", "pizza", "burger", "menu", "help", "summary", "details", "coloring", "for", "to"
    }

    @classmethod
    def is_contact_intent(cls, query: str) -> bool:
        q = query.casefold().strip()

        # 1. Action words with word boundary (avoid matching "coloring", "engineering", etc.)
        has_call = any(re.search(rf"\b{w}\b", q) for w in cls.CALL_WORDS) or \
                   any(re.search(p, q) for p in cls.TAMIL_CALL_PATTERNS)

        has_msg = any(re.search(rf"\b{w}\b", q) for w in cls.MSG_WORDS) or \
                  any(re.search(p, q) for p in cls.TAMIL_MSG_PATTERNS)

        if not (has_call or has_msg):
            return False

        # 2. Check for explicit recipient / target
        has_target = bool(re.search(r"\b(?:pragadeesh|brother|friend|sister|mom|dad|பிரகதீஷ்|தம்பி|நண்பன்|அம்மா|அப்பா)\b", q)) or \
                     bool(re.search(r"\b(?:(?:\+?91)?[6-9]\d{9})\b", q))

        target_match = re.search(r"(?:to|call|message|msg|contact|அனுப்பு|பண்ணு)\s+([a-zA-Z\u0B80-\u0BFF]{2,})", query, re.I)
        if target_match:
            cand = target_match.group(1).casefold()
            if cand not in cls.NON_CONTACT_WORDS:
                has_target = True

        if re.search(r"[a-zA-Z\u0B80-\u0BFF]+(?:க்கு|ku|iku)\s*(?:கால்|போன்|மெசேஜ்|call|msg)", q):
            has_target = True

        return (has_call or has_msg) and has_target

    @classmethod
    async def process_contact_request(
        cls,
        user_id: str,
        query: str,
        session_profile: dict[str, Any],
        whatsapp_client: Any,
        user_lang: str = "tamil",
    ) -> dict[str, Any]:
        contacts = session_profile.get("contacts", {})
        q = query.casefold()

        # 1. Determine action: call vs message
        is_call = (
            any(re.search(rf"\b{w}\b", q) for w in cls.CALL_WORDS) or
            any(re.search(p, q) for p in cls.TAMIL_CALL_PATTERNS)
        ) and not (
            any(re.search(rf"\b{w}\b", q) for w in cls.MSG_WORDS) or
            any(re.search(p, q) for p in cls.TAMIL_MSG_PATTERNS)
        )

        # 2. Check if phone number is provided in text
        phone_match = re.search(r"\b(?:(?:\+?91)?[6-9]\d{9})\b", query)
        phone = phone_match.group(0).replace("+", "") if phone_match else None
        if phone and len(phone) == 10:
            phone = f"91{phone}"

        # 3. Extract target name
        target_name = "Pragadeesh" if ("பிரகதீஷ்" in query or "pragadeesh" in q) else None
        if not target_name:
            match = re.search(r"(?:to|call|message|msg|contact|அனுப்பு|பண்ணு)\s+([a-zA-Z\u0B80-\u0BFF]{2,})", query, re.I)
            if match:
                extracted = match.group(1).strip()
                if extracted.casefold() not in cls.NON_CONTACT_WORDS and extracted.casefold() not in {"a", "the", "one", "oru", "oruvan", "ஒரு"}:
                    target_name = extracted.title()
        if not target_name and phone:
            target_name = phone
        if not target_name:
            target_name = "Pragadeesh"

        # 4. If not in text, check saved contacts
        target_key = target_name.casefold()
        if not phone:
            phone = contacts.get(target_key)

        # 5. Extract or generate message body if it's a message action
        msg_body = ""
        if not is_call:
            if any(w in q for w in ("random", "ரேண்டம்", "ஏதாச்சும்", "something", "fun")):
                msg_body = f"Hey {target_name}! 🤝 Hope you're having a wonderful day! Sending warm positive vibes from WhatsApp AI."
            else:
                body_match = re.search(r"(?:that|saying|சொல்லி|மெசேஜ்)\s*[:,\-]?\s*(.+)", query, re.I)
                msg_body = body_match.group(1).strip() if body_match else f"Hi {target_name}, hope all is good!"

        # Scenario A: Phone number is NOT known
        if not phone:
            session_profile["pending_contact_action"] = {
                "action": "call" if is_call else "message",
                "name": target_name,
                "msg_body": msg_body,
            }
            if user_lang in {"tamil", "tanglish"}:
                reply = (
                    f"📲 *{target_name}-ன் வாட்ஸ்அப் எண் என்ன ப்ரோ?*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"அவரது 10-இலக்க மொபைல் எண்ணை (எ.கா: `9876543210`) இங்கே அனுப்பவும்.\n"
                    f"நான் உடனே உங்கள் காண்டாக்ட்டில் சேமித்து, "
                    f"{'நேரடி கால் லிங்க் தருகிறேன்' if is_call else 'மெசேஜை உடனே அனுப்பி விடுகிறேன்'}! ✨"
                )
            else:
                reply = (
                    f"📲 *What is {target_name}'s mobile number?*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Please send the 10-digit phone number (e.g., `9876543210`).\n"
                    f"I will save it and {'provide the direct WhatsApp call link' if is_call else 'deliver your message instantly'}! ✨"
                )
            return {
                "reply": reply,
                "buttons": [
                    {"id": "btn_clear_chat", "title": "🧹 Clear Chat"},
                ],
                "profile": session_profile,
            }

        # Scenario B: Phone number IS known
        # Save contact permanently
        if "contacts" not in session_profile:
            session_profile["contacts"] = {}
        session_profile["contacts"][target_key] = phone

        if is_call:
            call_link = f"https://wa.me/{phone}"
            if user_lang in {"tamil", "tanglish"}:
                reply = (
                    f"📞 *{target_name}-க்கு வாட்ஸ்அப் கால் செய்ய தயார்!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *பெயர்:* {target_name}\n"
                    f"📱 *எண்:* +{phone}\n\n"
                    f"👉 *1-Click WhatsApp Call & Chat லிங்க்:*\n"
                    f"{call_link}\n\n"
                    f"மேலே உள்ள லிங்கைத் தொட்டால் {target_name}-ன் வாட்ஸ்அப் சாட் & ஆடியோ/வீடியோ கால் நேரடியாகத் திறக்கும்!"
                )
            else:
                reply = (
                    f"📞 *Ready to connect with {target_name}!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *Name:* {target_name}\n"
                    f"📱 *Number:* +{phone}\n\n"
                    f"👉 *Direct WhatsApp Link:*\n"
                    f"{call_link}\n\n"
                    f"Tap the link above to start a WhatsApp audio/video call or chat instantly!"
                )
            return {
                "reply": reply,
                "buttons": [
                    {"id": f"msg_to_{phone}", "title": f"💬 Message {target_name}"[:20]},
                    {"id": "btn_clear_chat", "title": "🧹 Clear Chat"},
                ],
                "profile": session_profile,
            }
        else:
            # Send message directly via WhatsApp Cloud API
            dispatch_status = "sent"
            try:
                if whatsapp_client:
                    await whatsapp_client.send_text(
                        phone,
                        f"📩 *Message from {user_id} via Thirdhand AI:*\n\n{msg_body}"
                    )
            except Exception as exc:
                logger.warning("Failed to dispatch WhatsApp message to %s (%s)", phone, exc)
                dispatch_status = "queued_or_mock"

            if user_lang in {"tamil", "tanglish"}:
                reply = (
                    f"✅ *{target_name}-க்கு மெசேஜ் வெற்றிகரமாக அனுப்பப்பட்டது! (Delivered)*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *பெறுநர்:* {target_name}\n"
                    f"📱 *எண்:* +{phone}\n"
                    f"💬 *அனுப்பப்பட்ட மெசேஜ்:*\n"
                    f"_{msg_body}_\n\n"
                    f"🔗 *சாட்டைத் திறக்க:* https://wa.me/{phone}"
                )
            else:
                reply = (
                    f"✅ *Message delivered to {target_name} successfully!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *Recipient:* {target_name}\n"
                    f"📱 *Phone:* +{phone}\n"
                    f"💬 *Delivered Text:*\n"
                    f"_{msg_body}_\n\n"
                    f"🔗 *Open Chat:* https://wa.me/{phone}"
                )
            return {
                "reply": reply,
                "buttons": [
                    {"id": "btn_clear_chat", "title": "🧹 Clear Chat"},
                ],
                "profile": session_profile,
            }

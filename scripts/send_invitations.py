import asyncio
import os
import sys
from pathlib import Path
from dotenv import dotenv_values
import httpx

ENV_PATH = Path(__file__).resolve().parent.parent / ".env.whatsapp"

WELCOME_TEXT = """👋 *Vanakkam bro! Thirdhand AI-kku ungalai anbudan varaverkirom!* ✨

Naan ungaloda personal 24/7 AI Super-Assistant. Ungalukku eppo enna thevai pattaalum enkitta ketkalam:

• 💬 *Edhavadhu sandhegam / Questions:* Cinema, study, doubts, recipes, tech
• 🎙️ *Voice Notes:* Tamil, Tanglish, English-la voice message anuppinaalum answer pannuven!
• 🛒 *Zepto 10-Min Groceries:* Milk, bread, snacks nu sonna cart ready panni kudupen!
• 🍽️ *Food & Hotels:* Unga locality-la sema budget / best food spots
• 🎬 *Movie Tickets & Booking assistance*
• 🎨 *AI Images:* 'Create a moon image' nu sonna picture generate pannuven!

_Try panni paarunga bro! Oru 'Hi' podunga illana unga voice-la pesunga!_ 🚀"""


async def send_welcome(phone_number: str) -> bool:
    env = dotenv_values(ENV_PATH)
    token = env.get("META_ACCESS_TOKEN")
    phone_id = env.get("META_PHONE_NUMBER_ID", "1380349731839361")
    
    clean_number = "".join(filter(str.isdigit, phone_number))
    if not clean_number.startswith("91") and len(clean_number) == 10:
        clean_number = "91" + clean_number

    url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_number,
        "type": "text",
        "text": {"body": WELCOME_TEXT},
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        data = resp.json()
        if resp.status_code == 200:
            print(f"✅ Successfully sent invitation to {clean_number}: Message ID {data.get('messages', [{}])[0].get('id')}")
            return True
        else:
            print(f"❌ Failed to send to {clean_number} (HTTP {resp.status_code}): {data}")
            return False


async def main():
    if len(sys.argv) < 2:
        print("Usage: python send_invitations.py <phone1> <phone2> ...")
        return
    numbers = sys.argv[1:]
    for num in numbers:
        await send_welcome(num)


if __name__ == "__main__":
    asyncio.run(main())

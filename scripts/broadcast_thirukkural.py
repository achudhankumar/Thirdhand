import asyncio
import os
from pathlib import Path
from dotenv import dotenv_values
import httpx

ENV_PATH = Path(__file__).resolve().parent.parent / ".env.whatsapp"

THIRUKKURAL_MSG = """✨ *இன்றைய திருக்குறள் & உத்வேகம் (Daily Inspiration)* ✨

📖 *திருக்குறள்:*
_"தெய்வத்தால் ஆகாது எனினும் முயற்சிதன்_
_மெய்வருத்தக் கூலி தரும்."_

💡 *விளக்கம் & மோட்டிவேஷன்:*
விதியால் அல்லது எந்த ஒரு சூழலாலும் ஒரு காரியம் முடியாது என்று தோன்றினாலும், நாம் செய்யும் அயராத உழைப்பும் தன்னம்பிக்கையான விடாமுயற்சியும் அதற்கான முழு பலனை நிச்சயம் பெற்றுத்தரும்! 🌟

எந்த ஒரு சவாலையும் கண்டு தயங்காமல், உங்கள் புதிய முயற்சிகளையும் இலக்குகளையும் தொடங்குங்கள். உங்கள் முயற்சி நிச்சயம் வெற்றியைத் தரும்! 🚀💪

— _Thirdhand AI Super-Assistant_ 🤝"""

async def send_broadcast():
    env = dotenv_values(ENV_PATH)
    token = env.get("META_ACCESS_TOKEN")
    phone_id = env.get("META_PHONE_NUMBER_ID", "1380349731839361")
    url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    recipients = ["919384146157", "916384965711"]
    for to in recipients:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": THIRUKKURAL_MSG},
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            data = resp.json()
            if resp.status_code == 200:
                msg_id = data.get("messages", [{}])[0].get("id")
                print(f"✅ Delivered to {to}: {msg_id}")
            else:
                print(f"❌ Failed for {to} ({resp.status_code}): {data}")

if __name__ == "__main__":
    asyncio.run(send_broadcast())

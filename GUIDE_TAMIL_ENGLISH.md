# Thirdhand 🤝 — வாட்ஸ்அப் ஏஐ ஏஜென்ட் (WhatsApp AI Super-Agent)
## முழுமையான தமிழ் & ஆங்கில வழிகாட்டி (Complete Tamil & English Setup Guide)

உங்கள் **Thirdhand WhatsApp AI Agent** இப்போது 100% முழுமையாகத் தயாராக உள்ளது! இதில் உள்ள அனைத்து 5 முக்கிய மாடியூல்களும் (Transit, Movie/Food Booking, E-Commerce Smart Shopper, Local Scout & TNEB/Medicine Utilities, Multimodal Voice/Image Assistant) இணைக்கப்பட்டு சோதிக்கப்பட்டுள்ளன.

---

## பாகம் 1: உங்கள் கம்ப்யூட்டரில் உடனடியாக ரன் செய்வது எப்படி? (1-Click Local Start)

நீங்கள் எந்த கோமண்டும் (Command) டைப் செய்யத் தேவையில்லை:
1. இந்த ZIP ஃபைலை உங்கள் கம்ப்யூட்டரில் Extract செய்யவும்.
2. **Windows** பயன்படுத்தினால்: உள்ளே இருக்கும் **`START_THIRDHAND_WINDOWS.bat`** ஃபைலை Double-Click செய்யவும்.
3. **Mac / Linux** பயன்படுத்தினால்: டெர்மினலில் `./start_thirdhand_mac_linux.sh` என்று ரன் செய்யவும்.
4. அதுவே தேவையான Python லைப்ரரிகளை இன்ஸ்டால் செய்து, சர்வரை ஸ்டார்ட் செய்து, உங்கள் பிரவுசரில் **`http://localhost:8000/simulator`** என்ற பக்கத்தை ஓப்பன் செய்யும்!

---

## பாகம் 2: இதை உங்கள் வாட்ஸ்அப்புடன் (WhatsApp) இணைக்க நீங்கள் தர வேண்டிய API Keys

வாட்ஸ்அப்பில் இந்த ஏஜென்ட் நேரடியாக வேலை செய்ய கீழ்க்கண்ட **இலவச (Free Tier)** கணக்குகளில் இருந்து API Keys எடுத்து `.env` ஃபைலில் போட வேண்டும்:

### 1. AI Brain — Google Gemini API Key (100% இலவசம்!)
- இணையதளம்: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Create API Key** கிளிக் செய்து கிடைக்கும் கீயை `.env` ஃபைலில் `GEMINI_API_KEY=` என்பதில் பேஸ்ட் செய்யவும். (அல்லது OpenAI பயன்படுத்த விரும்பினால் `OPENAI_API_KEY=` கொடுக்கலாம்).

### 2. Meta WhatsApp Cloud API (வாட்ஸ்அப் இணைப்பு)
- இணையதளம்: [https://developers.facebook.com/apps](https://developers.facebook.com/apps)
- **Create App** → **Other** → **Business** தேர்வு செய்து ஆப் உருவாக்கவும்.
- இடதுபுற மெனுவில் **WhatsApp → API Setup** செல்லவும்.
- அங்கிருந்து கீழ்க்கண்ட 3 விவரங்களை காப்பி செய்து `.env` ஃபைலில் பேஸ்ட் செய்யவும்:
  - `WHATSAPP_TOKEN=` (Temporary / System User Access Token)
  - `WHATSAPP_PHONE_NUMBER_ID=` (Phone Number ID — எண்கள் மட்டும்)
  - `APP_SECRET=` (**App Settings → Basic** பக்கத்தில் இருக்கும் App Secret)
  - `VERIFY_TOKEN=thirdhand_verify_2026` (இது ஏற்கனவே `.env` ஃபைலில் செட் செய்யப்பட்டுள்ளது)

### 3. DataStax Astra DB (உரையாடல் நினைவகம் — விருப்பத்தேர்வு / Optional)
- நீங்கள் Astra DB கொடுக்காவிட்டாலும், இந்த ஏஜென்ட் தானாகவே **Local File Memory (`data/local_sessions.json`)** மூலம் உங்கள் உரையாடல்களைச் சேமித்துக் கொள்ளும்!
- கிளவுட் டேட்டாபேஸ் வேண்டுமென்றால் [https://astra.datastax.com](https://astra.datastax.com) சென்று இலவச Serverless DB உருவாக்கி `ASTRA_DB_API_ENDPOINT` மற்றும் `ASTRA_DB_APPLICATION_TOKEN` கொடுக்கலாம்.

### 4. ரயில் & மேப்ஸ் (RapidAPI IRCTC & Google Maps — விருப்பத்தேர்வு)
- **ரயில் நேரடி தகவல் (IRCTC):** [https://rapidapi.com](https://rapidapi.com) இல் `IRCTC` (`irctc1.p.rapidapi.com`) Basic Free பிளான் சப்ஸ்கிரைப் செய்து `RAPIDAPI_KEY=` கொடுக்கவும்.
- **அருகிலுள்ள இடங்கள் (Google Places):** Google Cloud Console-இல் Places API ஆன் செய்து `GOOGLE_MAPS_API_KEY=` கொடுக்கவும்.

---

## பாகம் 3: Meta Portal-இல் Webhook இணைப்பது எப்படி?

1. உங்கள் கம்ப்யூட்டரில் சர்வர் ஓடிக்கொண்டிருக்கும்போது (`port 8000`), மற்றொரு டெர்மினலில் கீழ்க்கண்ட கமாண்டை ரன் செய்யவும்:
   ```bash
   ngrok http 8000
   ```
2. Ngrok கொடுக்கும் HTTPS லிங்கை காப்பி செய்து (உதாரணம்: `https://abcd-123.ngrok-free.app`), அதன் கடைசியில் `/webhook` சேர்த்து (`https://abcd-123.ngrok-free.app/webhook`) Meta Developer Portal-இல் **WhatsApp → Configuration → Callback URL** இடத்தில் பேஸ்ட் செய்யவும்.
3. **Verify Token** இடத்தில் `thirdhand_verify_2026` என்று கொடுத்து **Verify and Save** கிளிக் செய்யவும்.
4. கீழே **Webhook fields → Manage** கிளிக் செய்து **`messages`** என்பதை **Subscribe** செய்யவும்.
5. அவ்வளவுதான்! இப்போது உங்கள் வாட்ஸ்அப்பில் இருந்து டெஸ்ட் எண்ணிற்கு `"Hi"`, `"12606 train enga iruku?"`, `"Kamala theatre la ticket book pannu"`, அல்லது `"Best earbuds under 2000"` என்று மெசேஜ் அனுப்பிப் பாருங்கள்!

# Thirdhand — தமிழ் / English local setup

இந்த வெளியீடு Phase 1 பாதுகாப்பு மற்றும் நிலைத்தன்மை திருத்தங்கள் மட்டுமே. இது multi-tenant SaaS அல்லது முழுமையாகச் சான்றளிக்கப்பட்ட live booking சேவை அல்ல.

Use Python 3.11–3.14. Run `START_THIRDHAND_WINDOWS.bat` on Windows or `./start_thirdhand_mac_linux.sh` on macOS/Linux after installing a supported Python. The launcher creates a private `.env.development`, binds to `127.0.0.1`, and uses separate local simulator storage.

Open `http://127.0.0.1:8000/simulator`. Enter `SIMULATOR_TOKEN` from the private configuration file in the password field. அந்த token-ஐ பொது chat, screenshots அல்லது source control-ல் பகிர வேண்டாம். The launcher does not print secrets.

Real AI/media/provider features require the respective real keys. Gemini chat alone cannot run Whisper transcription. Install ffmpeg for voice decoding and the matching Playwright browser for validated merchant checkout/testing. No active merchant profile or completed payment is supplied.

மொழியைத் தேர்வு செய்யலாம்; நகரம் அல்லது location pin கொடுக்கலாம். Pincode கட்டாயமில்லை. தெரியாத இடங்கள், நேரடி ரயில் நிலை, விலை அல்லது திறந்திருக்கும் நேரம் ஊகிக்கப்படாது. Provider இல்லாவிட்டால் unavailable என்று தெரிவிக்கப்படும்.

Commands include `London`, `trichy`, `time`, `task call home`, `tasks`, `done 1`, `calendar`, `cancel`, `stop`, `start` and `reset`. Live reminder delivery and merchant checkout are disabled in the simulator. Verified WhatsApp reminders must stay inside the original customer-service window.

For production configuration, migrations, verification and rollback, read `README.md`, `PHASE1_IMPLEMENTATION_REPORT.md` and `docs/PHASE1_MIGRATIONS.md`. Production simulator routes are disabled. No deployment, Embedded Signup, Coexistence or Phase 2 work is included.

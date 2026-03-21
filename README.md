# ScamShield

> Built at **HooHacks 2026** — Protecting elderly individuals from phone scams in real time.

ScamShield is a Raspberry Pi device that listens to calls on speakerphone, detects scam patterns using the Gemini API, and instantly alerts both the person on the call and their family. No app to install. No behavior change required. Just put the call on speaker near the device.

---

## The Problem

Phone scams targeting the elderly cost Americans over **$3 billion per year**. Victims are often isolated, trusting, and pressured in the moment — before a family member can intervene. By the time anyone finds out, it's too late.

ScamShield gives elderly users a silent guardian that catches scams in real time and gets their family involved immediately.

---

## How It Works

```
Phone on speakerphone
        │
        ▼
 Grove Sound Sensor  ──── voice activity detected ────►  Pi microphone captures audio
        │
        ▼
  Whisper tiny.en  ──── local speech-to-text ────► 15-second transcript chunk (PRD)
        │
        ▼
  Gemini 1.5 Flash  ──── scam likelihood score 0–100 ────► + keyword fallback
        │
     score ≥ 70 or ≥ 2 scam keywords?
        │
        ▼
  ┌─────────────────────────────────────────────────────┐
  │                  ALERT PIPELINE                     │
  │  • Google Nest speaks ElevenLabs warning audio      │
  │  • Grove LED turns RED                              │
  │  • Grove Buzzer sounds for 2 seconds                │
  │  • Twilio SMS sent to family member                 │
  │  • SenseCAP Indicator shows "SCAM DETECTED"         │
  │  • Event logged to SQLite → synced to Postgres      │
  └─────────────────────────────────────────────────────┘
        │
        ▼
  Family Dashboard (Next.js + Auth0)
  — view all events, transcripts, timestamps from anywhere
```

---

## Features

- **Zero friction for elderly users** — no app, no buttons to learn, just speakerphone
- **Real-time detection** — alert fires within 10 seconds of a triggering phrase
- **Dual detection engine** — Gemini API scoring + keyword fallback (works offline)
- **Multi-channel alerts** — audio (Nest), visual (LED), haptic (buzzer), SMS (family)
- **Manual panic button** — Grove Button triggers the full alert pipeline instantly
- **Family dashboard** — Auth0-secured, accessible from anywhere via Vercel
- **Offline resilient** — keyword detection and local SQLite work without internet

---

## Hardware

| Component | Purpose |
|-----------|---------|
| Raspberry Pi 4B | Main compute |
| Logitech webcam (mic only) | Audio capture |
| Grove Base HAT | GPIO interface for Grove components |
| Grove Sound Sensor | Voice activity detection (VAD) |
| Grove LED (red + green) | Visual status indicator |
| Grove Buzzer | Audible alert |
| Grove Button | Manual alert trigger |
| SenseCAP Indicator | Live transcript + status display |
| Google Nest (any model) | ElevenLabs warning audio playback |

---

## Tech Stack

**Pi (Python 3.13)**
- `openai-whisper` — local speech-to-text (tiny.en model)
- `google-generativeai` — Gemini 1.5 Flash scam scoring
- `elevenlabs` — pre-generates warning audio at startup
- `pychromecast` — plays warning.mp3 on Google Nest
- `twilio` — SMS alerts to family
- `RPi.GPIO` — LED, buzzer, button control
- `fastapi` + `uvicorn` — local REST API
- `pyserial` — SenseCAP Indicator serial protocol
- `pyngrok` — exposes Pi API to internet for dashboard

**Dashboard (Next.js 14)**
- App Router + TypeScript
- Auth0 — family member authentication
- Tailwind CSS — styling
- Vercel — hosting

**Infrastructure**
- SQLite — local event storage on Pi (offline resilient)
- Railway Postgres — cloud sync for dashboard access
- ngrok — Pi → internet tunnel (URL kept server-side only)

---

## Project Structure

```
ScamShield/
├── pi/                         # All Raspberry Pi code
│   ├── main.py                 # Entry point — wires all components
│   ├── config.py               # Environment variables + constants
│   ├── audio_capture.py        # Grove Sound Sensor VAD + audio chunks
│   ├── stt.py                  # Whisper transcription
│   ├── detection.py            # Gemini scoring + keyword fallback
│   ├── alert.py                # Alert pipeline (Nest, LED, SMS, DB)
│   ├── startup.py              # Boot sequence (audio gen, Nest discovery, ngrok)
│   ├── server.py               # FastAPI REST API
│   ├── sync.py                 # SQLite → Postgres background sync
│   ├── sensecap.py             # SenseCAP serial display driver
│   ├── db.py                   # SQLite helpers
│   ├── keywords.py             # Scam keyword list
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       ├── test_detection.py
│       ├── test_alert.py
│       └── test_db.py
├── dashboard/                  # Next.js family dashboard
│   ├── app/
│   │   ├── dashboard/page.tsx  # Main dashboard view
│   │   ├── api/events/         # Proxy → Pi FastAPI
│   │   └── api/status/
│   ├── components/
│   │   ├── StatusBadge.tsx     # Pi online/offline/listening
│   │   ├── AlertBanner.tsx     # Most recent scam alert
│   │   ├── EventTable.tsx      # Paginated event log
│   │   └── EventRow.tsx        # Expandable event with transcript
│   ├── lib/api.ts
│   └── middleware.ts           # Auth0 route protection
├── sensecap/
│   └── firmware/
│       └── display.ino         # SenseCAP Arduino sketch
├── migrate.sql                 # Railway Postgres schema
├── startup.sh                  # Pi boot script
└── .gitignore
```

---

## Setup

### Prerequisites

- Raspberry Pi 4B running Raspberry Pi OS (64-bit)
- Python 3.13
- Node.js 18+
- All hardware components connected via Grove Base HAT
- Accounts: Gemini API, ElevenLabs, Twilio, Auth0, Railway, ngrok, Vercel

### Pi Setup

```bash
# Clone the repo
git clone https://github.com/TristanGru/ScamShield.git
cd ScamShield

# Create and activate venv
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r pi/requirements.txt

# Configure environment
cp pi/.env.example pi/.env
# Edit pi/.env and fill in all API keys and config values

# Initialize database
python pi/db.py --init

# Run ScamShield
python pi/main.py

# Or use the boot script (set to run at startup)
chmod +x startup.sh
./startup.sh
```

### Dashboard Setup

```bash
cd dashboard
npm install

# Configure environment
cp .env.local.example .env.local
# Fill in AUTH0_* and PI_API_URL values

# Run locally
npm run dev

# Deploy to Vercel
vercel --prod
```

### Railway Postgres

```bash
# Run migrate.sql against your Railway Postgres instance
psql $POSTGRES_URL -f migrate.sql
```

---

## Environment Variables

Copy `pi/.env.example` to `pi/.env` and fill in:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `ELEVENLABS_API_KEY` | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | Voice ID for warning audio |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Twilio phone number |
| `TWILIO_TO_NUMBER` | Family member's phone number |
| `POSTGRES_URL` | Railway Postgres connection string |
| `NGROK_AUTHTOKEN` | ngrok auth token |
| `AUDIO_DEVICE_INDEX` | Microphone device index (run `python -m sounddevice` to find) |
| `NEST_IP` | (Optional) Hardcoded Nest IP if mDNS is blocked |

---

## Detection Logic

ScamShield fires an alert when **either** condition is met:

- Gemini scam score ≥ 70 (out of 100)
- 2 or more scam keywords matched (whole-word, case-insensitive)

**Keyword categories:** IRS/government impersonation, gift card demands, arrest threats, lottery scams, tech support fraud, grandparent bail scams, refund/overpayment scams, urgency phrases ("don't hang up", "act now"), and more.

Gemini failure → keyword-only fallback. Internet outage → full offline keyword detection.

---

## API Endpoints

The Pi runs a FastAPI server on port 8000, exposed via ngrok.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/status` | Pi status (listening, Nest connected, uptime) |
| GET | `/events` | Paginated event list |
| POST | `/events` | Create event (for testing) |
| GET | `/metrics` | Prometheus-format counters |

---

## Running Tests

```bash
cd ScamShield
python -m pytest pi/tests/ -v
```

---

## Prize Tracks

- **Best Accessibility & Empowerment** — designed specifically to protect elderly users
- **Best Use of Gemini API** — real-time scam scoring via Gemini 1.5 Flash
- **Best Use of ElevenLabs** — high-quality voice warning pre-generated and played via Nest
- **Best Use of Auth0** — family dashboard authentication
- **Best Use of GoDaddy Domain** — production domain for the family dashboard

---

## Team

Built at **HooHacks 2026** by students from the University of Virginia.

---

## License

MIT

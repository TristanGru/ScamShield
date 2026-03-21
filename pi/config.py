"""
config.py — Loads .env and defines all constants used across the Pi system.
Fails fast with a clear error message if any required variable is missing.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the pi/ directory
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        print(f"[FATAL] Missing required environment variable: {key}", file=sys.stderr)
        print(f"        Copy pi/.env.example to pi/.env and fill in all values.", file=sys.stderr)
        sys.exit(1)
    return val


def _optional(key: str, default: str) -> str:
    return os.getenv(key, default)


# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")

# ── ElevenLabs ────────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY: str = _require("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID: str = _require("ELEVENLABS_VOICE_ID")

# ── Twilio ────────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID: str = _require("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN: str = _require("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER: str = _require("TWILIO_FROM_NUMBER")
TWILIO_TO_NUMBER: str = _require("TWILIO_TO_NUMBER")

# ── Database ──────────────────────────────────────────────────────────────────
SQLITE_DB_PATH: str = _optional("SQLITE_DB_PATH", "/data/scamshield.db")
POSTGRES_URL: str = _optional("POSTGRES_URL", "")

# ── ngrok ─────────────────────────────────────────────────────────────────────
NGROK_AUTHTOKEN: str = _optional("NGROK_AUTHTOKEN", "")

# ── Audio ─────────────────────────────────────────────────────────────────────
AUDIO_DEVICE_INDEX: int = int(_optional("AUDIO_DEVICE_INDEX", "0"))
VAD_THRESHOLD: int = int(_optional("VAD_THRESHOLD", "500"))
CHUNK_DURATION_SECONDS: int = int(_optional("CHUNK_DURATION_SECONDS", "15"))
SAMPLE_RATE: int = 16000
CHANNELS: int = 1
SAMPLE_WIDTH: int = 2  # 16-bit

# ── Grove HAT GPIO Pins ───────────────────────────────────────────────────────
GPIO_LED_RED_PIN: int = int(_optional("GPIO_LED_RED_PIN", "18"))
GPIO_LED_GREEN_PIN: int = int(_optional("GPIO_LED_GREEN_PIN", "17"))
GPIO_BUZZER_PIN: int = int(_optional("GPIO_BUZZER_PIN", "23"))
GPIO_BUTTON_PIN: int = int(_optional("GPIO_BUTTON_PIN", "24"))
GPIO_SOUND_SENSOR_PIN: int = int(_optional("GPIO_SOUND_SENSOR_PIN", "0"))

# ── SenseCAP ──────────────────────────────────────────────────────────────────
SENSECAP_SERIAL_PORT: str = _optional("SENSECAP_SERIAL_PORT", "/dev/ttyUSB0")
SENSECAP_BAUD_RATE: int = int(_optional("SENSECAP_BAUD_RATE", "115200"))

# ── Detection Thresholds ──────────────────────────────────────────────────────
SCAM_SCORE_THRESHOLD: int = int(_optional("SCAM_SCORE_THRESHOLD", "75"))
SCAM_KEYWORD_MIN_MATCHES: int = int(_optional("SCAM_KEYWORD_MIN_MATCHES", "2"))
SMS_DEBOUNCE_SECONDS: int = int(_optional("SMS_DEBOUNCE_SECONDS", "60"))

# ── LED Reset Delay ───────────────────────────────────────────────────────────
LED_RESET_SECONDS: int = 10

# ── Warning audio cache path ──────────────────────────────────────────────────
WARNING_AUDIO_PATH: str = str(Path(__file__).parent / "warning.mp3")

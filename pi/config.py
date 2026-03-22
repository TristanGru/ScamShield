"""
config.py — Loads .env and defines all constants used across the Pi system.
Fails fast with a clear error message if any required variable is missing.
"""

import os
import socket
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
GEMINI_MODEL: str = _optional("GEMINI_MODEL", "gemini-3.1-flash-lite-preview").strip()

# ── ElevenLabs ────────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY: str = _require("ELEVENLABS_API_KEY")
# Premade "Adam" (male) — official catalog voice, not the Voice Library marketplace.
# Free tier: API allows premade/default voices; *library* / shared marketplace voices return 402.
ELEVENLABS_DEFAULT_VOICE_ID: str = "pNInz6obpgDQGcFmaJgB"
_ELEVEN_RAW = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
ELEVENLABS_VOICE_ID: str = _ELEVEN_RAW if _ELEVEN_RAW else ELEVENLABS_DEFAULT_VOICE_ID
# Voice for Nest warning only (defaults to ELEVENLABS_VOICE_ID). Strip whitespace — stray spaces break the API.
_ELEVEN_WARN = os.getenv("ELEVENLABS_WARNING_VOICE_ID", "").strip()
ELEVENLABS_WARNING_VOICE_ID: str = _ELEVEN_WARN if _ELEVEN_WARN else ELEVENLABS_VOICE_ID
ELEVENLABS_MODEL_ID: str = _optional("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()
ELEVENLABS_OUTPUT_FORMAT: str = _optional("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128").strip()

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
GPIO_LED_RED_PIN: int = int(_optional("GPIO_LED_RED_PIN", "24"))
GPIO_LED_GREEN_PIN: int = int(_optional("GPIO_LED_GREEN_PIN", "23"))
GPIO_BUZZER_PIN: int = int(_optional("GPIO_BUZZER_PIN", "16"))   # D16
GPIO_BUTTON_PIN: int = int(_optional("GPIO_BUTTON_PIN", "5"))    # D5
GPIO_SOUND_SENSOR_PIN: int = int(_optional("GPIO_SOUND_SENSOR_PIN", "0"))

# ── SenseCAP ──────────────────────────────────────────────────────────────────
SENSECAP_SERIAL_PORT: str = _optional("SENSECAP_SERIAL_PORT", "/dev/ttyUSB0")
SENSECAP_BAUD_RATE: int = int(_optional("SENSECAP_BAUD_RATE", "115200"))

# ── Detection Thresholds ──────────────────────────────────────────────────────
SCAM_SCORE_THRESHOLD: int = int(_optional("SCAM_SCORE_THRESHOLD", "75"))
SCAM_KEYWORD_MIN_MATCHES: int = int(_optional("SCAM_KEYWORD_MIN_MATCHES", "2"))
SMS_DEBOUNCE_SECONDS: int = int(_optional("SMS_DEBOUNCE_SECONDS", "60"))
ALERT_COOLDOWN_SECONDS: int = int(_optional("SCAM_ALERT_COOLDOWN", "30"))

# ── Conversation context (rolling transcript buffer for Gemini) ───────────────
CONTEXT_CHUNKS: int = int(_optional("SCAM_CONTEXT_CHUNKS", "5"))
CONTEXT_SILENCE_RESET: int = int(_optional("SCAM_CONTEXT_SILENCE_RESET", "3"))

# ── LED Reset Delay ───────────────────────────────────────────────────────────
LED_RESET_SECONDS: int = 10

# ── Warning audio cache path ──────────────────────────────────────────────────
WARNING_AUDIO_PATH: str = str(Path(__file__).parent / "warning.mp3")
# JSON sidecar: voice_id + model_id used to build warning.mp3; if env changes, audio is regenerated.
WARNING_AUDIO_META_PATH: str = str(Path(__file__).parent / "warning.mp3.meta")

# Spoken text for Nest / gTTS (ElevenLabs at startup). Must NOT contain any phrase from
# SCAM_KEYWORDS in keywords.py — the mic can pick up the speaker and re-trigger detection.
NEST_WARNING_TEXT: str = (
    "This is a friendly reminder from your home device. "
    "For your security, avoid sharing sensitive account information. "
    "You can disconnect if something feels off."
)

# ── Pi LAN IP (used to build HTTP URL for Chromecast audio streaming) ─────────
def _detect_lan_ip() -> str:
    """Return the Pi's LAN IP by routing toward an external host (no packets sent)."""
    override = os.getenv("PI_LAN_IP", "")
    if override:
        return override
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

PI_LAN_IP: str = _detect_lan_ip()
PI_API_PORT: int = int(_optional("PI_API_PORT", "8000"))

# ── Text-only mode (no ElevenLabs API, Nest/Chromecast, or SenseCAP serial) ───
# Set SCAMSHIELD_TEXT_ONLY=1 for dev/demo — integrations are logged/printed as plain text.
TEXT_ONLY_MODE: bool = _optional("SCAMSHIELD_TEXT_ONLY", "0").lower() in ("1", "true", "yes")

# ── Testing / dev safety switches ─────────────────────────────────────────────
SKIP_SMS: bool = _optional("SCAMSHIELD_SKIP_SMS", "0").lower() in ("1", "true", "yes")
SKIP_BUZZER: bool = _optional("SCAMSHIELD_SKIP_BUZZER", "0").lower() in ("1", "true", "yes")
SKIP_GEMINI: bool = _optional("SCAMSHIELD_SKIP_GEMINI", "0").lower() in ("1", "true", "yes")

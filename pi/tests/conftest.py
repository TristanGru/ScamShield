"""
Ensure both the repo root (package `pi`) and `pi/` (legacy `config` imports) are on sys.path.
Set dummy API keys so `pi.config` can load in tests without a real .env.
"""

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_PI = _ROOT / "pi"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_PI) not in sys.path:
    sys.path.insert(0, str(_PI))

for _key, _val in (
    ("GEMINI_API_KEY", "test-gemini"),
    ("ELEVENLABS_API_KEY", "test-eleven"),
    ("ELEVENLABS_VOICE_ID", "test-voice"),
    ("TWILIO_ACCOUNT_SID", "ACtest"),
    ("TWILIO_AUTH_TOKEN", "test-twilio"),
    ("TWILIO_FROM_NUMBER", "+10000000000"),
    ("TWILIO_TO_NUMBER", "+10000000001"),
):
    os.environ.setdefault(_key, _val)

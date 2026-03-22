"""
stt.py — Speech-to-text using Vosk (offline, ARM64/Pi 4 compatible).

Transcribes audio chunks to plain text. The transcript is passed to Gemini
for scam detection (with keyword fallback if Gemini is unavailable).
"""

import io
import json
import logging
import time
import wave

logger = logging.getLogger(__name__)

_model = None

VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"


def load_model() -> None:
    """Load Vosk small-en-us model. Auto-downloads on first run (~40 MB)."""
    global _model
    from vosk import Model, SetLogLevel

    SetLogLevel(-1)

    logger.info("Loading Vosk model '%s'…", VOSK_MODEL_NAME)
    t0 = time.monotonic()
    _model = Model(model_name=VOSK_MODEL_NAME)
    elapsed = time.monotonic() - t0
    logger.info("Vosk model loaded in %.1fs", elapsed)


def transcribe(wav_bytes: bytes) -> str:
    """
    Transcribe a WAV bytes object to plain text.
    Returns empty string on failure — never raises.
    Full free-form transcription; scam detection is handled downstream by Gemini.
    """
    if _model is None:
        logger.error("Vosk model not loaded — call load_model() first")
        return ""

    try:
        from vosk import KaldiRecognizer

        wf = wave.open(io.BytesIO(wav_bytes), "rb")
        rec = KaldiRecognizer(_model, wf.getframerate())
        rec.SetWords(False)

        t0 = time.monotonic()
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        text = result.get("text", "").strip()
        elapsed = time.monotonic() - t0

        logger.info(
            "Transcribed %d bytes in %.2fs: %r",
            len(wav_bytes),
            elapsed,
            text[:80] + ("…" if len(text) > 80 else ""),
        )
        return text

    except Exception as exc:
        logger.error("Vosk transcription failed: %s", exc)
        return ""

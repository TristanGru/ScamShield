"""
stt.py — Speech-to-text using Vosk (offline, ARM64/Pi 4 compatible).

The model is downloaded once on first run and reused for all chunks.
Audio is passed as in-memory WAV bytes — never persisted.
"""

import io
import json
import logging
import time
import wave

logger = logging.getLogger(__name__)

_model = None

VOSK_MODEL_NAME = "vosk-model-en-us-0.22-lgraph"


def load_model() -> None:
    """Load Vosk English model. Auto-downloads on first run (~40 MB)."""
    global _model
    from vosk import Model, SetLogLevel

    SetLogLevel(-1)

    logger.info("Loading Vosk model '%s' (downloads on first run)…", VOSK_MODEL_NAME)
    t0 = time.monotonic()
    _model = Model(model_name=VOSK_MODEL_NAME)
    elapsed = time.monotonic() - t0
    logger.info("Vosk model loaded in %.1fs", elapsed)


def transcribe(wav_bytes: bytes) -> str:
    """
    Transcribe a WAV bytes object to text.
    Returns empty string on failure — never raises.
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

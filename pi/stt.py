"""
stt.py — Speech-to-text using Whisper tiny.en (local, no network required).

The model is loaded once at startup and reused for all chunks.
Audio is passed as in-memory bytes — never written to disk.
"""

import io
import logging
import time
import tempfile
import os

logger = logging.getLogger(__name__)

_model = None


def load_model() -> None:
    """Load Whisper tiny.en model into memory. Call once at startup."""
    global _model
    import whisper

    logger.info("Loading Whisper tiny.en model…")
    t0 = time.monotonic()
    _model = whisper.load_model("tiny.en")
    elapsed = time.monotonic() - t0
    logger.info("Whisper model loaded in %.1fs", elapsed)


def transcribe(wav_bytes: bytes) -> str:
    """
    Transcribe a WAV bytes object to text.
    Returns empty string on failure — never raises.

    Whisper requires a file path, so we write to a temp file and immediately
    delete it after transcription. The audio data is NOT persisted — temp file
    lifetime is milliseconds.
    """
    if _model is None:
        logger.error("Whisper model not loaded — call load_model() first")
        return ""

    # Write to a temp file (Whisper API requires file path, not bytes)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp_path = tmp.name

        t0 = time.monotonic()
        result = _model.transcribe(tmp_path, language="en", fp16=False)
        elapsed = time.monotonic() - t0

        text = result.get("text", "").strip()
        logger.info(
            "Transcribed %d bytes in %.2fs: %r",
            len(wav_bytes),
            elapsed,
            text[:80] + ("…" if len(text) > 80 else ""),
        )
        return text

    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        return ""

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

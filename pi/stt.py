"""
stt.py — Speech-to-text using faster-whisper (CTranslate2, ARM64-compatible).

The model is loaded once at startup and reused for all chunks.
Audio is passed as in-memory bytes — never written to disk long-term.
"""

import logging
import os
import tempfile
import time

logger = logging.getLogger(__name__)

_model = None


def load_model() -> None:
    """Load faster-whisper tiny.en model into memory. Call once at startup."""
    global _model
    from faster_whisper import WhisperModel

    logger.info("Loading faster-whisper tiny.en model (cpu / int8)…")
    t0 = time.monotonic()
    _model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    elapsed = time.monotonic() - t0
    logger.info("Whisper model loaded in %.1fs", elapsed)


def transcribe(wav_bytes: bytes) -> str:
    """
    Transcribe a WAV bytes object to text.
    Returns empty string on failure — never raises.

    faster-whisper accepts a file path, so we write to a short-lived temp file.
    """
    if _model is None:
        logger.error("Whisper model not loaded — call load_model() first")
        return ""

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp_path = tmp.name

        t0 = time.monotonic()
        segments, info = _model.transcribe(tmp_path, language="en", beam_size=1)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        elapsed = time.monotonic() - t0

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

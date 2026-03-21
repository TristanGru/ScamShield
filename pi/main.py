"""
main.py — ScamShield entry point.

Wires audio capture → STT → detection → alert pipeline, plus:
  - FastAPI server (background thread via uvicorn)
  - Sync worker (background thread)
  - Grove Button GPIO interrupt for manual alert trigger
  - SenseCAP display updates throughout
"""

import logging
import queue
import signal
import sys
import threading
import time

import uvicorn

import alert
import detection
import sensecap
import server as server_module
import stt
import sync as sync_module
from audio_capture import AudioCapture
import os
from config import GPIO_BUTTON_PIN

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
from startup import run_startup

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Try GPIO for button interrupt
try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO = None
    _GPIO_AVAILABLE = False

_shutdown_event = threading.Event()


# ── GPIO button ───────────────────────────────────────────────────────────────

def _setup_button_interrupt() -> None:
    """Register Grove Button on GPIO_BUTTON_PIN for manual alert trigger (FR-021)."""
    if not _GPIO_AVAILABLE or GPIO is None:
        logger.warning("GPIO not available — manual button disabled")
        return
    try:
        GPIO.setup(GPIO_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(
            GPIO_BUTTON_PIN,
            GPIO.RISING,
            callback=_on_button_press,
            bouncetime=2000,
        )
        logger.info("Grove Button interrupt registered on GPIO %d", GPIO_BUTTON_PIN)
    except Exception as exc:
        logger.error("Button interrupt setup failed: %s", exc)


def _on_button_press(channel: int) -> None:
    """Callback fired on button press — fires a manual alert (FR-021)."""
    logger.info("Manual button press detected (GPIO %d)", channel)
    threading.Thread(
        target=alert.fire_alert,
        kwargs={
            "trigger_type": "manual",
            "score": None,
            "keywords": [],
            "transcript": "(Manual trigger by user)",
        },
        daemon=True,
    ).start()


# ── FastAPI server ────────────────────────────────────────────────────────────

def _start_api_server() -> None:
    """Run uvicorn in a daemon thread."""
    config = uvicorn.Config(
        app="server:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        loop="asyncio",
    )
    uvicorn_server = uvicorn.Server(config)
    uvicorn_server.run()


# ── Audio processing loop ─────────────────────────────────────────────────────

def _processing_loop(capture: AudioCapture) -> None:
    """
    Main loop: drain chunk_queue → transcribe → score → alert.
    Runs on the main thread after all setup is done.
    """
    logger.info("Audio processing loop started")
    server_module.set_listening(True)
    sensecap.set_listening()

    while not _shutdown_event.is_set():
        try:
            wav_bytes = capture.chunk_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        # Transcribe
        transcript = stt.transcribe(wav_bytes)
        if not transcript.strip():
            continue

        logger.debug("Transcript: %s", transcript[:80])
        sensecap.set_transcript(transcript)

        # Score
        score, keywords = detection.score_transcript(transcript)
        logger.info("Score=%d keywords=%s", score, keywords)

        # Alert if needed
        if detection.should_alert(score, keywords):
            alert.fire_alert(
                trigger_type="auto",
                score=score,
                keywords=keywords,
                transcript=transcript,
            )

    server_module.set_listening(False)
    logger.info("Audio processing loop stopped")


# ── Shutdown handler ──────────────────────────────────────────────────────────

def _handle_shutdown(signum, frame) -> None:
    logger.info("Shutdown signal received (%d) — stopping…", signum)
    _shutdown_event.set()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    # Startup sequence
    startup_result = run_startup()
    logger.info("Startup result: %s", startup_result)

    # Load Whisper model once
    logger.info("Loading Whisper model…")
    stt.load_model()
    logger.info("Whisper model ready")

    # FastAPI server
    api_thread = threading.Thread(target=_start_api_server, daemon=True, name="api-server")
    api_thread.start()
    logger.info("FastAPI server started on :8000")

    # Sync worker
    sync_module.start_sync_worker()
    logger.info("Sync worker started")

    # GPIO button
    _setup_button_interrupt()

    # Audio capture
    capture = AudioCapture()
    capture.start()
    logger.info("Audio capture started")

    try:
        _processing_loop(capture)
    finally:
        capture.stop()
        sensecap.set_ready()
        alert.cleanup_gpio()
        if _GPIO_AVAILABLE and GPIO is not None:
            try:
                GPIO.cleanup()
            except Exception:
                pass
        sensecap.disconnect()
        logger.info("ScamShield shutdown complete")


if __name__ == "__main__":
    main()

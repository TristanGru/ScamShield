"""
main.py — ScamShield entry point (PRD Phase 1: detection loop + hardware alerts).

Wires audio capture → STT → scam detection → alert pipeline, plus:
  - FastAPI server (background thread via uvicorn)
  - Sync worker (background thread)
  - Manual button via hardware.setup_manual_button
  - SenseCAP display updates throughout
"""

import logging
import os
import queue
import signal
import threading

import uvicorn

import alert
import sensecap
import server as server_module
import stt
import sync as sync_module
from audio_capture import AudioCapture
from hardware import setup_manual_button
from startup import run_startup

import detection

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_shutdown_event = threading.Event()


def _on_button_press(channel: int) -> None:
    """Physical button → same alert chain as auto-detection (PRD Phase 1)."""
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


def _processing_loop(capture: AudioCapture) -> None:
    """
    Main loop: drain chunk_queue → transcribe → score → alert.
    """
    logger.info("Audio processing loop started")
    server_module.set_listening(True)
    sensecap.set_listening()

    while not _shutdown_event.is_set():
        try:
            wav_bytes = capture.chunk_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        transcript = stt.transcribe(wav_bytes)
        if not transcript.strip():
            continue

        logger.debug("Transcript: %s", transcript[:80])
        sensecap.set_transcript(transcript)

        score, keywords = detection.score_transcript(transcript)
        logger.info("Score=%d keywords=%s", score, keywords)

        if detection.should_alert(score, keywords):
            alert.fire_alert(
                trigger_type="auto",
                score=score,
                keywords=keywords,
                transcript=transcript,
            )

    server_module.set_listening(False)
    logger.info("Audio processing loop stopped")


def _handle_shutdown(signum, frame) -> None:
    logger.info("Shutdown signal received (%d) — stopping…", signum)
    _shutdown_event.set()


def main() -> None:
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    startup_result = run_startup()
    logger.info("Startup result: %s", startup_result)

    logger.info("Loading Whisper model…")
    stt.load_model()
    logger.info("Whisper model ready")

    api_thread = threading.Thread(target=_start_api_server, daemon=True, name="api-server")
    api_thread.start()
    logger.info("FastAPI server started on :8000")

    sync_module.start_sync_worker()
    logger.info("Sync worker started")

    setup_manual_button(_on_button_press)

    capture = AudioCapture()
    capture.start()
    logger.info("Audio capture started")

    try:
        _processing_loop(capture)
    finally:
        capture.stop()
        sensecap.set_ready()
        alert.cleanup_gpio()
        sensecap.disconnect()
        logger.info("ScamShield shutdown complete")


if __name__ == "__main__":
    main()

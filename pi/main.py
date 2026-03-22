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
from collections import deque

import uvicorn

import alert
import sensecap
import server as server_module
import stt
import sync as sync_module
from audio_capture import AudioCapture
from hardware import setup_manual_button
from startup import run_startup
from config import CONTEXT_CHUNKS, CONTEXT_SILENCE_RESET

import detection

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_shutdown_event = threading.Event()

# Bounded queue between STT worker and detection: when Gemini is slower than Vosk,
# the STT thread blocks on put() and stops draining chunk_queue → backpressure to capture.
_TRANSCRIPT_QUEUE_MAX = 10


def _stt_pipeline_worker(capture: AudioCapture, transcript_queue: queue.Queue[str]) -> None:
    """
    Drain audio chunks from capture.chunk_queue, run Vosk, push plain text downstream.

    Pipelining: while the main thread waits on Gemini for chunk N, this thread can
    transcribe chunk N+1 so wall-clock work overlaps (STT || Gemini per step).
    """
    logger.info("STT pipeline worker started")
    while not _shutdown_event.is_set():
        try:
            wav_bytes = capture.chunk_queue.get(timeout=1.0)
        except queue.Empty:
            continue
        transcript = stt.transcribe(wav_bytes)
        while not _shutdown_event.is_set():
            try:
                transcript_queue.put(transcript, timeout=0.5)
                break
            except queue.Full:
                continue
    logger.info("STT pipeline worker stopped")


def _on_button_press(channel: int) -> None:
    """Physical button: clear active alert, or fire manual alert if idle."""
    logger.info("Button press detected (GPIO %d)", channel)
    if alert.is_alert_active():
        alert.clear_alert()
        logger.info("Alert cleared by button press")
    else:
        threading.Thread(
            target=alert.fire_alert,
            kwargs={
                "trigger_type": "manual",
                "score": None,
                "keywords": [],
                "transcript": "(Manual trigger by user)",
                "conversation_context": "",
                "reason": "manual",
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


def _processing_loop(transcript_queue: queue.Queue[str]) -> None:
    """
    Main loop: drain transcript queue (filled by STT worker) → score → alert.

    STT runs in a dedicated thread so Vosk can overlap with Gemini/network on
    the previous chunk.

    A rolling deque keeps the last CONTEXT_CHUNKS transcripts so Gemini
    sees multi-chunk conversation context.  Keywords are matched against
    the current chunk only (via current_chunk param) to avoid re-triggering
    on old text.
    """
    logger.info("Audio processing loop started (STT pipelined)")
    server_module.set_listening(True)
    sensecap.set_listening()

    transcript_buffer: deque[str] = deque(maxlen=CONTEXT_CHUNKS)
    silence_count = 0

    while not _shutdown_event.is_set():
        try:
            transcript = transcript_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        if not transcript.strip():
            silence_count += 1
            if silence_count >= CONTEXT_SILENCE_RESET and transcript_buffer:
                logger.debug(
                    "Silence reset (%d empty chunks) — clearing transcript buffer",
                    silence_count,
                )
                transcript_buffer.clear()
            continue

        silence_count = 0
        transcript_buffer.append(transcript)

        logger.debug("Transcript: %s", transcript[:80])
        sensecap.set_transcript(transcript)

        full_context = "\n---\n".join(transcript_buffer)
        analysis = detection.analyze_transcript(
            full_context, current_chunk=transcript,
        )
        logger.info(
            "Score=%d keywords=%s (buffer=%d chunks)",
            analysis.score,
            analysis.matched_keywords,
            len(transcript_buffer),
        )

        if detection.should_alert(analysis.score, analysis.matched_keywords):
            alert.fire_alert(
                trigger_type="auto",
                score=analysis.score,
                keywords=analysis.matched_keywords,
                transcript=transcript,
                conversation_context=full_context,
                reason=analysis.reason or "none",
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

    logger.info("Loading Vosk model…")
    stt.load_model()
    logger.info("Vosk model ready")

    api_thread = threading.Thread(target=_start_api_server, daemon=True, name="api-server")
    api_thread.start()
    logger.info("FastAPI server started on :8000")

    sync_module.start_sync_worker()
    logger.info("Sync worker started")

    setup_manual_button(_on_button_press)

    transcript_queue: queue.Queue[str] = queue.Queue(maxsize=_TRANSCRIPT_QUEUE_MAX)
    capture = AudioCapture()
    stt_thread = threading.Thread(
        target=_stt_pipeline_worker,
        args=(capture, transcript_queue),
        daemon=True,
        name="stt-pipeline",
    )
    stt_thread.start()
    capture.start()
    logger.info("Audio capture started (STT pipeline worker running)")

    try:
        _processing_loop(transcript_queue)
    finally:
        capture.stop()
        sensecap.set_ready()
        alert.cleanup_gpio()
        sensecap.disconnect()
        logger.info("ScamShield shutdown complete")


if __name__ == "__main__":
    main()

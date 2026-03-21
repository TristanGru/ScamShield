"""
audio_capture.py — Captures audio from the Logitech webcam mic.

Uses Grove Sound Sensor as a Voice Activity Detector (VAD):
  - Polls the sound sensor every 100ms
  - When volume exceeds VAD_THRESHOLD, starts accumulating audio
  - After CHUNK_DURATION_SECONDS of audio, puts a WAV bytes object into the queue
  - Audio is NEVER written to disk — held in memory only (BL-006)
"""

import io
import logging
import queue
import threading
import time
import wave
from typing import Optional

import pyaudio

from config import (
    AUDIO_DEVICE_INDEX,
    VAD_THRESHOLD,
    CHUNK_DURATION_SECONDS,
    SAMPLE_RATE,
    CHANNELS,
    SAMPLE_WIDTH,
    GPIO_SOUND_SENSOR_PIN,
)

logger = logging.getLogger(__name__)

# Try importing GPIO (will fail on non-Pi systems — graceful degradation)
try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO = None
    _GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available — VAD will use PyAudio amplitude instead")


FRAMES_PER_BUFFER = 1024


def _read_sound_sensor_level() -> int:
    """Read the Grove Sound Sensor analog level (0–1023).
    Falls back to a constant above threshold if GPIO unavailable.
    """
    if not _GPIO_AVAILABLE or GPIO is None:
        return VAD_THRESHOLD + 100  # always listening in dev/test
    try:
        # Grove analog read via ADC on Grove Base HAT
        from grove.adc import ADC
        adc = ADC()
        return adc.read(GPIO_SOUND_SENSOR_PIN)
    except Exception as exc:
        logger.debug("Sound sensor read failed: %s", exc)
        return VAD_THRESHOLD + 100


def _build_wav_bytes(frames: list[bytes]) -> bytes:
    """Package raw PCM frames into a WAV-format bytes object."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))
    return buf.getvalue()


class AudioCapture:
    """
    Continuous audio capture loop.
    Puts WAV bytes chunks into `chunk_queue` whenever voice activity is detected.
    """

    def __init__(self) -> None:
        self.chunk_queue: queue.Queue[bytes] = queue.Queue(maxsize=10)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._pa = pyaudio.PyAudio()

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True, name="audio-capture")
        self._thread.start()
        logger.info("Audio capture started on device index %d", AUDIO_DEVICE_INDEX)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._pa.terminate()
        logger.info("Audio capture stopped")

    def _capture_loop(self) -> None:
        frames_per_chunk = int(SAMPLE_RATE * CHUNK_DURATION_SECONDS)

        try:
            stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=AUDIO_DEVICE_INDEX,
                frames_per_buffer=FRAMES_PER_BUFFER,
            )
        except OSError as exc:
            logger.error("Failed to open audio stream: %s", exc)
            return

        logger.info(
            "Capture loop running — chunk=%ds, VAD_THRESHOLD=%d",
            CHUNK_DURATION_SECONDS,
            VAD_THRESHOLD,
        )

        frames: list[bytes] = []
        collecting = False
        frames_collected = 0

        while not self._stop_event.is_set():
            level = _read_sound_sensor_level()

            if level >= VAD_THRESHOLD:
                if not collecting:
                    logger.debug("VAD triggered (level=%d) — starting chunk capture", level)
                    collecting = True
                    frames = []
                    frames_collected = 0

            if collecting:
                try:
                    data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    frames.append(data)
                    frames_collected += FRAMES_PER_BUFFER

                    if frames_collected >= frames_per_chunk:
                        wav_bytes = _build_wav_bytes(frames)
                        try:
                            self.chunk_queue.put_nowait(wav_bytes)
                            logger.debug("Chunk queued (%d bytes)", len(wav_bytes))
                        except queue.Full:
                            logger.warning("Chunk queue full — dropping oldest chunk")
                            try:
                                self.chunk_queue.get_nowait()
                            except queue.Empty:
                                pass
                            self.chunk_queue.put_nowait(wav_bytes)

                        frames = []
                        frames_collected = 0
                        collecting = False
                except OSError as exc:
                    logger.error("Audio read error: %s — restarting capture", exc)
                    break
            else:
                time.sleep(0.1)

        stream.stop_stream()
        stream.close()
        logger.info("Capture loop exited")

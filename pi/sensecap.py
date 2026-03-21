"""
sensecap.py — Serial communication with the SenseCAP Indicator display.

Sends simple line-based commands over USB serial. The SenseCAP firmware
(sensecap/firmware/display.ino) parses these commands and updates the display.

Protocol:
  STATUS:<status_text>\n   — set the top status line
  TEXT:<body_text>\n       — set the scrolling body text

If the serial port is unavailable, all methods silently no-op (EC-012).
"""

import logging
import threading
from typing import Optional

import serial

from config import SENSECAP_SERIAL_PORT, SENSECAP_BAUD_RATE, TEXT_ONLY_MODE

logger = logging.getLogger(__name__)

_serial: Optional[serial.Serial] = None
_lock = threading.Lock()


def connect() -> bool:
    """Open the SenseCAP serial port. Returns True if successful."""
    global _serial
    if TEXT_ONLY_MODE:
        logger.info(
            "[SenseCAP] (text-only) Would open serial: %s @ %d baud — not connecting.",
            SENSECAP_SERIAL_PORT,
            SENSECAP_BAUD_RATE,
        )
        return True
    try:
        _serial = serial.Serial(
            port=SENSECAP_SERIAL_PORT,
            baudrate=SENSECAP_BAUD_RATE,
            timeout=1,
        )
        logger.info("SenseCAP connected on %s @ %d baud", SENSECAP_SERIAL_PORT, SENSECAP_BAUD_RATE)
        return True
    except serial.SerialException as exc:
        logger.warning("SenseCAP not connected (%s) — display output disabled (EC-012)", exc)
        _serial = None
        return False


def _send(command: str) -> None:
    """Send a command line to SenseCAP. Thread-safe. Silent on failure."""
    if TEXT_ONLY_MODE:
        logger.info("[SenseCAP] (text-only) %s", command)
        return
    if _serial is None or not _serial.is_open:
        return
    try:
        with _lock:
            _serial.write((command + "\n").encode("utf-8"))
    except Exception as exc:
        logger.debug("SenseCAP write failed: %s", exc)


def set_ready() -> None:
    """Show startup ready state — green background."""
    _send("STATUS:ScamShield Ready")
    _send("TEXT:Monitoring for scam calls...")


def set_listening() -> None:
    """Show listening/transcribing state."""
    _send("STATUS:Listening...")
    _send("TEXT:Analyzing call audio")


def set_scam_detected(transcript: str = "") -> None:
    """Show scam detected state — red alert."""
    _send("STATUS:!!! SCAM DETECTED !!!")
    short_transcript = transcript[:80] + ("..." if len(transcript) > 80 else "")
    _send(f"TEXT:{short_transcript}")


def set_safe() -> None:
    """Return to safe/idle state."""
    _send("STATUS:Call seems safe")
    _send("TEXT:Continuing to monitor...")


def set_transcript(text: str) -> None:
    """Update the body text with live transcript."""
    short = text[:100] + ("..." if len(text) > 100 else "")
    _send(f"TEXT:{short}")


def disconnect() -> None:
    global _serial
    if TEXT_ONLY_MODE:
        logger.info("[SenseCAP] (text-only) disconnect — no serial open.")
        _serial = None
        return
    if _serial and _serial.is_open:
        _serial.close()
    _serial = None

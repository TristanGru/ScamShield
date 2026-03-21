"""
alert.py — Alert pipeline for ScamShield.

fire_alert(trigger_type, score, keywords, transcript) executes concurrently:
  1. Google Nest: play ElevenLabs warning.mp3 via pychromecast
  2. Grove LED: turn red
  3. Grove Buzzer: sound for 2 seconds
  4. Twilio: send SMS to family member (with debounce)
  5. SQLite: write event record
  6. SenseCAP: update display

After LED_RESET_SECONDS, LED returns to green (BL-008, FR-020).

All external calls are individually try/except — one failure never blocks others.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    TWILIO_TO_NUMBER,
    SMS_DEBOUNCE_SECONDS,
    LED_RESET_SECONDS,
    WARNING_AUDIO_PATH,
)
import db
import hardware
import sensecap

# Re-export for tests and callers that patch LED helpers
set_led_red = hardware.set_led_red
set_led_green = hardware.set_led_green
sound_buzzer = hardware.sound_buzzer

logger = logging.getLogger(__name__)

# Metrics
_alerts_fired = 0
_sms_sent_count = 0

# SMS debounce tracking (BL-004)
_last_sms_time: Optional[float] = None
_sms_lock = threading.Lock()

# Nest reference (set by startup.py)
_nest_cast = None
_nest_connected = False


def set_nest_cast(cast_device) -> None:
    """Called by startup.py after Nest discovery."""
    global _nest_cast, _nest_connected
    _nest_cast = cast_device
    _nest_connected = cast_device is not None


# ── Alert actions (each runs in its own thread) ───────────────────────────────

def _play_nest_warning() -> None:
    """Play pre-cached ElevenLabs warning.mp3 on Google Nest via pychromecast."""
    if _nest_cast is None:
        logger.warning("Nest not connected — skipping Nest audio (EC-002)")
        return
    try:
        import pychromecast
        mc = _nest_cast.media_controller
        mc.play_media(f"file://{WARNING_AUDIO_PATH}", "audio/mp3")
        mc.block_until_active(timeout=5)
        logger.info("Nest: playing warning audio")
    except Exception as exc:
        logger.error("Nest audio playback failed: %s", exc)


def _led_and_buzzer() -> None:
    set_led_red()
    sound_buzzer(duration=2.0)


def _send_sms(keywords: list[str], trigger_type: str, transcript: str) -> bool:
    """Send Twilio SMS with debounce (BL-004). Returns True if sent."""
    global _last_sms_time, _sms_sent_count

    with _sms_lock:
        now = time.time()
        if _last_sms_time and (now - _last_sms_time) < SMS_DEBOUNCE_SECONDS:
            remaining = SMS_DEBOUNCE_SECONDS - (now - _last_sms_time)
            logger.info("SMS debounced — %.0fs remaining", remaining)
            return False
        _last_sms_time = now

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        keywords_str = ", ".join(keywords) if keywords else "none"
        trigger_label = "Manually flagged by user" if trigger_type == "manual" else "Auto-detected"

        body = (
            f"🚨 ScamShield Alert\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Trigger: {trigger_label}\n"
            f"Keywords: {keywords_str}\n"
            f"Preview: {transcript[:100]}..."
            if transcript else ""
        )

        client.messages.create(
            body=body,
            from_=TWILIO_FROM_NUMBER,
            to=TWILIO_TO_NUMBER,
        )
        _sms_sent_count += 1
        logger.info("SMS sent to %s", TWILIO_TO_NUMBER)
        return True

    except Exception as exc:
        logger.error("Twilio SMS failed: %s — retrying once", exc)
        try:
            time.sleep(5)
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(body=body, from_=TWILIO_FROM_NUMBER, to=TWILIO_TO_NUMBER)
            _sms_sent_count += 1
            return True
        except Exception as retry_exc:
            logger.error("Twilio SMS retry failed: %s", retry_exc)
            return False


def _reset_led_after_delay() -> None:
    """Return LED to green after LED_RESET_SECONDS (FR-020)."""
    time.sleep(LED_RESET_SECONDS)
    set_led_green()
    sensecap.set_safe()


# ── Main entry point ──────────────────────────────────────────────────────────

def fire_alert(
    trigger_type: str,
    score: Optional[int],
    keywords: list[str],
    transcript: str,
) -> None:
    """
    Execute the full alert pipeline concurrently.
    trigger_type: 'auto' | 'manual'
    """
    global _alerts_fired
    _alerts_fired += 1

    logger.info(
        "ALERT FIRED trigger=%s score=%s keywords=%s",
        trigger_type,
        score,
        keywords,
    )

    # Update SenseCAP immediately (synchronous — fast serial write)
    sensecap.set_scam_detected(transcript)

    # Run all alert actions concurrently
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="alert") as executor:
        nest_future = executor.submit(_play_nest_warning)
        led_future = executor.submit(_led_and_buzzer)
        sms_future = executor.submit(_send_sms, keywords, trigger_type, transcript)
        db_future = executor.submit(
            db.write_event,
            trigger_type,
            score,
            keywords,
            transcript,
            False,  # sms_sent updated below
        )

        # Wait for DB write to get event_id
        event_id = db_future.result(timeout=5)
        sms_sent = sms_future.result(timeout=10)

        # Update SMS status if it was sent
        if sms_sent and event_id:
            try:
                import sqlite3
                from config import SQLITE_DB_PATH
                with sqlite3.connect(SQLITE_DB_PATH) as conn:
                    conn.execute(
                        "UPDATE events SET sms_sent = 1 WHERE id = ?", (event_id,)
                    )
            except Exception as exc:
                logger.error("Failed to update sms_sent flag: %s", exc)

    # Schedule LED reset in background (non-blocking)
    threading.Thread(target=_reset_led_after_delay, daemon=True).start()


def get_metrics() -> dict:
    return {
        "alerts_fired": _alerts_fired,
        "sms_sent": _sms_sent_count,
    }


def cleanup_gpio() -> None:
    """Call on shutdown to clean up GPIO state."""
    hardware.cleanup_gpio()

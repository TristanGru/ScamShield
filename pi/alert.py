"""
alert.py — Alert pipeline for ScamShield.

fire_alert(...) executes concurrently:
  1. Google Nest: Gemini-written script (optional) → ElevenLabs MP3 → Chromecast stream
  2. Grove LED: turn red
  3. Grove Buzzer: sound for 2 seconds
  4. Twilio: send SMS to family member (with debounce)
  5. SQLite: write event record
  6. SenseCAP: update display

After LED_RESET_SECONDS, LED returns to green (BL-008, FR-020).

All external calls are individually try/except — one failure never blocks others.
"""

import logging
import os
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
    TEXT_ONLY_MODE,
    SKIP_SMS,
    SKIP_BUZZER,
    DYNAMIC_NEST_VOICE,
    NEST_WARNING_TEXT,
    WARNING_AUDIO_PATH,
    PI_LAN_IP,
    PI_API_PORT,
    ALERT_COOLDOWN_SECONDS,
)
import db
import detection
import hardware
import sensecap
from elevenlabs_tts import gtts_write_mp3, synthesize_elevenlabs_mp3

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

# Alert cooldown state — prevents repeat Nest/buzzer/SMS during an active scam call.
_alert_lock = threading.Lock()
_alert_active: bool = False
_last_alert_time: float = 0.0

# Nest reference (set by startup.py)
_nest_cast = None
_nest_connected = False


def set_nest_cast(cast_device) -> None:
    """Called by startup.py after Nest discovery."""
    global _nest_cast, _nest_connected
    _nest_cast = cast_device
    _nest_connected = cast_device is not None


def is_alert_active() -> bool:
    """True while the system is in an active-warning state (cooldown not yet cleared)."""
    with _alert_lock:
        return _alert_active


def clear_alert() -> None:
    """Reset alert state — called by button press or external API."""
    global _alert_active
    with _alert_lock:
        _alert_active = False
    set_led_green()
    sensecap.set_safe()
    logger.info("Alert cleared — LED green, SenseCAP safe")


# ── Alert actions (each runs in its own thread) ───────────────────────────────

def _play_nest_warning(
    conversation_context: str = "",
    reason: str = "none",
    score: Optional[int] = None,
    trigger_type: str = "auto",
) -> None:
    """Gemini script (optional) + ElevenLabs or gTTS, then stream warning.mp3 to Nest."""
    if TEXT_ONLY_MODE:
        mode = "dynamic Gemini + ElevenLabs" if DYNAMIC_NEST_VOICE else "static NEST_WARNING_TEXT"
        logger.info(
            "[Google Nest] (text-only) Would stream http://%s:%d/warning.mp3 (%s)",
            PI_LAN_IP,
            PI_API_PORT,
            mode,
        )
        return
    if _nest_cast is None:
        logger.warning("Nest not connected — skipping Nest audio (EC-002)")
        return

    if DYNAMIC_NEST_VOICE:
        script = detection.generate_nest_voice_script(
            conversation_context, score, reason, trigger_type,
        )
    else:
        script = NEST_WARNING_TEXT.strip()

    skip_el = os.getenv("ELEVENLABS_SKIP_WARNING", "").lower() in ("1", "true", "yes")
    if skip_el:
        logger.info("ELEVENLABS_SKIP_WARNING=1 — gTTS for this alert")
        if not gtts_write_mp3(script, WARNING_AUDIO_PATH):
            return
    else:
        if not synthesize_elevenlabs_mp3(script, WARNING_AUDIO_PATH):
            logger.warning("ElevenLabs failed for alert — gTTS fallback")
            if not gtts_write_mp3(script, WARNING_AUDIO_PATH):
                return

    # Chromecast aggressively caches media by URL; dynamic alerts reuse the same path.
    # Without a unique query param, Nest may replay the startup clip (stale MP3 on disk).
    audio_url = (
        f"http://{PI_LAN_IP}:{PI_API_PORT}/warning.mp3?v={time.time_ns()}"
    )
    try:
        mc = _nest_cast.media_controller
        mc.play_media(audio_url, "audio/mpeg")
        mc.block_until_active(timeout=15)
        logger.info("Nest: streaming %s", audio_url)
    except Exception as exc:
        logger.error("Nest audio playback failed: %s", exc)


def _led_and_buzzer() -> None:
    set_led_red()
    if SKIP_BUZZER:
        logger.info("[Buzzer] SCAMSHIELD_SKIP_BUZZER=1 — skipping Grove buzzer")
        return
    sound_buzzer(duration=2.0)


def _send_sms(keywords: list[str], trigger_type: str, transcript: str) -> bool:
    """Send Twilio SMS with debounce (BL-004). Returns True if sent."""
    global _last_sms_time, _sms_sent_count

    if SKIP_SMS:
        logger.info("[SMS] SCAMSHIELD_SKIP_SMS=1 — skipping Twilio (trigger=%s)", trigger_type)
        return False

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
    """Return LED to green after LED_RESET_SECONDS (FR-020).

    If the alert is still active (user hasn't pressed button / no cooldown
    expiry), keep LED red — it will be cleared by clear_alert() instead.
    """
    time.sleep(LED_RESET_SECONDS)
    with _alert_lock:
        if _alert_active:
            logger.debug("LED reset skipped — alert still active")
            return
    set_led_green()
    sensecap.set_safe()


# ── Main entry point ──────────────────────────────────────────────────────────

def fire_alert(
    trigger_type: str,
    score: Optional[int],
    keywords: list[str],
    transcript: str,
    conversation_context: str = "",
    reason: str = "none",
) -> None:
    """
    Execute the full alert pipeline concurrently.
    trigger_type: 'auto' | 'manual'

    conversation_context: rolling transcript (--- joined) for Gemini Nest script.
    reason: analyst reason from detection (or "manual").

    During cooldown (ALERT_COOLDOWN_SECONDS after the last full alert), only
    the DB write executes — Nest/buzzer/SMS/LED are suppressed.
    """
    global _alerts_fired, _alert_active, _last_alert_time
    _alerts_fired += 1

    with _alert_lock:
        now = time.time()
        suppressed = (
            _alert_active
            and (now - _last_alert_time) < ALERT_COOLDOWN_SECONDS
        )
        if not suppressed:
            _alert_active = True
            _last_alert_time = now

    if suppressed:
        logger.info(
            "Alert suppressed (cooldown %ds) — DB write only  trigger=%s score=%s",
            ALERT_COOLDOWN_SECONDS, trigger_type, score,
        )
        db.write_event(trigger_type, score, keywords, transcript, False)
        return

    logger.info(
        "ALERT FIRED trigger=%s score=%s keywords=%s",
        trigger_type,
        score,
        keywords,
    )

    if TEXT_ONLY_MODE:
        keywords_str = ", ".join(keywords) if keywords else "(none)"
        score_str = str(score) if score is not None else "(n/a)"
        msg = (
            f"\n{'═' * 52}\n"
            f"  SCAMSHIELD — ALERT (text-only mode)\n"
            f"{'═' * 52}\n"
            f"  Trigger:      {trigger_type}\n"
            f"  Scam score:   {score_str}\n"
            f"  Keywords:     {keywords_str}\n"
            f"  Transcript:   {transcript[:400]}{'…' if len(transcript) > 400 else ''}\n"
            f"{'─' * 52}\n"
            f"  [Nest audio] Dynamic script + ElevenLabs if SCAM_DYNAMIC_NEST_VOICE=1.\n"
            f"  [Google Nest] Would stream: http://{PI_LAN_IP}:{PI_API_PORT}/warning.mp3\n"
            f"  [SenseCAP] Would show STATUS: !!! SCAM DETECTED !!! + transcript line.\n"
            f"{'═' * 52}\n"
        )
        print(msg, flush=True)

    # Update SenseCAP immediately (synchronous — fast serial write)
    sensecap.set_scam_detected(transcript)

    # Run all alert actions concurrently
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="alert") as executor:
        nest_future = executor.submit(
            _play_nest_warning,
            conversation_context,
            reason,
            score,
            trigger_type,
        )
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
        try:
            led_future.result(timeout=5)
        except Exception as exc:
            logger.error("LED/buzzer failed: %s", exc)
        try:
            nest_future.result(timeout=120)
        except Exception as exc:
            logger.error("Nest playback failed: %s", exc)

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

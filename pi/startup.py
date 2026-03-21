"""
startup.py — Pi startup sequence.

run_startup() is called once at boot before the main audio loop:
  1. Generate ElevenLabs warning audio → warning.mp3 (cached, D-004)
  2. Discover Google Nest on local network via pychromecast
  3. Start ngrok tunnel → store public URL in Postgres config table
  4. Update FastAPI server status flags
"""

import logging
import os
import time

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    NGROK_AUTHTOKEN,
    TEXT_ONLY_MODE,
    WARNING_AUDIO_PATH,
)
import db
import sensecap

logger = logging.getLogger(__name__)

WARNING_TEXT = (
    "Warning! This may be a scam. "
    "Do not share personal info or send money. "
    "Stay safe and hang up if unsure."
)


def _generate_warning_audio() -> bool:
    """
    Generate ElevenLabs TTS warning.mp3 and cache it locally.
    Returns True if successful. Falls back to Nest native TTS on failure (BL-005, EC-011).
    """
    if TEXT_ONLY_MODE:
        logger.info(
            "[ElevenLabs] (text-only) Would synthesize MP3 → %s\n"
            "Voice ID from env | model eleven_multilingual_v2\n"
            "Script:\n%s",
            WARNING_AUDIO_PATH,
            WARNING_TEXT,
        )
        return False

    if os.getenv("ELEVENLABS_SKIP_WARNING", "").lower() in ("1", "true", "yes"):
        logger.warning(
            "ELEVENLABS_SKIP_WARNING set — skipping ElevenLabs (no warning.mp3; use Nest fallback)"
        )
        return False

    if os.path.exists(WARNING_AUDIO_PATH):
        logger.info("warning.mp3 already cached — skipping generation")
        return True

    logger.info("Generating ElevenLabs warning audio…")
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.play import save

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.text_to_speech.convert(
            text=WARNING_TEXT,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        save(audio, WARNING_AUDIO_PATH)
        logger.info("warning.mp3 saved to %s", WARNING_AUDIO_PATH)
        return True

    except Exception as exc:
        err_s = str(exc).lower()
        if "402" in str(exc) or "payment_required" in err_s or "paid_plan" in err_s:
            logger.error(
                "ElevenLabs blocked (plan/voice) — set ELEVENLABS_SKIP_WARNING=1 or change "
                "ELEVENLABS_VOICE_ID; Nest will use fallback. Details: %s",
                exc,
            )
            return False
        logger.error("ElevenLabs generation failed: %s — retrying once (EC-011)", exc)
        time.sleep(5)
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs.play import save

            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio = client.text_to_speech.convert(
                text=WARNING_TEXT,
                voice_id=ELEVENLABS_VOICE_ID,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            save(audio, WARNING_AUDIO_PATH)
            logger.info("warning.mp3 saved (retry succeeded)")
            return True
        except Exception as retry_exc:
            logger.error("ElevenLabs retry failed: %s — Nest will use native TTS fallback", retry_exc)
            return False


def _discover_nest():
    """
    Discover the first Google Nest/Chromecast on the local network.
    Returns cast device or None (EC-002).
    """
    if TEXT_ONLY_MODE:
        logger.info(
            "[Google Nest] (text-only) mDNS / Chromecast discovery skipped.\n"
            "On each alert, would cast: file://%s (ElevenLabs MP3 or fallback).",
            WARNING_AUDIO_PATH,
        )
        return None

    if os.getenv("SKIP_NEST_DISCOVERY", "").lower() in ("1", "true", "yes"):
        logger.warning(
            "SKIP_NEST_DISCOVERY set — Nest/Chromecast disabled "
            "(set NEST_IP + fix zeroconf, or remove this flag to enable)"
        )
        return None

    import pychromecast

    nest_ip = os.getenv("NEST_IP")

    # Prefer direct IP when set — fewer zeroconf/mDNS edge cases on some networks (RPi)
    if nest_ip:
        logger.info("Discovering Nest via NEST_IP=%s …", nest_ip)
        browser2 = None
        try:
            chromecasts_by_ip, browser2 = pychromecast.get_listed_chromecasts(
                friendly_names=None, uuids=None, known_hosts=[nest_ip]
            )
            if browser2 is not None:
                browser2.stop_discovery()
            if chromecasts_by_ip:
                cast = chromecasts_by_ip[0]
                try:
                    cast.wait()
                except Exception as wait_exc:
                    logger.error("Nest cast.wait() failed: %s", wait_exc)
                    return None
                logger.info("Nest found: %s (model: %s)", cast.name, cast.model_name)
                return cast
        except Exception as exc:
            logger.error("Nest discovery via NEST_IP failed: %s", exc)
        logger.warning("NEST_IP set but no cast at that host — trying mDNS discovery")

    logger.info("Discovering Google Nest via pychromecast (mDNS)…")
    browser = None
    try:
        chromecasts, browser = pychromecast.get_chromecasts(timeout=10)
        if browser is not None:
            browser.stop_discovery()

        if not chromecasts:
            logger.warning("No Chromecast/Nest devices found on network (EC-002)")
            return None

        cast = chromecasts[0]
        try:
            cast.wait()
        except Exception as wait_exc:
            logger.error("Nest cast.wait() failed: %s", wait_exc)
            return None
        logger.info("Nest found: %s (model: %s)", cast.name, cast.model_name)
        return cast

    except Exception as exc:
        logger.error("Nest discovery error: %s", exc)
        if browser is not None:
            try:
                browser.stop_discovery()
            except Exception:
                pass
        return None


def _start_ngrok() -> str:
    """Start ngrok tunnel and return the public HTTPS URL."""
    if not NGROK_AUTHTOKEN:
        logger.warning("NGROK_AUTHTOKEN not set — skipping tunnel")
        return ""
    try:
        from pyngrok import ngrok
        ngrok.set_auth_token(NGROK_AUTHTOKEN)
        tunnel = ngrok.connect(8000, "http")
        url = tunnel.public_url
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)
        logger.info("ngrok tunnel started: %s", url)
        return url
    except Exception as exc:
        logger.error("ngrok failed: %s — dashboard will be LAN-only", exc)
        return ""


def run_startup() -> dict:
    """
    Run the full startup sequence.
    Returns a dict with: nest_connected, warning_audio_ok, ngrok_url
    """
    logger.info("=== ScamShield Startup ===")
    if TEXT_ONLY_MODE:
        logger.warning(
            "SCAMSHIELD_TEXT_ONLY=1 — ElevenLabs, Nest, and SenseCAP hardware are OFF; "
            "see log lines tagged [ElevenLabs], [Google Nest], [SenseCAP]."
        )
    sensecap.connect()
    sensecap.set_ready()

    # 1. DB init
    db.init_db()

    # 2. ElevenLabs warning audio
    warning_ok = _generate_warning_audio()

    # 3. Nest discovery
    nest = _discover_nest()
    nest_connected = nest is not None

    # 4. Register Nest with alert module
    import alert as alert_module
    alert_module.set_nest_cast(nest)

    # 5. ngrok
    ngrok_url = _start_ngrok()
    if ngrok_url:
        db.set_config("ngrok_url", ngrok_url)
        db.set_config("startup_time", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    # 6. Update server status
    import server as server_module
    server_module.set_nest_connected(nest_connected)

    logger.info(
        "Startup complete — nest=%s warning_audio=%s ngrok=%s",
        nest_connected,
        warning_ok,
        bool(ngrok_url),
    )

    if warning_ok:
        sensecap.set_ready()

    return {
        "nest_connected": nest_connected,
        "warning_audio_ok": warning_ok,
        "ngrok_url": ngrok_url,
    }

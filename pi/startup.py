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
    WARNING_AUDIO_PATH,
)
import db
import sensecap

logger = logging.getLogger(__name__)

WARNING_TEXT = (
    "Warning! This may be a scam call. "
    "Please do not give out any personal information, "
    "gift cards, or money. Stay safe and hang up if unsure."
)


def _generate_warning_audio() -> bool:
    """
    Generate ElevenLabs TTS warning.mp3 and cache it locally.
    Returns True if successful. Falls back to Nest native TTS on failure (BL-005, EC-011).
    """
    if os.path.exists(WARNING_AUDIO_PATH):
        logger.info("warning.mp3 already cached — skipping generation")
        return True

    logger.info("Generating ElevenLabs warning audio…")
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import save

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.generate(
            text=WARNING_TEXT,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_monolingual_v1",
        )
        save(audio, WARNING_AUDIO_PATH)
        logger.info("warning.mp3 saved to %s", WARNING_AUDIO_PATH)
        return True

    except Exception as exc:
        logger.error("ElevenLabs generation failed: %s — retrying once (EC-011)", exc)
        time.sleep(5)
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import save

            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio = client.generate(
                text=WARNING_TEXT,
                voice=ELEVENLABS_VOICE_ID,
                model="eleven_monolingual_v1",
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
    logger.info("Discovering Google Nest via pychromecast…")
    try:
        import pychromecast
        chromecasts, browser = pychromecast.get_chromecasts(timeout=10)
        browser.stop_discovery()

        if not chromecasts:
            logger.warning("No Chromecast/Nest devices found on network (EC-002)")
            return None

        cast = chromecasts[0]

        # Check if we have a hardcoded IP (OQ-003 — mDNS may be blocked on hackathon WiFi)
        import os
        nest_ip = os.getenv("NEST_IP")
        if nest_ip:
            logger.info("Using hardcoded NEST_IP=%s", nest_ip)
            chromecasts_by_ip, browser2 = pychromecast.get_listed_chromecasts(
                friendly_names=None, uuids=None, known_hosts=[nest_ip]
            )
            browser2.stop_discovery()
            if chromecasts_by_ip:
                cast = chromecasts_by_ip[0]

        cast.wait()
        logger.info("Nest found: %s (model: %s)", cast.name, cast.model_name)
        return cast

    except Exception as exc:
        logger.error("Nest discovery error: %s", exc)
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

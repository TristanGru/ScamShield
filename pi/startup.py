"""
startup.py — Pi startup sequence.

run_startup() is called once at boot before the main audio loop:
  1. Generate ElevenLabs warning audio → warning.mp3 (cached, D-004)
  2. Discover Google Nest on local network via pychromecast
  3. Start ngrok tunnel → store public URL in Postgres config table
  4. Update FastAPI server status flags
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from elevenlabs_tts import gtts_write_mp3, mask_voice_id, synthesize_elevenlabs_mp3

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_DEFAULT_VOICE_ID,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_OUTPUT_FORMAT,
    ELEVENLABS_WARNING_VOICE_ID,
    NEST_WARNING_TEXT,
    NGROK_AUTHTOKEN,
    TEXT_ONLY_MODE,
    WARNING_AUDIO_META_PATH,
    WARNING_AUDIO_PATH,
)
import db
import sensecap

logger = logging.getLogger(__name__)


def _read_warning_meta() -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(WARNING_AUDIO_META_PATH):
            return None
        with open(WARNING_AUDIO_META_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_warning_meta() -> None:
    payload = {
        "voice_id": ELEVENLABS_WARNING_VOICE_ID,
        "model_id": ELEVENLABS_MODEL_ID,
        "output_format": ELEVENLABS_OUTPUT_FORMAT,
    }
    with open(WARNING_AUDIO_META_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=0)


def _invalidate_warning_cache(reason: str) -> None:
    for path in (WARNING_AUDIO_PATH, WARNING_AUDIO_META_PATH):
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info("Removed %s (%s)", path, reason)
        except OSError as exc:
            logger.warning("Could not remove %s: %s", path, exc)


def _cache_matches_env() -> bool:
    if not os.path.exists(WARNING_AUDIO_PATH):
        return False
    meta = _read_warning_meta()
    if not meta:
        return False
    return (
        meta.get("voice_id") == ELEVENLABS_WARNING_VOICE_ID
        and meta.get("model_id") == ELEVENLABS_MODEL_ID
        and meta.get("output_format") == ELEVENLABS_OUTPUT_FORMAT
    )


def _gtts_fallback() -> bool:
    """gTTS when ElevenLabs is skipped or failed (bootstrap default warning.mp3)."""
    logger.warning(
        "Using gTTS for warning.mp3 — NOT ElevenLabs voice. "
        "Fix API key/plan or remove ELEVENLABS_SKIP_WARNING."
    )
    return gtts_write_mp3(NEST_WARNING_TEXT, WARNING_AUDIO_PATH)


def _generate_warning_audio() -> bool:
    """
    Generate default ElevenLabs TTS warning.mp3 at startup (cached).
    Alerts may overwrite this file with a dynamic Gemini script + ElevenLabs.
    """
    if TEXT_ONLY_MODE:
        logger.info(
            "[ElevenLabs] (text-only) Would synthesize MP3 → %s\n"
            "voice=%s model=%s\nScript:\n%s",
            WARNING_AUDIO_PATH,
            mask_voice_id(ELEVENLABS_WARNING_VOICE_ID),
            ELEVENLABS_MODEL_ID,
            NEST_WARNING_TEXT,
        )
        return False

    if os.getenv("ELEVENLABS_SKIP_WARNING", "").lower() in ("1", "true", "yes"):
        _invalidate_warning_cache("ELEVENLABS_SKIP_WARNING")
        logger.warning("ELEVENLABS_SKIP_WARNING set — using gTTS (not ElevenLabs voice)")
        return _gtts_fallback()

    if os.getenv("ELEVENLABS_REGENERATE_WARNING", "").lower() in ("1", "true", "yes"):
        _invalidate_warning_cache("ELEVENLABS_REGENERATE_WARNING=1")

    if os.path.exists(WARNING_AUDIO_PATH) and _cache_matches_env():
        logger.info(
            "warning.mp3 cache OK — voice=%s model=%s (delete file or set "
            "ELEVENLABS_REGENERATE_WARNING=1 to rebuild)",
            mask_voice_id(ELEVENLABS_WARNING_VOICE_ID),
            ELEVENLABS_MODEL_ID,
        )
        return True

    if os.path.exists(WARNING_AUDIO_PATH) and not _cache_matches_env():
        _invalidate_warning_cache("voice_id/model_id/output_format changed in .env")

    if not os.getenv("ELEVENLABS_VOICE_ID", "").strip() and not os.getenv(
        "ELEVENLABS_WARNING_VOICE_ID", ""
    ).strip():
        logger.info(
            "ElevenLabs voice env unset — using default premade Adam male (%s), free-tier API friendly",
            mask_voice_id(ELEVENLABS_DEFAULT_VOICE_ID),
        )

    logger.info(
        "Generating ElevenLabs warning audio (voice=%s model=%s)…",
        mask_voice_id(ELEVENLABS_WARNING_VOICE_ID),
        ELEVENLABS_MODEL_ID,
    )

    if synthesize_elevenlabs_mp3(NEST_WARNING_TEXT, WARNING_AUDIO_PATH):
        return True
    logger.error("ElevenLabs bootstrap failed — gTTS fallback")
    return _gtts_fallback()


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
    from pychromecast import CastBrowser, SimpleCastListener
    import zeroconf as zc

    nest_ip = os.getenv("NEST_IP")
    DISCOVERY_TIMEOUT = 15

    def _cast_label(cast) -> str:
        if getattr(cast, "name", None):
            return cast.name
        ci = getattr(cast, "cast_info", None)
        if ci is not None and getattr(ci, "friendly_name", None):
            return ci.friendly_name
        return getattr(cast, "host", None) or "Chromecast"

    def _try_connect(cast):
        """Wait for the cast socket to connect; return cast or None."""
        try:
            cast.wait(timeout=10)
            logger.info(
                "Nest found: %s (model: %s)",
                _cast_label(cast),
                cast.model_name or "?",
            )
            return cast
        except Exception as exc:
            logger.error("Nest cast.wait() failed: %s", exc)
            return None

    # --- Direct IP (preferred when NEST_IP is set) ---
    if nest_ip:
        logger.info("Connecting to Nest at NEST_IP=%s …", nest_ip)
        try:
            cast = pychromecast.get_chromecast_from_host(
                (nest_ip, 8009, None, None, None)
            )
            result = _try_connect(cast)
            if result:
                return result
        except Exception as exc:
            logger.warning("NEST_IP direct connect failed: %s — trying mDNS", exc)

    # --- mDNS discovery via CastBrowser (replaces deprecated get_chromecasts) ---
    logger.info("Discovering Google Nest via mDNS…")
    zconf = None
    browser = None
    try:
        zconf = zc.Zeroconf()
        listener = SimpleCastListener()
        browser = CastBrowser(listener, zconf)
        browser.start_discovery()
        time.sleep(DISCOVERY_TIMEOUT)
        browser.stop_discovery()

        services = listener.services
        if not services:
            logger.warning("No Chromecast/Nest devices found on network (EC-002)")
            return None

        service = list(services.values())[0]
        cast = pychromecast.get_chromecast_from_cast_info(service, zconf)
        return _try_connect(cast)

    except Exception as exc:
        logger.error("Nest mDNS discovery error: %s", exc)
        return None
    finally:
        if browser:
            try:
                browser.stop_discovery()
            except Exception:
                pass
        if zconf:
            try:
                zconf.close()
            except Exception:
                pass


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

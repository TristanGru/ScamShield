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
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_DEFAULT_VOICE_ID,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_OUTPUT_FORMAT,
    ELEVENLABS_WARNING_VOICE_ID,
    NGROK_AUTHTOKEN,
    TEXT_ONLY_MODE,
    WARNING_AUDIO_META_PATH,
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


def _mask_voice_id(voice_id: str) -> str:
    if len(voice_id) <= 8:
        return "****"
    return f"{voice_id[:4]}…{voice_id[-4:]}"


def _elevenlabs_api_error_message(response_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse ElevenLabs JSON error body; return (human message, error code)."""
    try:
        data = json.loads(response_text)
        detail = data.get("detail")
        if isinstance(detail, dict):
            return detail.get("message"), detail.get("code")
        if isinstance(detail, str):
            return detail, None
    except Exception:
        pass
    return None, None


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


def _tts_elevenlabs_rest() -> bool:
    """
    Official REST: POST /v1/text-to-speech/{voice_id} — voice is always in the URL path.
    More reliable than the Python SDK for honoring the chosen voice.
    """
    vid = ELEVENLABS_WARNING_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    params = {"output_format": ELEVENLABS_OUTPUT_FORMAT}
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    body = {"text": WARNING_TEXT, "model_id": ELEVENLABS_MODEL_ID}
    logger.info(
        "ElevenLabs REST TTS — voice=%s model=%s",
        _mask_voice_id(vid),
        ELEVENLABS_MODEL_ID,
    )
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, params=params, json=body, headers=headers)
        r.raise_for_status()
        Path(WARNING_AUDIO_PATH).write_bytes(r.content)
    _write_warning_meta()
    logger.info("warning.mp3 saved via REST API → %s", WARNING_AUDIO_PATH)
    return True


def _tts_elevenlabs_sdk() -> bool:
    """Fallback: Python SDK (some versions mishandle kwargs — REST is preferred)."""
    from elevenlabs.client import ElevenLabs
    from elevenlabs.play import save

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio = client.text_to_speech.convert(
        voice_id=ELEVENLABS_WARNING_VOICE_ID,
        text=WARNING_TEXT,
        model_id=ELEVENLABS_MODEL_ID,
        output_format=ELEVENLABS_OUTPUT_FORMAT,
    )
    save(audio, WARNING_AUDIO_PATH)
    _write_warning_meta()
    logger.info("warning.mp3 saved via Python SDK → %s", WARNING_AUDIO_PATH)
    return True


def _gtts_fallback() -> bool:
    """
    Google Translate TTS — sounds like a generic Google voice, NOT ElevenLabs.
    """
    try:
        from gtts import gTTS

        logger.warning(
            "Using gTTS (Google) for warning.mp3 — this is NOT your ElevenLabs voice. "
            "Fix API key/plan/voice_id or remove ELEVENLABS_SKIP_WARNING."
        )
        tts = gTTS(WARNING_TEXT, lang="en")
        tts.save(WARNING_AUDIO_PATH)
        # No ElevenLabs meta — next boot will try ElevenLabs again if configured
        try:
            if os.path.exists(WARNING_AUDIO_META_PATH):
                os.remove(WARNING_AUDIO_META_PATH)
        except OSError:
            pass
        logger.info("gTTS wrote %s", WARNING_AUDIO_PATH)
        return True
    except Exception as exc:
        logger.error("gTTS fallback failed: %s", exc)
        return False


def _generate_warning_audio() -> bool:
    """
    Generate ElevenLabs TTS warning.mp3 and cache it locally.
    Uses REST API first so the voice_id in your dashboard matches what you hear on Nest.
    """
    if TEXT_ONLY_MODE:
        logger.info(
            "[ElevenLabs] (text-only) Would synthesize MP3 → %s\n"
            "voice=%s model=%s\nScript:\n%s",
            WARNING_AUDIO_PATH,
            _mask_voice_id(ELEVENLABS_WARNING_VOICE_ID),
            ELEVENLABS_MODEL_ID,
            WARNING_TEXT,
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
            _mask_voice_id(ELEVENLABS_WARNING_VOICE_ID),
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
            _mask_voice_id(ELEVENLABS_DEFAULT_VOICE_ID),
        )

    logger.info(
        "Generating ElevenLabs warning audio (voice=%s model=%s)…",
        _mask_voice_id(ELEVENLABS_WARNING_VOICE_ID),
        ELEVENLABS_MODEL_ID,
    )

    try:
        return _tts_elevenlabs_rest()
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        body = exc.response.text or ""
        snippet = body[:500]
        api_msg, api_code = _elevenlabs_api_error_message(body)
        if code == 402:
            logger.error(
                "ElevenLabs 402 — %s [code=%s]. "
                "On the free tier, library / default catalog voices often cannot be used via the API "
                "(paid_plan_required). Options: (1) upgrade ElevenLabs, or (2) set ELEVENLABS_VOICE_ID "
                "to a voice your plan allows in the API (e.g. an Instant Voice Clone you own), then "
                "delete warning.mp3 + warning.mp3.meta or set ELEVENLABS_REGENERATE_WARNING=1. "
                "Falling back to gTTS (Google voice, NOT ElevenLabs). Raw: %s",
                api_msg or "payment required",
                api_code or "?",
                snippet or exc,
            )
            return _gtts_fallback()
        logger.warning(
            "ElevenLabs REST HTTP %s — trying Python SDK. Body: %s",
            code,
            (api_msg or snippet or exc),
        )
        try:
            return _tts_elevenlabs_sdk()
        except Exception as sdk_exc:
            logger.error("ElevenLabs SDK failed: %s — retrying REST after 5s", sdk_exc)
            time.sleep(5)
            try:
                return _tts_elevenlabs_rest()
            except Exception as rest2:
                logger.error(
                    "ElevenLabs still failing after retry (%s) — last-resort gTTS (not ElevenLabs voice)",
                    rest2,
                )
                return _gtts_fallback()
    except Exception as exc:
        err_s = str(exc).lower()
        if "402" in str(exc) or "payment_required" in err_s or "paid_plan" in err_s:
            logger.error(
                "ElevenLabs blocked (plan/voice) — %s. Using gTTS (Google voice, not ElevenLabs).",
                exc,
            )
            return _gtts_fallback()
        logger.warning("ElevenLabs REST failed (%s) — trying Python SDK", exc)
        try:
            return _tts_elevenlabs_sdk()
        except Exception as sdk_exc:
            logger.error("ElevenLabs SDK failed: %s — retrying REST after 5s", sdk_exc)
            time.sleep(5)
            try:
                return _tts_elevenlabs_rest()
            except Exception as rest2:
                logger.error(
                    "ElevenLabs REST retry failed: %s — last-resort gTTS (not ElevenLabs voice)",
                    rest2,
                )
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

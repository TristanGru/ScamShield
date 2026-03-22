"""
elevenlabs_tts.py — ElevenLabs text-to-speech for Nest warning.mp3.

Used at startup (cached default clip) and at alert time (Gemini-written script).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import httpx

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_OUTPUT_FORMAT,
    ELEVENLABS_WARNING_VOICE_ID,
    WARNING_AUDIO_META_PATH,
    WARNING_AUDIO_PATH,
)

logger = logging.getLogger(__name__)


def mask_voice_id(voice_id: str) -> str:
    if len(voice_id) <= 8:
        return "****"
    return f"{voice_id[:4]}…{voice_id[-4:]}"


def _write_warning_meta() -> None:
    payload = {
        "voice_id": ELEVENLABS_WARNING_VOICE_ID,
        "model_id": ELEVENLABS_MODEL_ID,
        "output_format": ELEVENLABS_OUTPUT_FORMAT,
    }
    with open(WARNING_AUDIO_META_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=0)


def _elevenlabs_api_error_message(response_text: str) -> Tuple[Optional[str], Optional[str]]:
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


def synthesize_elevenlabs_mp3(
    text: str,
    output_path: Optional[str] = None,
    *,
    write_meta: bool = True,
) -> bool:
    """
    Synthesize MP3 via ElevenLabs REST (preferred) or Python SDK.
    Returns True on success.
    """
    out = output_path or WARNING_AUDIO_PATH
    text = (text or "").strip()
    if not text:
        logger.error("ElevenLabs: empty text — cannot synthesize")
        return False

    vid = ELEVENLABS_WARNING_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    params = {"output_format": ELEVENLABS_OUTPUT_FORMAT}
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    body = {"text": text, "model_id": ELEVENLABS_MODEL_ID}
    logger.info(
        "ElevenLabs REST TTS — voice=%s model=%s (%d chars)",
        mask_voice_id(vid),
        ELEVENLABS_MODEL_ID,
        len(text),
    )
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(url, params=params, json=body, headers=headers)
            r.raise_for_status()
            Path(out).write_bytes(r.content)
        if write_meta:
            _write_warning_meta()
        logger.info("ElevenLabs MP3 saved → %s", out)
        return True
    except httpx.HTTPStatusError as exc:
        body = exc.response.text or ""
        api_msg, _ = _elevenlabs_api_error_message(body)
        logger.warning(
            "ElevenLabs REST HTTP %s — trying SDK. %s",
            exc.response.status_code,
            api_msg or body[:200],
        )
    except Exception as exc:
        logger.warning("ElevenLabs REST failed (%s) — trying SDK", exc)

    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.play import save

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.text_to_speech.convert(
            voice_id=ELEVENLABS_WARNING_VOICE_ID,
            text=text,
            model_id=ELEVENLABS_MODEL_ID,
            output_format=ELEVENLABS_OUTPUT_FORMAT,
        )
        save(audio, out)
        if write_meta:
            _write_warning_meta()
        logger.info("ElevenLabs MP3 saved via SDK → %s", out)
        return True
    except Exception as exc:
        logger.error("ElevenLabs SDK failed: %s", exc)
        return False


def gtts_write_mp3(text: str, output_path: Optional[str] = None, remove_meta: bool = True) -> bool:
    """Google TTS fallback — not ElevenLabs voice."""
    out = output_path or WARNING_AUDIO_PATH
    try:
        from gtts import gTTS

        logger.warning("Using gTTS for MP3 (not ElevenLabs voice) → %s", out)
        tts = gTTS((text or "").strip() or " ", lang="en")
        tts.save(out)
        if remove_meta:
            try:
                if os.path.exists(WARNING_AUDIO_META_PATH):
                    os.remove(WARNING_AUDIO_META_PATH)
            except OSError:
                pass
        return True
    except Exception as exc:
        logger.error("gTTS failed: %s", exc)
        return False

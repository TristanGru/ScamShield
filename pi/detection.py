"""
detection.py — Scam detection engine.

score_transcript(text) -> (score: int, matched_keywords: list[str])

Two methods run on every transcript chunk:
  1. Gemini 1.5 Flash API — returns scam likelihood score 0–100
  2. Keyword matcher — case-insensitive whole-word matching (BL-002)

If Gemini fails (timeout, error, bad JSON), keyword-only scoring is used.
Alert fires if score >= SCAM_SCORE_THRESHOLD OR matched_keywords >= SCAM_KEYWORD_MIN_MATCHES.
"""

import json
import logging
import re
import time
from typing import Optional

from google import genai

from config import (
    GEMINI_API_KEY,
    SCAM_SCORE_THRESHOLD,
    SCAM_KEYWORD_MIN_MATCHES,
)
from keywords import SCAM_KEYWORDS

logger = logging.getLogger(__name__)

# Metrics counters (read by server.py for /metrics)
_chunks_processed = 0
_gemini_errors = 0

GEMINI_TIMEOUT_SECONDS = 5

_SYSTEM_PROMPT = """You are a scam call detection system protecting elderly phone users.

Analyze the following phone call transcript and return a JSON object with:
- "score": integer 0-100 representing scam likelihood (0=definitely not a scam, 100=definitely a scam)
- "reason": brief string explaining the top red flag, or "none" if not a scam

Scam indicators: impersonating IRS/SSA/Medicare, demanding gift cards/wire transfers/Bitcoin,
threatening arrest or deportation, claiming prizes or refunds, tech support scams,
grandparent scams, urgency/secrecy pressure, requesting remote access.

Respond with ONLY valid JSON. No markdown, no explanation outside the JSON.

Example response: {"score": 85, "reason": "IRS impersonation with gift card demand"}
"""

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _call_gemini(text: str) -> Optional[dict]:
    """Call Gemini API. Returns parsed JSON dict or None on failure."""
    global _gemini_errors
    try:
        client = _get_client()
        prompt = f"{_SYSTEM_PROMPT}\n\nTranscript:\n{text}"

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17",
            contents=prompt,
        )

        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"```(?:json)?\s*", "", raw).strip("` \n")

        parsed = json.loads(raw)

        score = parsed.get("score")
        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            raise ValueError(f"Invalid score value: {score}")

        logger.info("Gemini score=%d reason=%r", int(score), parsed.get("reason", ""))
        return {"score": int(score), "reason": parsed.get("reason", "")}

    except Exception as exc:
        _gemini_errors += 1
        logger.warning("Gemini API failed (%s) — falling back to keyword detection", exc)
        return None


def _keyword_match(text: str) -> list[str]:
    """Return list of matched scam keywords (whole-word, case-insensitive). BL-002."""
    text_lower = text.lower()
    matched = []
    for kw in SCAM_KEYWORDS:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text_lower):
            matched.append(kw)
    return matched


def score_transcript(text: str) -> tuple[int, list[str]]:
    """
    Score a transcript for scam likelihood.
    Returns (score, matched_keywords).
    Score is 0 if text is empty or all detection fails.
    """
    global _chunks_processed
    _chunks_processed += 1

    if not text or not text.strip():
        return 0, []

    matched_keywords = _keyword_match(text)
    keyword_score = min(100, len(matched_keywords) * 30)

    gemini_result = _call_gemini(text)

    if gemini_result is not None:
        final_score = gemini_result["score"]
    else:
        # Fallback: derive score from keywords only (BL-007)
        final_score = keyword_score
        logger.info("Keyword-only score: %d (keywords=%s)", final_score, matched_keywords)

    return final_score, matched_keywords


def should_alert(score: int, keywords: list[str]) -> bool:
    """BL-001: Alert if score >= threshold OR keyword matches >= minimum."""
    return score >= SCAM_SCORE_THRESHOLD or len(keywords) >= SCAM_KEYWORD_MIN_MATCHES


def get_metrics() -> dict:
    return {
        "chunks_processed": _chunks_processed,
        "gemini_errors": _gemini_errors,
    }

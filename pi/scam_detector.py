"""
scam_detector.py — Gemini + keyword scam analysis (PRD Phase 1).

analyze_transcript() returns confidence (0–1), score (0–100), reason, and keywords.
score_transcript() remains (score, keywords) for callers that do not need reason.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import google.generativeai as genai

try:
    from pi.config import (
        GEMINI_API_KEY,
        SCAM_SCORE_THRESHOLD,
        SCAM_KEYWORD_MIN_MATCHES,
    )
    from pi.keywords import SCAM_KEYWORDS
except ImportError:
    from config import (
        GEMINI_API_KEY,
        SCAM_SCORE_THRESHOLD,
        SCAM_KEYWORD_MIN_MATCHES,
    )
    from keywords import SCAM_KEYWORDS

logger = logging.getLogger(__name__)

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


def _init_gemini() -> None:
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass(frozen=True)
class ScamAnalysis:
    """Structured result aligned with PRD (confidence + reason)."""

    score: int  # 0–100
    confidence: float  # 0.0–1.0 (score / 100)
    reason: str
    matched_keywords: list[str]


def _call_gemini(text: str) -> Optional[dict]:
    """Call Gemini API. Returns parsed JSON dict or None on failure."""
    global _gemini_errors
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"{_SYSTEM_PROMPT}\n\nTranscript:\n{text}"

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=100,
            ),
            request_options={"timeout": GEMINI_TIMEOUT_SECONDS},
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"```(?:json)?\s*", "", raw).strip("` \n")

        parsed = json.loads(raw)

        score = parsed.get("score")
        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            raise ValueError(f"Invalid score value: {score}")

        logger.info("Gemini score=%d reason=%r", int(score), parsed.get("reason", ""))
        return {"score": int(score), "reason": str(parsed.get("reason", "") or "")}

    except Exception as exc:
        _gemini_errors += 1
        logger.warning("Gemini API failed (%s) — falling back to keyword detection", exc)
        return None


def _keyword_match(text: str) -> list[str]:
    """Return list of matched scam keywords (whole-word, case-insensitive)."""
    text_lower = text.lower()
    matched = []
    for kw in SCAM_KEYWORDS:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text_lower):
            matched.append(kw)
    return matched


def analyze_transcript(text: str) -> ScamAnalysis:
    """
    Full analysis: Gemini score + reason, with keyword fallback when Gemini fails.
    """
    global _chunks_processed
    _chunks_processed += 1

    if not text or not text.strip():
        return ScamAnalysis(
            score=0,
            confidence=0.0,
            reason="none",
            matched_keywords=[],
        )

    matched_keywords = _keyword_match(text)
    keyword_score = min(100, len(matched_keywords) * 30)

    gemini_result = _call_gemini(text)

    if gemini_result is not None:
        final_score = gemini_result["score"]
        reason = gemini_result.get("reason", "") or "none"
    else:
        final_score = keyword_score
        reason = "keyword_fallback" if matched_keywords else "gemini_unavailable"
        logger.info("Keyword-only score: %d (keywords=%s)", final_score, matched_keywords)

    conf = max(0.0, min(1.0, final_score / 100.0))
    return ScamAnalysis(
        score=final_score,
        confidence=conf,
        reason=reason,
        matched_keywords=matched_keywords,
    )


def score_transcript(text: str) -> tuple[int, list[str]]:
    """Backward-compatible (score 0–100, matched keywords)."""
    a = analyze_transcript(text)
    return a.score, a.matched_keywords


def should_alert(score: int, keywords: list[str]) -> bool:
    """True if score meets PRD threshold or enough keywords match."""
    return score >= SCAM_SCORE_THRESHOLD or len(keywords) >= SCAM_KEYWORD_MIN_MATCHES


def should_alert_analysis(analysis: ScamAnalysis) -> bool:
    """Same as should_alert but takes a ScamAnalysis."""
    return should_alert(analysis.score, analysis.matched_keywords)


def get_metrics() -> dict:
    return {
        "chunks_processed": _chunks_processed,
        "gemini_errors": _gemini_errors,
    }


_init_gemini()

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

from google import genai

try:
    from pi.config import (
        GEMINI_API_KEY,
        GEMINI_MODEL,
        SCAM_SCORE_THRESHOLD,
        SCAM_KEYWORD_MIN_MATCHES,
        SKIP_GEMINI,
    )
    from pi.keywords import SCAM_KEYWORDS
except ImportError:
    from config import (
        GEMINI_API_KEY,
        GEMINI_MODEL,
        SCAM_SCORE_THRESHOLD,
        SCAM_KEYWORD_MIN_MATCHES,
        SKIP_GEMINI,
    )
    from keywords import SCAM_KEYWORDS

logger = logging.getLogger(__name__)

_chunks_processed = 0
_gemini_errors = 0
_client: Optional[genai.Client] = None

GEMINI_TIMEOUT_SECONDS = 5

_SYSTEM_PROMPT = """You are an impartial phone call analyst. Your job is to estimate the probability that an ongoing call is a scam targeting an elderly person.

You will receive a rolling transcript (speech-to-text, segments separated by ---).
IMPORTANT: The transcript comes from an offline speech-to-text engine and often contains mishearings, garbled words, and fragments. Do NOT treat a single suspicious-sounding word as evidence if the surrounding context is innocent or incoherent. Focus on the overall pattern and intent of the conversation.

Return a JSON object with:
- "score": integer 0-100 (0 = certainly legitimate, 100 = certainly a scam)
- "reason": one-sentence explanation, or "none" if score < 30

Scoring guidance:
- 0-20: Normal conversation — greetings, family chat, appointment scheduling, casual topics.
- 21-40: Mildly suspicious wording but no clear scam pattern. Could easily be innocent.
- 41-60: Multiple soft signals (unusual urgency, vague authority claims) but no concrete demand yet.
- 61-80: Clear scam pattern emerging — impersonation + demand for action/payment, but some ambiguity remains.
- 81-100: Unambiguous scam — explicit impersonation of authority AND demand for gift cards, wire transfers, cryptocurrency, remote access, or personal information. Reserve 90+ for cases with multiple confirmed indicators.

Common scam patterns (require BOTH impersonation/pressure AND a concrete demand to score high):
- Government impersonation (IRS, SSA, Medicare) + threatening arrest/deportation
- Tech support ("your computer is infected") + requesting remote access or payment
- Grandparent/family emergency ("grandson in jail") + urgent payment demand
- Prize/lottery ("you've won") + fee required to claim
- Refund/overpayment scam + request to send money back

Things that are NOT scams by themselves — keep score low unless combined with pressure + payment demand:
- Mentioning money, banks, or payments in normal context
- A family member asking for help
- Discussing insurance, medical bills, or government programs
- Sales calls, telemarketing, robocalls (annoying but not fraud)
- Garbled or incoherent transcript fragments

Respond with ONLY valid JSON. No markdown, no explanation outside the JSON.

Examples:
{"score": 12, "reason": "none"}
{"score": 35, "reason": "caller claims to be from Medicare but no demand yet"}
{"score": 82, "reason": "IRS impersonation with gift card payment demand"}
"""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


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
    if SKIP_GEMINI:
        logger.debug("[Gemini] SCAMSHIELD_SKIP_GEMINI=1 — skipping API call")
        return None
    try:
        client = _get_client()
        prompt = f"{_SYSTEM_PROMPT}\n\nTranscript:\n{text}"

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
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


def analyze_transcript(
    text: str,
    current_chunk: Optional[str] = None,
) -> ScamAnalysis:
    """
    Full analysis: Gemini score + reason, with keyword fallback when Gemini fails.

    text:          Full conversation context (rolling buffer joined with ---).
    current_chunk: If provided, keywords are matched against this only (avoids
                   re-matching old chunks). If None, keywords run on `text`.
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

    kw_source = current_chunk if current_chunk is not None else text
    matched_keywords = _keyword_match(kw_source)
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


def score_transcript(
    text: str,
    current_chunk: Optional[str] = None,
) -> tuple[int, list[str]]:
    """Backward-compatible (score 0–100, matched keywords)."""
    a = analyze_transcript(text, current_chunk=current_chunk)
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

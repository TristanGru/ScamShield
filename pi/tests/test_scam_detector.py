"""
test_scam_detector.py — Phase 1 PRD: confidence, reason, and analysis API.
"""

from unittest.mock import MagicMock, patch

import pytest


def test_analyze_transcript_gemini_success():
    from pi import scam_detector as sd

    with patch.object(sd, "_call_gemini", return_value={"score": 80, "reason": "IRS demand"}):
        a = sd.analyze_transcript("The IRS demands gift cards today.")
    assert a.score == 80
    assert abs(a.confidence - 0.8) < 1e-6
    assert a.reason == "IRS demand"
    assert "IRS" in a.matched_keywords


def test_analyze_transcript_empty():
    from pi import scam_detector as sd

    a = sd.analyze_transcript("")
    assert a.score == 0
    assert a.confidence == 0.0
    assert a.matched_keywords == []


def test_should_alert_analysis_matches_should_alert():
    from pi import scam_detector as sd

    high = sd.ScamAnalysis(
        score=80,
        confidence=0.8,
        reason="x",
        matched_keywords=[],
    )
    low = sd.ScamAnalysis(
        score=50,
        confidence=0.5,
        reason="none",
        matched_keywords=["IRS"],
    )
    assert sd.should_alert_analysis(high) is True
    assert sd.should_alert_analysis(low) is False


def test_keyword_minimum_triggers_despite_low_gemini_score():
    """PRD: multiple scam keywords still trigger alert when Gemini under-threshold."""
    from pi import scam_detector as sd

    with patch.object(sd, "_call_gemini", return_value={"score": 10, "reason": "benign"}):
        a = sd.analyze_transcript(
            "The IRS wants gift cards — pay or face arrest immediately."
        )
    assert len(a.matched_keywords) >= 2
    assert sd.should_alert_analysis(a) is True


def test_confidence_is_score_over_100():
    from pi import scam_detector as sd

    with patch.object(sd, "_call_gemini", return_value={"score": 75, "reason": "ok"}):
        a = sd.analyze_transcript("Some transcript with enough text.")
    assert a.confidence == 0.75

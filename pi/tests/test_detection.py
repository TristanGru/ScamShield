"""
test_detection.py — Unit tests for the scam detection engine.
Covers all scoring paths: Gemini success, Gemini failure, keyword-only, no match.
"""

import pytest
from unittest.mock import patch, MagicMock


# ── Keyword matching tests ─────────────────────────────────────────────────────

def test_keyword_match_irs():
    from pi.detection import _keyword_match
    result = _keyword_match("This is the IRS calling about your taxes.")
    assert "IRS" in result


def test_keyword_match_case_insensitive():
    from pi.detection import _keyword_match
    result = _keyword_match("you owe money to the irs right now")
    assert "IRS" in result


def test_keyword_match_no_partial_words():
    """BL-002: 'history' should NOT match 'his'."""
    from pi.detection import _keyword_match
    result = _keyword_match("I have a long history of working hard.")
    assert len(result) == 0


def test_keyword_match_multiple():
    from pi.detection import _keyword_match
    text = "The IRS says you must pay with gift cards or face arrest."
    result = _keyword_match(text)
    assert "IRS" in result
    assert "gift cards" in result
    assert "arrest" in result
    assert len(result) >= 3


def test_keyword_match_empty_text():
    from pi.detection import _keyword_match
    result = _keyword_match("")
    assert result == []


def test_keyword_match_normal_conversation():
    from pi.detection import _keyword_match
    result = _keyword_match("Hi grandma, how are you doing today? The weather is nice.")
    assert len(result) == 0


# ── should_alert logic ────────────────────────────────────────────────────────

def test_should_alert_high_score():
    from pi.detection import should_alert
    assert should_alert(score=75, keywords=[]) is True


def test_should_alert_threshold_exact():
    from pi.detection import should_alert
    assert should_alert(score=70, keywords=[]) is True


def test_should_alert_below_threshold_no_keywords():
    from pi.detection import should_alert
    assert should_alert(score=69, keywords=[]) is False


def test_should_alert_keywords_only():
    from pi.detection import should_alert
    assert should_alert(score=0, keywords=["IRS", "gift cards"]) is True


def test_should_alert_one_keyword_no_score():
    """One keyword alone should NOT trigger if score is below threshold."""
    from pi.detection import should_alert
    assert should_alert(score=0, keywords=["IRS"]) is False


# ── score_transcript — Gemini success ────────────────────────────────────────

def test_score_transcript_gemini_success():
    from pi import detection
    mock_response = MagicMock()
    mock_response.text = '{"score": 87, "reason": "IRS impersonation"}'

    with patch.object(detection, "_call_gemini", return_value={"score": 87, "reason": "IRS impersonation"}):
        score, keywords = detection.score_transcript(
            "This is the IRS. You owe $5,000. Pay with gift cards."
        )
    assert score == 87
    assert "IRS" in keywords
    assert "gift cards" in keywords


# ── score_transcript — Gemini failure fallback ────────────────────────────────

def test_score_transcript_gemini_failure_keyword_fallback():
    from pi import detection
    with patch.object(detection, "_call_gemini", return_value=None):
        score, keywords = detection.score_transcript(
            "The IRS says you must pay with gift cards immediately or face arrest."
        )
    # keyword fallback: 3+ keywords = 90 (capped at 100)
    assert score >= 60
    assert len(keywords) >= 2


def test_score_transcript_gemini_failure_no_keywords():
    from pi import detection
    with patch.object(detection, "_call_gemini", return_value=None):
        score, keywords = detection.score_transcript(
            "How is the weather today? I hope it is sunny."
        )
    assert score == 0
    assert keywords == []


# ── score_transcript — empty input ───────────────────────────────────────────

def test_score_transcript_empty_string():
    from pi import detection
    score, keywords = detection.score_transcript("")
    assert score == 0
    assert keywords == []


def test_score_transcript_whitespace_only():
    from pi import detection
    score, keywords = detection.score_transcript("   \n  ")
    assert score == 0
    assert keywords == []


# ── Gemini JSON parsing ───────────────────────────────────────────────────────

def test_call_gemini_strips_markdown_fences():
    """Gemini sometimes returns ```json ... ``` — we must handle that."""
    from pi import detection
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = '```json\n{"score": 55, "reason": "prize scam"}\n```'

    with patch("pi.detection.genai.GenerativeModel", return_value=mock_model):
        result = detection._call_gemini("You've won a prize! Claim your reward now.")

    assert result is not None
    assert result["score"] == 55


def test_call_gemini_invalid_json_returns_none():
    from pi import detection
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "not json at all"

    with patch("pi.detection.genai.GenerativeModel", return_value=mock_model):
        result = detection._call_gemini("some transcript")

    assert result is None


def test_call_gemini_out_of_range_score_returns_none():
    from pi import detection
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = '{"score": 999, "reason": "test"}'

    with patch("pi.detection.genai.GenerativeModel", return_value=mock_model):
        result = detection._call_gemini("some transcript")

    assert result is None

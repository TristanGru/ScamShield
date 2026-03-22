"""NEST_WARNING_TEXT must stay free of SCAM_KEYWORDS — the Nest can be picked up by the mic."""

import re

from pi.config import NEST_WARNING_TEXT
from pi.keywords import SCAM_KEYWORDS


def test_nest_warning_text_has_no_scam_keyword_matches() -> None:
    """Same whole-word rules as scam_detector._keyword_match."""
    text_lower = NEST_WARNING_TEXT.lower()
    for kw in SCAM_KEYWORDS:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        assert re.search(pattern, text_lower) is None, (
            f"NEST_WARNING_TEXT must not contain keyword {kw!r} (mic feedback)"
        )


def test_nest_warning_text_non_empty() -> None:
    assert len(NEST_WARNING_TEXT.strip()) >= 20

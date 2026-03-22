"""
detection.py — Backward-compatible re-exports for scam_detector (PRD Phase 1).

Prefer importing from pi.scam_detector in new code.
"""

try:
    from .scam_detector import (  # type: ignore
        ScamAnalysis,
        analyze_transcript,
        generate_nest_voice_script,
        get_metrics,
        score_transcript,
        should_alert,
        should_alert_analysis,
        _call_gemini,
        _keyword_match,
    )
except ImportError:
    from scam_detector import (  # type: ignore
        ScamAnalysis,
        analyze_transcript,
        generate_nest_voice_script,
        get_metrics,
        score_transcript,
        should_alert,
        should_alert_analysis,
        _call_gemini,
        _keyword_match,
    )

"""
test_alert.py — Unit tests for alert.py.
All external calls (Nest, GPIO, Twilio, DB, SenseCAP) are mocked.
"""

import time
from unittest.mock import MagicMock, patch, call

import pytest


# ── Helpers ────────────────────────────────────────────────────────────────────

def _reset_alert_module():
    """Reset module-level state between tests."""
    import pi.alert as alert_mod
    alert_mod._last_sms_time = None
    alert_mod._alerts_fired = 0
    alert_mod._sms_sent_count = 0
    alert_mod._nest_cast = None
    alert_mod._nest_connected = False


# ── LED / Buzzer ───────────────────────────────────────────────────────────────

def test_set_led_red_sim(caplog):
    """GPIO unavailable → [SIM] log, no crash."""
    import pi.alert as alert_mod
    import pi.hardware as hw
    original = hw._GPIO_AVAILABLE
    hw._GPIO_AVAILABLE = False
    with caplog.at_level("DEBUG", logger="pi.hardware"):
        alert_mod.set_led_red()
    hw._GPIO_AVAILABLE = original
    assert any("RED" in r.message for r in caplog.records)


def test_set_led_green_sim(caplog):
    import pi.alert as alert_mod
    import pi.hardware as hw
    original = hw._GPIO_AVAILABLE
    hw._GPIO_AVAILABLE = False
    with caplog.at_level("DEBUG", logger="pi.hardware"):
        alert_mod.set_led_green()
    hw._GPIO_AVAILABLE = original
    assert any("GREEN" in r.message for r in caplog.records)


def test_sound_buzzer_sim(caplog):
    import pi.alert as alert_mod
    import pi.hardware as hw
    original = hw._GPIO_AVAILABLE
    hw._GPIO_AVAILABLE = False
    with caplog.at_level("DEBUG", logger="pi.hardware"):
        alert_mod.sound_buzzer(duration=0.01)
    hw._GPIO_AVAILABLE = original
    assert any("BUZZER" in r.message for r in caplog.records)


# ── Nest playback ─────────────────────────────────────────────────────────────

def test_play_nest_warning_no_cast(caplog):
    """No Nest device → logs warning, no crash."""
    import pi.alert as alert_mod
    alert_mod._nest_cast = None
    with caplog.at_level("WARNING", logger="pi.alert"):
        alert_mod._play_nest_warning()
    assert any("EC-002" in r.message for r in caplog.records)


def test_play_nest_warning_with_cast():
    """Nest present → synthesize + media controller called."""
    import pi.alert as alert_mod

    mock_cast = MagicMock()
    mock_mc = MagicMock()
    mock_cast.media_controller = mock_mc
    alert_mod._nest_cast = mock_cast

    with patch("pi.alert.synthesize_elevenlabs_mp3", return_value=True):
        alert_mod._play_nest_warning()

    mock_mc.play_media.assert_called_once()
    mock_mc.block_until_active.assert_called_once()

    alert_mod._nest_cast = None


# ── SMS / debounce ────────────────────────────────────────────────────────────

def test_send_sms_success():
    import pi.alert as alert_mod
    _reset_alert_module()

    mock_client = MagicMock()
    with patch("pi.alert.Client", return_value=mock_client):
        sent = alert_mod._send_sms(["IRS", "gift cards"], "auto", "You owe money to the IRS.")

    assert sent is True
    mock_client.messages.create.assert_called_once()
    assert alert_mod._sms_sent_count == 1


def test_send_sms_debounce():
    """Second SMS within debounce window is suppressed."""
    import pi.alert as alert_mod
    _reset_alert_module()

    mock_client = MagicMock()
    with patch("pi.alert.Client", return_value=mock_client):
        sent1 = alert_mod._send_sms(["IRS"], "auto", "first call")
        sent2 = alert_mod._send_sms(["IRS"], "auto", "second call — debounced")

    assert sent1 is True
    assert sent2 is False
    assert mock_client.messages.create.call_count == 1
    assert alert_mod._sms_sent_count == 1


def test_send_sms_debounce_expires():
    """After debounce window, SMS should send again."""
    import pi.alert as alert_mod
    from pi.config import SMS_DEBOUNCE_SECONDS
    _reset_alert_module()

    # Pretend last SMS was sent slightly more than debounce ago
    alert_mod._last_sms_time = time.time() - (SMS_DEBOUNCE_SECONDS + 1)

    mock_client = MagicMock()
    with patch("pi.alert.Client", return_value=mock_client):
        sent = alert_mod._send_sms(["IRS"], "auto", "after debounce")

    assert sent is True


def test_send_sms_twilio_failure_retry(caplog):
    """Twilio fails → retries once, logs error, returns False after both fail."""
    import pi.alert as alert_mod
    _reset_alert_module()

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("Twilio error")

    with patch("pi.alert.Client", return_value=mock_client):
        with patch("time.sleep"):  # Don't actually sleep
            with caplog.at_level("ERROR", logger="pi.alert"):
                sent = alert_mod._send_sms(["IRS"], "auto", "test")

    assert sent is False
    assert mock_client.messages.create.call_count == 2  # initial + retry


# ── set_nest_cast ─────────────────────────────────────────────────────────────

def test_set_nest_cast_connected():
    import pi.alert as alert_mod
    mock_cast = MagicMock()
    alert_mod.set_nest_cast(mock_cast)
    assert alert_mod._nest_connected is True
    assert alert_mod._nest_cast is mock_cast
    alert_mod._nest_cast = None
    alert_mod._nest_connected = False


def test_set_nest_cast_none():
    import pi.alert as alert_mod
    alert_mod.set_nest_cast(None)
    assert alert_mod._nest_connected is False
    assert alert_mod._nest_cast is None


# ── fire_alert ────────────────────────────────────────────────────────────────

def test_fire_alert_auto(monkeypatch):
    """fire_alert('auto') calls all 4 concurrent actions and increments counter."""
    import pi.alert as alert_mod
    _reset_alert_module()

    calls = []

    monkeypatch.setattr(alert_mod, "_play_nest_warning", lambda *a, **kw: calls.append("nest"))
    monkeypatch.setattr(alert_mod, "_led_and_buzzer", lambda: calls.append("led"))
    monkeypatch.setattr(alert_mod, "_send_sms", lambda *a, **kw: calls.append("sms") or True)
    monkeypatch.setattr(alert_mod, "_reset_led_after_delay", lambda: None)

    fake_event_id = "evt-001"
    with patch("pi.alert.db.write_event", return_value=fake_event_id):
        with patch("pi.alert.sensecap.set_scam_detected"):
            with patch("sqlite3.connect"):
                alert_mod.fire_alert(
                    trigger_type="auto",
                    score=85,
                    keywords=["IRS", "gift cards"],
                    transcript="You owe the IRS money.",
                )

    assert alert_mod._alerts_fired == 1
    assert "nest" in calls
    assert "led" in calls
    assert "sms" in calls


def test_fire_alert_manual(monkeypatch):
    """fire_alert('manual') works with score=None."""
    import pi.alert as alert_mod
    _reset_alert_module()

    monkeypatch.setattr(alert_mod, "_play_nest_warning", lambda *a, **kw: None)
    monkeypatch.setattr(alert_mod, "_led_and_buzzer", lambda: None)
    monkeypatch.setattr(alert_mod, "_send_sms", lambda *a, **kw: True)
    monkeypatch.setattr(alert_mod, "_reset_led_after_delay", lambda: None)

    with patch("pi.alert.db.write_event", return_value="evt-002"):
        with patch("pi.alert.sensecap.set_scam_detected"):
            with patch("sqlite3.connect"):
                alert_mod.fire_alert(
                    trigger_type="manual",
                    score=None,
                    keywords=[],
                    transcript="(Manual trigger)",
                )

    assert alert_mod._alerts_fired == 1


def test_fire_alert_nest_failure_doesnt_block(monkeypatch):
    """Nest failure must not block other alerts from firing."""
    import pi.alert as alert_mod
    _reset_alert_module()

    sms_called = []

    def _bad_nest(*_a, **_kw):
        raise RuntimeError("Nest exploded")

    monkeypatch.setattr(alert_mod, "_play_nest_warning", _bad_nest)
    monkeypatch.setattr(alert_mod, "_led_and_buzzer", lambda: None)
    monkeypatch.setattr(alert_mod, "_send_sms", lambda *a, **kw: sms_called.append(True) or True)
    monkeypatch.setattr(alert_mod, "_reset_led_after_delay", lambda: None)

    with patch("pi.alert.db.write_event", return_value="evt-003"):
        with patch("pi.alert.sensecap.set_scam_detected"):
            with patch("sqlite3.connect"):
                # Should not raise despite Nest failure
                alert_mod.fire_alert("auto", 90, ["IRS"], "test")

    assert len(sms_called) == 1


# ── get_metrics ───────────────────────────────────────────────────────────────

def test_get_metrics_initial():
    import pi.alert as alert_mod
    _reset_alert_module()
    m = alert_mod.get_metrics()
    assert m["alerts_fired"] == 0
    assert m["sms_sent"] == 0

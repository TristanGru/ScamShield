"""
test_hardware.py — GPIO and SenseCAP wrappers (mocked, no real Pi).
"""

from unittest.mock import MagicMock, patch

import pytest


def test_init_gpio_no_crash_without_rpi():
    import pi.hardware as hw

    if hw._GPIO_AVAILABLE:
        pytest.skip("RPi.GPIO present — skip sim test")
    hw.init_gpio()


def test_set_led_red_sim_mode(caplog):
    import pi.hardware as hw

    original = hw._GPIO_AVAILABLE
    hw._GPIO_AVAILABLE = False
    with caplog.at_level("DEBUG", logger="pi.hardware"):
        hw.set_led_red()
    hw._GPIO_AVAILABLE = original
    assert any("RED" in r.message for r in caplog.records)


def test_set_status_safe_calls_sensecap():
    import pi.hardware as hw

    with patch("pi.hardware.sensecap.set_safe") as m:
        hw.set_status_safe()
    m.assert_called_once()


def test_set_body_transcript_calls_sensecap():
    import pi.hardware as hw

    with patch("pi.hardware.sensecap.set_transcript") as m:
        hw.set_body_transcript("hello world")
    m.assert_called_once_with("hello world")


def test_setup_manual_button_skips_without_gpio(caplog):
    import pi.hardware as hw

    original = hw._GPIO_AVAILABLE
    hw._GPIO_AVAILABLE = False
    with caplog.at_level("WARNING", logger="pi.hardware"):
        hw.setup_manual_button(lambda c: None)
    hw._GPIO_AVAILABLE = original
    assert any("manual button disabled" in r.message.lower() for r in caplog.records)


def test_setup_manual_button_with_mock_gpio():
    import pi.hardware as hw

    mock_gpio = MagicMock()
    try:
        with patch.object(hw, "GPIO", mock_gpio):
            with patch.object(hw, "_GPIO_AVAILABLE", True):

                def _cb(ch):
                    pass

                hw._gpio_inited = False
                hw.setup_manual_button(_cb, bouncetime_ms=500)
                mock_gpio.setmode.assert_called()
                mock_gpio.setup.assert_called()
    finally:
        hw._gpio_inited = False

"""
hardware.py — GPIO LEDs, buzzer, manual button, SenseCAP helpers (PRD Phase 1).

Single place for physical I/O used by main.py and alert.py.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

try:
    from pi.config import (
        GPIO_BUZZER_PIN,
        GPIO_BUTTON_PIN,
        GPIO_LED_GREEN_PIN,
        GPIO_LED_RED_PIN,
    )
except ImportError:
    from config import (
        GPIO_BUZZER_PIN,
        GPIO_BUTTON_PIN,
        GPIO_LED_GREEN_PIN,
        GPIO_LED_RED_PIN,
    )

import sensecap

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO

    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO = None
    _GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available — hardware simulation mode")

_gpio_inited = False


def init_gpio() -> None:
    """Configure BCM pins for LEDs and buzzer (idempotent)."""
    global _gpio_inited
    if _gpio_inited or not _GPIO_AVAILABLE or GPIO is None:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_LED_RED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(GPIO_LED_GREEN_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(GPIO_BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)
    _gpio_inited = True
    logger.info("GPIO initialized — LED/Buzzer ready")


def set_led_red() -> None:
    init_gpio()
    if not _GPIO_AVAILABLE or GPIO is None:
        logger.debug("[SIM] LED → RED")
        return
    try:
        GPIO.output(GPIO_LED_RED_PIN, GPIO.HIGH)
        GPIO.output(GPIO_LED_GREEN_PIN, GPIO.LOW)
    except Exception as exc:
        logger.error("LED red failed: %s", exc)


def set_led_green() -> None:
    init_gpio()
    if not _GPIO_AVAILABLE or GPIO is None:
        logger.debug("[SIM] LED → GREEN")
        return
    try:
        GPIO.output(GPIO_LED_RED_PIN, GPIO.LOW)
        GPIO.output(GPIO_LED_GREEN_PIN, GPIO.HIGH)
    except Exception as exc:
        logger.error("LED green failed: %s", exc)


def sound_buzzer(duration: float = 2.0) -> None:
    init_gpio()
    if not _GPIO_AVAILABLE or GPIO is None:
        logger.debug("[SIM] BUZZER for %.1fs", duration)
        return
    import time

    try:
        pwm = GPIO.PWM(GPIO_BUZZER_PIN, 1000)  # 1 kHz tone — works for passive and active buzzers
        pwm.start(50)
        time.sleep(duration)
        pwm.stop()
        GPIO.output(GPIO_BUZZER_PIN, GPIO.LOW)
        logger.debug("Buzzer sounded for %.1fs", duration)
    except Exception as exc:
        logger.error("Buzzer failed: %s", exc)


def set_status_safe() -> None:
    """PRD: SenseCAP shows call seems safe."""
    sensecap.set_safe()


def set_status_scam(transcript: str = "") -> None:
    """PRD-style scam warning on SenseCAP."""
    sensecap.set_scam_detected(transcript)


def set_status_listening() -> None:
    sensecap.set_listening()


def set_body_transcript(text: str) -> None:
    sensecap.set_transcript(text)


def setup_manual_button(on_press: Callable[[int], None], bouncetime_ms: int = 2000) -> None:
    """
    Rising-edge interrupt on the Grove button (PRD: physical manual report).
    """
    if not _GPIO_AVAILABLE or GPIO is None:
        logger.warning("GPIO not available — manual button disabled")
        return
    init_gpio()
    try:
        GPIO.setup(GPIO_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        def _cb(channel: int) -> None:
            on_press(channel)

        GPIO.add_event_detect(
            GPIO_BUTTON_PIN,
            GPIO.RISING,
            callback=_cb,
            bouncetime=bouncetime_ms,
        )
        logger.info("Manual button registered on GPIO %d", GPIO_BUTTON_PIN)
    except Exception as exc:
        logger.error("Button setup failed: %s", exc)


def cleanup_gpio() -> None:
    """Release GPIO resources."""
    global _gpio_inited
    if _GPIO_AVAILABLE and GPIO is not None:
        try:
            GPIO.cleanup()
        except Exception:
            pass
    _gpio_inited = False

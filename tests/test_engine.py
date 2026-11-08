"""Engine decisions that don't need hardware."""
from ditoo_control.engine import Engine


def make():
    e = Engine()
    e.cfg["away"]["enabled"] = False
    return e


def test_off_mode_switches_the_leds_off():
    e = make()
    e.cfg["mode"] = "off"
    assert e.brightness() == 0


def test_away_turns_the_display_off():
    e = make()
    e.away = True
    scene, reason = e.compute()
    assert scene["key"] == ("off",) and e.brightness() == 0 and reason


def test_night_brightness_can_be_zero():
    e = make()
    e.cfg["night"].update(enabled=True, start=0, end=24, brightness=0)
    e.cfg["mode"] = "clock"
    assert e.brightness() == 0


def test_pomodoro_mode_does_not_start_the_timer():
    e = make()
    e.set_mode("pomodoro")
    e.compute()
    assert not e.pomo.running


def test_stopping_pomodoro_returns_to_automatic():
    e = make()
    e.set_mode("pomodoro")
    e.pomodoro_action("start")
    e.pomodoro_action("stop")
    assert e.cfg["mode"] == "auto" and not e.pomo.running


def test_ai_heartbeats_are_not_logged_twice():
    e = make()
    e.ai_event("claude", "working")
    n = len(e.logs)
    e.ai_event("claude", "working")
    assert len(e.logs) == n

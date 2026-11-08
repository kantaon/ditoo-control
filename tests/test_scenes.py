"""Every scene is valid for the device and pixel-exact."""
import pytest

from ditoo_control import ditoo, gfx, i18n, scenes


@pytest.fixture(params=["en", "cs"])
def lang(request):
    i18n.set_lang(request.param)
    scenes.clear_cache()
    yield request.param
    i18n.set_lang("en")


def all_scenes():
    out = [(k, sc) for k, _t, _d, sc in scenes.gallery()]
    out += [("test", scenes.test_pattern()), ("weather_unset", scenes.weather_unset()), ("media_missing", scenes.media_missing()),
            ("pomo_ready", scenes.pomodoro_ready(25)), ("ai_idle", scenes.ai_idle()), ("off", scenes.off())]
    return out


def test_scenes_are_valid_for_the_device(lang):
    for key, sc in all_scenes():
        assert sc["kind"] in ("anim", "image", "native"), key
        assert 1 <= len(sc["frames"]) <= ditoo.MAX_FRAMES, key
        assert len(sc["ms"]) == len(sc["frames"]), key
        assert sc["label"], key
        for f in sc["frames"]:
            assert len(f) == 256, key
            assert all(len(p) == 3 and all(0 <= c <= 255 for c in p) for p in f), key
        size = sum(len(ditoo.encode_frame(f, 100)) for f in sc["frames"])
        assert size < 65535, key               # animation length field is 16 bits


def lit_margins(frame):
    xs = [x for y in range(16) for x in range(16) if sum(frame[y * 16 + x]) > 30]
    return (min(xs), 15 - max(xs)) if xs else None


@pytest.mark.parametrize("key", ["clock", "game", "weather", "weather_snow", "weather_night", "ai_claude", "ai_codex",
                                 "ai_attn", "ai_error", "pomodoro", "viz", "notify", "hot"])
def test_centred_scenes_are_symmetric(key):
    sc = dict((k, s) for k, s in all_scenes())[key]
    for f in sc["frames"]:
        m = lit_margins(f)
        if m:
            assert abs(m[0] - m[1]) <= 1, (key, m)


@pytest.mark.parametrize("temp", [-12, -3, 0, 7, 12, 24, 35])
def test_temperature_label_is_centred(temp):
    w = {"temp": temp, "code": 0, "is_day": True, "text": "Clear", "tomorrow": {"code": 0, "max": 1, "text": "Clear"}}
    f = scenes.weather(w)["frames"][0]
    xs = [x for y in range(11, 16) for x in range(16) if sum(f[y * 16 + x]) > 30]
    assert abs(min(xs) - (15 - max(xs))) <= 1


def test_punctuation_is_proportional():
    assert gfx.text_width("7") == 3
    assert gfx.text_width("7°") == 3 + 1 + 2
    assert gfx.text_width("1:2") == 3 + 1 + 1 + 1 + 3


def test_live_screens_are_still_images():
    class T:
        cpu_temp, gpu_temp, cpu_load, gpu_load = 60, 55, 30, 70
    cfg = {"cpu_warn": 80, "cpu_crit": 90, "gpu_warn": 78, "gpu_crit": 86, "fps_good": 60}
    assert scenes.monitor(T, cfg)["kind"] == "image"
    assert scenes.game(T, 120, cfg, "X", [(8.0, 8.0)] * 16)["kind"] == "image"


def test_clock_holds_the_last_second_until_the_next_upload():
    sc = scenes.clock({"clock_color": [80, 200, 255], "clock_type": "animated"}, now=1_700_000_000 - 0.5)
    assert sc["ms"][-1] > 1000
    assert all(ms == 1000 for ms in sc["ms"][:-1])


def test_pomodoro_screen_never_starts_the_timer():
    sc = scenes.pomodoro_ready(25)
    assert sc["key"][0] == "pomo_ready"

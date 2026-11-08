"""Everything the Ditoo Pro can show, drawn pixel-exact for its 16x16 panel.

Design rules
- Live data screens (PC monitor, game HUD) are still images updated in place: re-uploading an
  animation every second restarts it and makes the numbers flicker.
- Everything else is a seamless loop: frame counts are multiples of every motion period, and
  motion is either brightness easing or whole-pixel paths – never rounded circles that wobble.
- Layouts are symmetric on the 16 px grid (odd-width elements get 2 px gaps to stay centred).

A scene is a dict:
  kind     'anim' | 'image' | 'native'
  key      identity; the device worker re-uploads only when the key changes
  frames   list of 256-pixel lists (upload + UI preview)
  ms       per-frame durations
  label    human description for the UI
  throttle minimum seconds between re-uploads of the same scene family
  native   for kind 'native': (driver method, kwargs)
"""
import colorsys
import math
import random
import time

from .gfx import CHECK, CROSS, SIZE, WHITE, Canvas, lerp, scale, temp_color, text_width, usage_color
from .i18n import _

TAU = 2 * math.pi
DIM_BG = (16, 16, 20)


def anim(frames, ms, label, key, throttle=0.0):
    if not isinstance(ms, list):
        ms = [ms] * len(frames)
    return {"kind": "anim", "key": key, "frames": [f.pixels() for f in frames], "ms": ms,
            "label": label, "throttle": throttle}


def still(c, label, key, throttle=0.0):
    return {"kind": "image", "key": key, "frames": [c.pixels()], "ms": [1000], "label": label, "throttle": throttle}


def ease(f, n, phase=0.0):
    """Smooth 0..1..0 over n frames (cosine)."""
    return 0.5 - 0.5 * math.cos(TAU * (f / n + phase))


def _num(v):
    return "--" if v is None else str(max(0, min(99, int(round(v)))))


def big_number(c, s, y, color):
    """4x7 digits centred on the panel. Two digits get a 2 px gap so they sit exactly in the middle."""
    s = str(s)
    if len(s) == 2:
        c.text(3, y, s[0], color, font=4)
        c.text(9, y, s[1], color, font=4)
    else:
        c.text((16 - text_width(s, 4)) // 2, y, s, color, font=4)


def small_centered(c, s, y, color):
    c.text((16 - text_width(s)) // 2, y, s, color)


def _bar(c, x, y, w, frac, color, bg=DIM_BG):
    n = round(max(0.0, min(1.0, frac)) * w)
    for i in range(w):
        c.set(x + i, y, color if i < n else bg)


def _temp_or_load(temp, load, warn, crit):
    """Temperature when we have one; otherwise (no MSI Afterburner) the load in %, so the screen is never empty."""
    if temp is not None or load is None:
        return temp, temp_color(temp, warn, crit)
    return min(99, load), usage_color(load / 100)


# ======================================================================================
# PC monitor (still, updated in place)
def monitor(t, cfg):
    c = Canvas()
    rows = ((0, "C", t.cpu_temp, t.cpu_load, cfg["cpu_warn"], cfg["cpu_crit"], (255, 120, 40)),
            (8, "G", t.gpu_temp, t.gpu_load, cfg["gpu_warn"], cfg["gpu_crit"], (110, 210, 60)))
    for y, lbl, temp, load, warn, crit, lc in rows:
        c.text(0, y + 1, lbl, lc)
        value, col = _temp_or_load(temp, load, warn, crit)
        s = _num(value).rjust(2)
        c.text(4, y, s[0], col, font=4)
        c.text(9, y, s[1], col, font=4)
        if temp is not None:                                              # degree mark = it is a temperature
            for x, yy in ((14, y), (15, y), (14, y + 1), (15, y + 1)):
                c.set(x, yy, scale(col, 0.7))
        frac = (load or 0) / 100
        _bar(c, 0, y + 7, 16, frac, usage_color(frac))
    return still(c, _("PC monitor – temperatures and load"), ("monitor", tuple(c.px)), throttle=0.9)


# ======================================================================================
# Gaming HUD (still, updated in place)
GAMEPAD = [
    "..############..",
    ".##############.",
    "###.########.###",
    "##...######.#.##",
    "###.########.###",
    "################",
    "#####......#####",
    ".###........###.",
]


def frametime_color(ms):
    if ms is None:
        return (40, 40, 48)
    if ms <= 17.5:
        return (0, 220, 110)      # 60+ FPS pace
    if ms <= 34:
        return (240, 200, 0)      # 30-60 FPS pace
    return (255, 45, 35)          # stutter


def game(t, fps, cfg, name, ft_hist=None):
    """FPS on top, CPU | GPU temperature, frametime graph of the last 16 s at the bottom."""
    c = Canvas()
    if fps:
        f = int(round(fps))
        col = (0, 230, 110) if f >= cfg.get("fps_good", 60) else (240, 210, 0) if f >= 30 else (255, 40, 30)
        big_number(c, min(f, 999), 0, col)
    else:
        c.icon(0, 0, GAMEPAD[:7], {"#": (110, 110, 255)})
    cv, ccol = _temp_or_load(t.cpu_temp, t.cpu_load, cfg["cpu_warn"], cfg["cpu_crit"])
    gv, gcol = _temp_or_load(t.gpu_temp, t.gpu_load, cfg["gpu_warn"], cfg["gpu_crit"])
    c.text(0, 8, _num(cv), ccol)
    c.text(9, 8, _num(gv), gcol)
    for x in range(7):                                   # which number is which
        c.set(x, 13, (150, 70, 25))                      # CPU = orange (same as monitor)
        c.set(9 + x, 13, (55, 120, 30))                  # GPU = green
    hist = list(ft_hist or [])[-16:]
    hist = [None] * (16 - len(hist)) + hist
    for x, item in enumerate(hist):
        if not item or item[0] is None:
            c.set(x, 15, (22, 22, 28))
            continue
        ms, avg = item
        col = frametime_color(ms)
        c.set(x, 15, col)
        if avg and ms > avg * 1.6 and ms > 12:           # spike → taller bar
            c.set(x, 14, col)
    last = next((i[0] for i in reversed(hist) if i and i[0]), None)
    lbl = _("Gaming – {name}", name=name) + (f" · {int(round(fps))} FPS" if fps else "") + (f" · {last:.1f} ms" if last else "")
    return still(c, lbl, ("game", tuple(c.px)), throttle=0.9)


def game_intro(name):
    label = name.upper()
    tw = text_width(label)
    frames = []
    n = 16 + tw + 1
    for off in range(n):
        f = Canvas()
        k = ease(off, 24)
        f.icon(0, 1, GAMEPAD, {"#": lerp((100, 100, 255), (230, 90, 220), k)})
        f.text(16 - off, 11, label, WHITE)
        frames.append(f)
        if len(frames) >= 60:
            break
    return anim(frames, 60, _("Game started – {name}", name=name), ("intro", name))


# ======================================================================================
# Weather – hand-drawn 16x10 icons, temperature on rows 11-15
SUN = [
    ".......oo.......",
    "..d..........d..",
    "...d..####..d...",
    ".....######.....",
    ".oo..######..oo.",
    ".oo..######..oo.",
    ".....######.....",
    "...d..####..d...",
    "..d..........d..",
    ".......oo.......",
]
MOON = [
    "......###.......",
    ".....##.........",
    "....##..........",
    "....##..........",
    "....##..........",
    "....###.........",
    ".....###....#...",
    "......#######...",
    "................",
    "................",
]
SMALL_SUN = [
    "...o............",
    ".d...d..........",
    "..###...........",
    "o#####o.........",
    "..###...........",
    ".d...d..........",
    "...o............",
]
CLOUD = [
    "......####......",
    "....########....",
    "..############..",
    ".##############.",
    ".##############.",
    "..############..",
]
STARS = [(1, 1), (13, 0), (14, 5), (10, 3), (2, 7)]


def _cloud(c, x, y, color, shade=None):
    c.icon(x, y, CLOUD, {"#": color})
    if shade:  # darker underside gives volume
        for xx in range(16):
            if c.get(xx, y + 5) == color if 0 <= y + 5 < 16 else False:
                c.set(xx, y + 5, shade)


def weather_frames(code, is_day):
    rng = random.Random(code * 7 + 1)
    frames = []
    clear = code in (0, 1)
    partly = code == 2
    cloudy = code == 3
    fog = code in (45, 48)
    snow = code in (71, 73, 75, 77, 85, 86)
    storm = code in (95, 96, 99)
    n = 24
    drops = [(x, rng.randrange(6), rng.choice((1, 1, 2))) for x in (2, 5, 8, 11, 14)]
    flakes = [(x, rng.randrange(6)) for x in (3, 7, 10, 13)]
    for f in range(n):
        c = Canvas()
        if clear and is_day:
            k = ease(f, n)
            c.icon(0, 0, SUN, {"#": (255, 205, 40), "o": lerp((255, 120, 0), (255, 190, 40), k),
                               "d": lerp((255, 190, 40), (255, 120, 0), k)})
        elif clear:
            c.icon(0, 0, MOON, {"#": (225, 225, 175)})
            for i, (x, y) in enumerate(STARS):
                c.set(x, y, scale(WHITE, 0.15 + 0.85 * ease(f, n, i / len(STARS))))
        elif partly or cloudy:
            if partly and is_day:
                k = ease(f, n)
                c.icon(1, 0, SMALL_SUN, {"#": (255, 205, 40), "o": lerp((255, 120, 0), (255, 190, 40), k),
                                         "d": lerp((255, 190, 40), (255, 120, 0), k)})
            dx = 1 if 6 <= f < 18 else 0           # slow, single-pixel drift
            col = (205, 208, 220) if partly else (160, 166, 182)
            _cloud(c, dx + (1 if partly else 0) - 1, 3 if partly else 2, col, scale(col, 0.75))
        elif fog:
            for i, y in enumerate((1, 3, 5, 7, 9)):
                off = 1 if ((f // 6) + i) % 2 else 0
                for x in range(1 + off, 14 + off - (i % 2) * 2):
                    c.set(x, y, scale((170, 172, 185), 0.55 + 0.1 * i))
        else:
            col = (110, 114, 130) if storm else (150, 156, 175)
            _cloud(c, 0, 0, col, scale(col, 0.7))
            for x, ph, speed in drops if not snow else []:
                y = 6 + ((f * speed + ph) % 6)
                if y <= 9:
                    c.set(x, y, (100, 170, 255))
                    if y - 1 >= 6:
                        c.set(x, y - 1, (40, 70, 130))
            for x, ph in flakes if snow else []:
                y = 6 + ((f // 2 + ph) % 6)
                xx = x + (1 if ((f // 4 + ph) % 2) else 0)
                if y <= 9:
                    c.set(xx, y, WHITE)
            if storm and f in (3, 4, 15):
                for x, y in ((8, 5), (7, 6), (7, 7), (8, 7), (8, 8), (7, 9)):
                    c.set(x, y, (255, 235, 70))
        frames.append(c)
    return frames


def weather(w, tomorrow=False, city=""):
    if not w:
        frames = []
        for f in range(12):
            c = Canvas()
            for i in range(3):
                c.set(5 + i * 3, 7, scale((150, 150, 180), 0.2 + 0.8 * ease(f, 12, i / 3)))
            frames.append(c)
        return anim(frames, 110, _("Weather – loading"), ("weather_loading",))
    if tomorrow:
        code, temp, is_day = w["tomorrow"]["code"], w["tomorrow"]["max"], True
    else:
        code, temp, is_day = w["code"], w["temp"], w["is_day"]
    t = int(round(temp))
    s = f"{t}°"
    col = (90, 170, 255) if t <= 0 else (130, 220, 255) if t < 10 else (255, 230, 120) if t < 25 else (255, 120, 60)
    frames = weather_frames(code, is_day)
    for c in frames:
        if tomorrow:
            c.text(0, 11, _("T"), (150, 150, 170))
            c.text(16 - text_width(s), 11, s, col)
        else:
            small_centered(c, s, 11, col)
    if tomorrow:
        lbl = _("Tomorrow – {text}, high {t} °C", text=_(w["tomorrow"]["text"]), t=t)
    elif city:
        lbl = _("Weather – {city} – {text}, {t} °C", city=city, text=_(w["text"]), t=t)
    else:
        lbl = _("Weather – {text}, {t} °C", text=_(w["text"]), t=t)
    return anim(frames, 120, lbl, ("weather", code, is_day, t, tomorrow))


# ======================================================================================
# Clock – big HH over MM, blinking centre dots, side columns fill up with the seconds.
# One 60-frame animation per minute; it is re-uploaded exactly when the digits change anyway.
def _clock_frame(lt, color):
    c = Canvas()
    big_number(c, time.strftime("%H", lt), 0, color)
    big_number(c, time.strftime("%M", lt), 9, color)
    if lt.tm_sec % 2 == 0:
        for x, y in ((7, 7), (8, 7), (7, 8), (8, 8)):
            c.set(x, y, lerp(color, WHITE, 0.3))
    filled = (lt.tm_sec + 1) * 16 // 60
    for i in range(16):
        y = 15 - i
        col = scale(color, 0.35) if i < filled else (20, 20, 26)
        if i == filled - 1:
            col = lerp(color, WHITE, 0.4)
        c.set(0, y, col), c.set(15, y, col)
    return c


def clock(cfg, now=None):
    if cfg.get("clock_type") == "native":
        return native_clock(cfg)
    now = now or time.time()
    start = math.floor(now) + 1  # the upload itself takes a moment
    color = tuple(cfg["clock_color"])
    lt0 = time.localtime(start)
    remaining = 60 - lt0.tm_sec
    frames = [_clock_frame(time.localtime(start + i), color) for i in range(remaining)]
    ms = [1000] * len(frames)
    ms[-1] = 3000  # hold :59 until the next minute's upload arrives (never loop back)
    stamp = time.strftime("%H:%M", lt0)
    return anim(frames, ms, _("Clock {time}", time=stamp), ("clock", stamp, color))


def native_clock(cfg):
    color = tuple(cfg["clock_color"])
    c = _clock_frame(time.localtime(), color)
    return {"kind": "native", "key": ("nclock", color, cfg.get("clock_style", 0)), "frames": [c.pixels()],
            "ms": [1000], "label": _("Native Divoom clock"), "throttle": 0,
            "native": ("clock", {"style": cfg.get("clock_style", 0), "color": color, "h24": True})}


def lamp(color):
    c = Canvas(bg=tuple(color))
    return {"kind": "native", "key": ("lamp", tuple(color)), "frames": [c.pixels()], "ms": [1000],
            "label": _("Lamp"), "throttle": 0, "native": ("light", {"color": tuple(color)})}


def visualizer(n=0):
    frames = []
    heights = [3, 6, 10, 13, 9, 12, 14, 8, 11, 13, 7, 10, 12, 6, 9, 4]
    for f in range(16):
        c = Canvas()
        for x in range(16):
            h = max(1, round(heights[x] * (0.45 + 0.55 * ease(f, 16, x / 7))))
            for y in range(16 - h, 16):
                c.set(x, y, lerp((0, 200, 255), (255, 0, 160), (15 - y) / 15))
        frames.append(c)
    sc = anim(frames, 80, _("Music visualizer (reacts to sound played on the Ditoo)"), ("viz", n))
    sc.update(kind="native", native=("visualizer", {"n": n}))
    return sc


def weather_unset():
    """Weather screen before a location is chosen: a pin icon."""
    frames = []
    pin = ["..####..", ".######.", "###..###", "###..###", ".######.", "..####..", "...##...", "...##..."]
    for f in range(20):
        c = Canvas()
        c.icon(4, 3, pin, {"#": lerp((90, 140, 255), (160, 200, 255), ease(f, 20))})
        frames.append(c)
    return anim(frames, 100, _("Weather – set your location in the app"), ("weather_unset",))


def media_missing():
    frames = []
    for f in range(20):
        c = Canvas()
        col = scale((150, 150, 180), 0.4 + 0.6 * ease(f, 20))
        for x in range(4, 12):
            c.set(x, 3, col), c.set(x, 12, col)
        for y in range(3, 13):
            c.set(4, y, col), c.set(11, y, col)
        c.set(7, 6, col), c.set(8, 6, col)
        for x, y in ((6, 10), (7, 9), (8, 10), (9, 9), (10, 10), (5, 11), (6, 11), (7, 11), (8, 11), (9, 11), (10, 11)):
            c.set(x, y, col)
        frames.append(c)
    return anim(frames, 100, _("Image / GIF"), ("media_missing",))


def test_pattern():
    """Setup wizard check: a rainbow frame and a big pulsing check mark – impossible to miss."""
    frames = []
    for f in range(24):
        c = Canvas()
        for i, (x, y) in enumerate(BORDER):
            c.set(x, y, _hue(i / len(BORDER) + f / 24))
        k = ease(f, 24)
        for y in range(16):
            for x in range(16):
                if CHECK[y][x] == "#" and 1 <= x <= 14 and 1 <= y <= 14:
                    c.set(x, y, lerp((40, 230, 110), WHITE, 0.4 * k))
        frames.append(c)
    return anim(frames, 60, "Test", ("test",))


def off():
    return still(Canvas(), _("Off"), ("off",))


# ======================================================================================
# AI agents – a comet travelling a pixel-exact rounded square
def _track(inset=1):
    a, b = inset, 15 - inset
    pts = [(x, a) for x in range(a + 1, b)] + [(b, y) for y in range(a + 1, b)] + \
          [(x, b) for x in range(b - 1, a, -1)] + [(a, y) for y in range(b - 1, a, -1)]
    return pts


TRACK = _track(1)          # 48 pixels
AI_COLORS = {"claude": (235, 120, 70), "codex": (40, 205, 185)}
AI_NAMES = {"claude": "Claude", "codex": "Codex (ChatGPT)"}

# Each agent has its own 8x8 sign, centred inside the ring (x4..11, y4..11)
GLYPHS = {
    "claude": [            # eight-point spark
        "...##...",
        ".#.##.#.",
        "..####..",
        "########",
        "########",
        "..####..",
        ".#.##.#.",
        "...##...",
    ],
    "codex": [             # terminal prompt >_
        "........",
        "##......",
        ".##.....",
        "..##....",
        ".##.....",
        "##......",
        "....####",
        "........",
    ],
}
GENERIC_GLYPH = ["........", "..####..", ".#....#.", ".#.##.#.", ".#.##.#.", ".#....#.", "..####..", "........"]


def _ai_color(source):
    return AI_COLORS.get(source or "", (180, 120, 255))


def _label(source):
    return AI_NAMES.get(source or "", (source or "AI").capitalize())


def agent_name(source):
    return _label(source)


def _badge(c, source):
    """Small agent-coloured corner mark so done / error / waiting screens say who it was."""
    col = _ai_color(source)
    for x, y in ((0, 0), (1, 0), (0, 1)):
        c.set(x, y, col)


def _agent_frames(source, n=24):
    color = _ai_color(source)
    glyph = GLYPHS.get(source, GENERIC_GLYPH)
    direction = -1 if source == "codex" else 1      # Codex orbits the other way
    step, tail = 2, 14
    frames = []
    for f in range(n):
        c = Canvas()
        head = (f * step * direction) % len(TRACK)
        for i, (x, y) in enumerate(TRACK):
            d = ((head - i) * direction) % len(TRACK)
            k = 1 - d / tail if d < tail else 0
            c.set(x, y, lerp(scale(color, 0.12), lerp(color, WHITE, 0.3 if d == 0 else 0), k) if k else scale(color, 0.12))
        if source == "codex":
            body = color
            cursor_on = (f // 6) % 2 == 0            # blinking cursor, 0.3 s on / off
            for gy, row in enumerate(glyph):
                for gx, ch in enumerate(row):
                    if ch == "#" and (gy < 6 or cursor_on):
                        c.set(4 + gx, 4 + gy, lerp(body, WHITE, 0.25))
        else:
            k = ease(f, n)                           # the spark breathes
            for gy, row in enumerate(glyph):
                for gx, ch in enumerate(row):
                    if ch == "#":
                        core = 2 <= gx <= 5 and 2 <= gy <= 5
                        c.set(4 + gx, 4 + gy, lerp(color, (255, 220, 190), (0.55 if core else 0.15) * k + (0.2 if core else 0)))
        frames.append(c)
    return frames


def ai_working(source="claude", sources=None):
    """One agent: its own loop. Several agents at once: their loops play one after another."""
    sources = [s for s in (sources or [source]) if s] or ["claude"]
    frames = []
    for s in sources[:2]:
        frames += _agent_frames(s)
    names = " + ".join(_label(s) for s in sources[:2])
    label = _("{agents} are working…", agents=names) if len(sources) > 1 else _("{agent} is working…", agent=names)
    return anim(frames, 50, label, ("ai_working", tuple(sources[:2])))


def ai_idle():
    frames = []
    for f in range(20):
        k = ease(f, 20)
        c = Canvas()
        for x, y in TRACK:
            c.set(x, y, scale((110, 110, 150), 0.15 + 0.25 * k))
        c.icon(4, 4, GENERIC_GLYPH, {"#": scale((150, 150, 180), 0.35 + 0.3 * k)})
        frames.append(c)
    return anim(frames, 120, _("AI – nothing running"), ("ai_idle",))


def ai_done(source="claude"):
    green = (40, 230, 110)
    pts = sorted((x, y) for y in range(16) for x in range(16) if CHECK[y][x] == "#")
    frames, ms = [], []
    for s in range(1, 11):
        c = Canvas()
        for x, y in pts[: math.ceil(len(pts) * s / 10)]:
            c.set(x, y, green)
        _badge(c, source)
        frames.append(c), ms.append(35)
    for s in range(12):
        c = Canvas()
        k = ease(s, 12)
        for x, y in pts:
            c.set(x, y, lerp(green, WHITE, 0.35 * k))
        _badge(c, source)
        frames.append(c), ms.append(90)
    frames.append(frames[-1]), ms.append(1200)
    return anim(frames, ms, _("{agent} finished the task", agent=_label(source)), ("ai_done", source))


def ai_error(source="claude"):
    red = (255, 50, 40)
    frames, ms = [], []
    for dx in (0, -1, 1, -1, 1, 0):
        c = Canvas(bg=(45, 0, 0))
        c.icon(dx, 0, CROSS, {"#": red})
        _badge(c, source)
        frames.append(c), ms.append(60)
    for s in range(12):
        c = Canvas(bg=scale((45, 0, 0), 1 - ease(s, 24)))
        c.icon(0, 0, CROSS, {"#": scale(red, 0.6 + 0.4 * ease(s, 12, 0.5))})
        _badge(c, source)
        frames.append(c), ms.append(100)
    return anim(frames, ms, _("{agent} – error", agent=_label(source)), ("ai_error", source))


def ai_attention(source="claude"):
    color = _ai_color(source)
    frames = []
    n = 20
    for f in range(n):
        c = Canvas()
        k = ease(f, n)
        col = lerp((120, 85, 0), (255, 205, 0), k)
        c.rect(7, 2, 2, 8, col)
        c.rect(6, 3, 4, 6, col)
        c.rect(7, 11, 2, 2, col)
        for i, (x, y) in enumerate(TRACK):
            if (i - f * 2) % 12 < 2:
                c.set(x, y, scale(color, 0.8))
        _badge(c, source)
        frames.append(c)
    return anim(frames, 70, _("{agent} is waiting for you", agent=_label(source)), ("ai_attn", source))


# ======================================================================================
# Overheating – thermometer on the left, big temperature on the right
def overheat(which, temp):
    frames = []
    n = 16
    for f in range(n):
        k = ease(f, n)
        c = Canvas(bg=scale((90, 0, 0), 0.25 + 0.75 * k))
        glass = (230, 220, 220)
        for y in range(1, 11):
            c.set(0, y, glass), c.set(4, y, glass)
        c.set(1, 0, glass), c.set(2, 0, glass), c.set(3, 0, glass)
        c.rect(0, 11, 5, 4, glass)
        c.rect(1, 12, 3, 2, (255, 40, 30))
        level = 3 if f < n // 2 else 2
        for y in range(level, 12):
            c.set(2, y, (255, 40, 30))
        s = _num(temp)
        c.text(6, 1, s[0], WHITE, font=4)
        c.text(11, 1, s[1], WHITE, font=4)
        c.text(5, 10, which, lerp((255, 160, 140), WHITE, k))
        frames.append(c)
    return anim(frames, 70, _("Overheating {part}: {temp} °C", part=which, temp=int(temp)), ("hot", which, _num(temp)))


# ======================================================================================
# Pomodoro – one-second frames, the 60-pixel border is the progress ring
def _border():
    pts = [(x, 0) for x in range(16)] + [(15, y) for y in range(1, 16)] + \
          [(x, 15) for x in range(14, -1, -1)] + [(0, y) for y in range(14, 0, -1)]
    return pts[8:] + pts[:8]


BORDER = _border()


def _pomo_frame(remaining, total, phase, paused, blink):
    color = (255, 90, 60) if phase == "focus" else (60, 220, 130)
    c = Canvas()
    frac = remaining / total if total else 0
    lit = math.ceil(len(BORDER) * frac)
    for i, (x, y) in enumerate(BORDER):
        if i < lit:
            c.set(x, y, lerp(color, WHITE, 0.5) if i == lit - 1 and blink else color)
        else:
            c.set(x, y, (26, 26, 32))
    if remaining >= 60:
        big_number(c, min(99, math.ceil(remaining / 60)), 2, scale(WHITE, 0.55) if paused else WHITE)
        small_centered(c, "II" if paused else ("MIN" if phase == "focus" else _("BRK")), 10, scale(color, 0.9))
    else:
        big_number(c, int(remaining), 4, color)
    return c


def pomodoro_ready(minutes):
    """Pomodoro screen while the timer is not running: shows the length, waits for Start."""
    color = (255, 90, 60)
    frames = []
    for f in range(20):
        c = Canvas()
        k = ease(f, 20)
        for x, y in BORDER:
            c.set(x, y, scale(color, 0.12 + 0.18 * k))
        big_number(c, min(99, int(minutes)), 2, scale(WHITE, 0.45 + 0.25 * k))
        small_centered(c, "MIN", 10, scale(color, 0.5))
        frames.append(c)
    label = _("Pomodoro ready – {min} min (start it in the app)", min=int(minutes))
    return anim(frames, 100, label, ("pomo_ready", int(minutes)))


def pomodoro(remaining, total, phase, paused):
    mins, secs = divmod(int(remaining), 60)
    lbl = (_("Focus") if phase == "focus" else _("Break")) + f" – {mins}:{secs:02d}" + (_(" (paused)") if paused else "")
    if paused:
        frames = [_pomo_frame(remaining, total, phase, True, b) for b in (True, False)]
        return anim(frames, 800, lbl, ("pomo", phase, int(remaining), "paused"))
    start = max(0, int(remaining) - 1)
    count = min(60, start + 1)
    frames = [_pomo_frame(start - i, total, phase, False, i % 2 == 0) for i in range(count)]
    return anim(frames, 1000, lbl, ("pomo", phase, int(remaining // 60), round(total)))


# ======================================================================================
# Text, notifications, media
def _hue(h, s=1.0, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def scrolling_text(text, color=(255, 255, 255), rainbow=False, label=None, key=None):
    text = (text or "").strip() or " "
    tw = text_width(text)
    color = tuple(color)
    if tw <= 16:
        frames = []
        for f in range(20):
            c = Canvas()
            col = _hue(f / 20) if rainbow else scale(color, 0.7 + 0.3 * ease(f, 20))
            small_centered(c, text, 5, col)
            frames.append(c)
        return anim(frames, 90, label or _("Text: {text}", text=text), key or ("text", text, color, rainbow))
    n = 16 + tw + 1
    step = max(1, math.ceil(n / 60))
    frames = []
    for i, o in enumerate(range(0, n, step)):
        c = Canvas()
        if rainbow:
            x = 16 - o
            for j, ch in enumerate(text):
                c.text(x + j * 4, 5, ch, _hue(j / 10 + i / 60))
        else:
            c.text(16 - o, 5, text, color)
        frames.append(c)
    return anim(frames, 55 * step, label or _("Text: {text}", text=text), key or ("text", text, color, rainbow))


def notify(text, color=(255, 200, 0)):
    sc = scrolling_text(text, (255, 255, 255), label=_("Notification: {text}", text=text), key=("notify", text, time.time()))
    color = tuple(color)
    for i, fr in enumerate(sc["frames"]):
        for x in range(16):
            k = 0.35 + 0.65 * ease(x + i, 16)
            fr[x] = scale(color, k)
            fr[15 * 16 + x] = scale(color, k)
    return sc


def media(frames, ms, name):
    if len(frames) == 1:
        return {"kind": "image", "key": ("media", name), "frames": frames, "ms": [1000],
                "label": _("Image – {name}", name=name), "throttle": 0}
    return {"kind": "anim", "key": ("media", name), "frames": frames, "ms": ms,
            "label": _("Animation – {name}", name=name), "throttle": 0}


def load_media(path_or_file):
    """Image/GIF -> up to 60 16x16 frames with a small palette (fast Bluetooth upload)."""
    from PIL import Image, ImageSequence
    im = Image.open(path_or_file)
    frames, ms = [], []
    for fr in ImageSequence.Iterator(im):
        f = fr.convert("RGBA")
        w, h = f.size
        side = min(w, h)
        f = f.crop(((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side))
        f = f.resize((SIZE, SIZE), Image.NEAREST if side <= 64 else Image.LANCZOS)
        bg = Image.new("RGBA", f.size, (0, 0, 0, 255))
        f = Image.alpha_composite(bg, f).convert("RGB").quantize(colors=32).convert("RGB")
        frames.append([tuple(p) for p in f.getdata()])
        ms.append(max(40, min(2000, int(fr.info.get("duration", 100) or 100))))
        if len(frames) >= 60:
            break
    return frames, ms


# ======================================================================================
# Ambient effects – palettes kept at 16 colours so uploads stay quick
def _palette(stops, n=16):
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(stops) - 1)
        a = int(t)
        b = min(a + 1, len(stops) - 1)
        out.append(lerp(stops[a], stops[b], t - a))
    return out


def fx_plasma(n=48):
    pal = [_hue(i / 16, 0.85, 1) for i in range(16)]
    frames = []
    for f in range(n):
        t = f / n * TAU
        c = Canvas()
        for y in range(16):
            for x in range(16):
                v = (math.sin(x * 0.42 + t) + math.sin(y * 0.36 - t) +
                     math.sin((x + y) * 0.28 + t) + math.sin(math.hypot(x - 7.5, y - 7.5) * 0.55 - t)) / 4
                c.set(x, y, pal[int((v + 1) / 2 * 15.999)])
        frames.append(c)
    return anim(frames, 70, _("Ambient – {name}", name=_("Plasma")), ("fx", "plasma"))


def fx_fire(n=40):
    pal = _palette([(0, 0, 0), (90, 0, 0), (200, 30, 0), (255, 120, 0), (255, 210, 60), (255, 255, 200)])
    rng = random.Random(7)
    heat = [[0.0] * 16 for _ in range(18)]
    frames = []
    for f in range(n + 20):
        for x in range(16):
            heat[17][x] = 1.0 if rng.random() < 0.55 else rng.uniform(0.2, 0.5)
            heat[16][x] = (heat[17][x] + rng.uniform(0.4, 1.0)) / 2
        new = [[0.0] * 16 for _ in range(18)]
        new[17], new[16] = heat[17], heat[16]
        for y in range(16):
            for x in range(16):
                s = heat[y + 1][x] * 1.4 + heat[y + 1][(x - 1) % 16] + heat[y + 1][(x + 1) % 16] + heat[min(17, y + 2)][x] * 0.6
                new[y][x] = max(0.0, s / 4 - rng.uniform(0.015, 0.075))
        heat = new
        if f >= 20:
            c = Canvas()
            for y in range(16):
                for x in range(16):
                    c.set(x, y, pal[int(min(0.999, heat[y][x] * 1.1) * 15.999)])
            frames.append(c)
    return anim(frames, 70, _("Ambient – {name}", name=_("Fire")), ("fx", "fire"))


def fx_matrix(n=32):
    rng = random.Random(42)
    cols = [(rng.randrange(n), rng.choice((5, 6, 7, 8)), rng.choice((1, 2))) for _ in range(16)]
    frames = []
    for f in range(n):
        c = Canvas()
        for x, (off, length, speed) in enumerate(cols):
            head = (f * speed + off) % n - 8
            for k in range(length):
                y = head - k
                if 0 <= y < 16:
                    c.set(x, y, (200, 255, 200) if k == 0 else scale((0, 230, 70), 1 - k / length))
        frames.append(c)
    return anim(frames, 80, _("Ambient – {name}", name=_("Matrix")), ("fx", "matrix"))


def fx_warp(n=32):
    rng = random.Random(5)
    rays = [(rng.uniform(0, TAU), rng.randrange(n)) for _ in range(20)]
    frames = []
    for f in range(n):
        c = Canvas()
        for a, ph in rays:
            p = ((f + ph) % n) / n
            r = p * p * 10.5
            x, y = int(7.5 + r * math.cos(a) + 0.5), int(7.5 + r * math.sin(a) + 0.5)
            c.set(x, y, scale((200, 220, 255), min(1.0, 0.15 + p * 1.3)))
        frames.append(c)
    return anim(frames, 55, _("Ambient – {name}", name=_("Warp")), ("fx", "warp"))


def fx_aurora(n=48):
    pal = _palette([(0, 0, 10), (0, 60, 50), (0, 200, 120), (80, 255, 180), (160, 80, 255)])
    frames = []
    for f in range(n):
        t = f / n * TAU
        c = Canvas()
        for x in range(16):
            center = 6 + 3 * math.sin(x * 0.35 + t) + 1.5 * math.sin(x * 0.8 - 2 * t)
            for y in range(16):
                v = max(0.0, 1 - abs(y - center) / 4.5) * (0.6 + 0.4 * math.sin(x * 0.5 - t))
                c.set(x, y, pal[int(min(0.999, v) * 15.999)])
        for i, (sx, sy) in enumerate(((2, 14), (11, 13), (6, 15), (14, 11))):
            c.set(sx, sy, scale(WHITE, 0.2 + 0.8 * ease(f, n, i / 4)))
        frames.append(c)
    return anim(frames, 80, _("Ambient – {name}", name=_("Aurora")), ("fx", "aurora"))


def fx_life(n=60):
    rng = random.Random(11)
    grid = [[rng.random() < 0.33 for _ in range(16)] for _ in range(16)]
    age = [[0] * 16 for _ in range(16)]
    frames = []
    for _f in range(n):
        c = Canvas()
        for y in range(16):
            for x in range(16):
                if grid[y][x]:
                    c.set(x, y, _hue(0.45 + min(age[y][x], 10) / 25, 0.8, 1))
        frames.append(c)
        new = [[False] * 16 for _ in range(16)]
        for y in range(16):
            for x in range(16):
                nb = sum(grid[(y + dy) % 16][(x + dx) % 16] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy)
                new[y][x] = nb == 3 or (grid[y][x] and nb == 2)
                age[y][x] = age[y][x] + 1 if new[y][x] and grid[y][x] else 0
        if sum(map(sum, new)) < 12:
            new = [[rng.random() < 0.33 for _ in range(16)] for _ in range(16)]
        grid = new
    return anim(frames, 140, _("Ambient – {name}", name=_("Game of Life")), ("fx", "life"))


EFFECTS = {"plasma": ("Plasma", fx_plasma), "fire": ("Fire", fx_fire), "matrix": ("Matrix", fx_matrix),
           "warp": ("Warp", fx_warp), "aurora": ("Aurora", fx_aurora), "life": ("Game of Life", fx_life)}
_fx_cache = {}


def effect_names():
    return {k: _(v[0]) for k, v in EFFECTS.items()}


def clear_cache():
    """Labels are translated when a scene is built – rebuild after a language switch."""
    _fx_cache.clear()


def effect(name):
    if name not in EFFECTS:
        name = "plasma"
    if name not in _fx_cache:
        _fx_cache[name] = EFFECTS[name][1]()
    return _fx_cache[name]


# ======================================================================================
# Gallery – every scene with sample data, so the UI can show what the device can do
class _FakeTel:
    cpu_temp, gpu_temp, cpu_load, gpu_load, framerate = 63, 58, 41, 87, 144


GALLERY_CFG = {"cpu_warn": 80, "cpu_crit": 90, "gpu_warn": 78, "gpu_crit": 86, "fps_good": 60,
               "clock_color": [80, 200, 255], "clock_type": "animated"}


def gallery():
    rain = {"temp": 7, "code": 61, "is_day": True, "text": "Rain", "tomorrow": {"code": 0, "max": 12, "text": "Clear"}}
    snow = {"temp": -3, "code": 73, "is_day": True, "text": "Snow", "tomorrow": {"code": 0, "max": 2, "text": "Clear"}}
    night = {"temp": 4, "code": 0, "is_day": False, "text": "Clear", "tomorrow": {"code": 2, "max": 9, "text": "Partly cloudy"}}
    clk = clock(GALLERY_CFG, now=int(time.time()) // 60 * 60 - 0.5)  # a full minute of frames
    ft = [(6.9, 6.9)] * 9 + [(24.0, 7.0)] + [(7.1, 6.9)] * 4 + [(40.0, 7.0)] + [(7.0, 6.9)]
    items = [
        ("clock", _("Clock"), _("Big digits, seconds fill the sides"), clk),
        ("monitor", _("PC monitor"), _("CPU / GPU temperature and load, live"), monitor(_FakeTel, GALLERY_CFG)),
        ("game", _("Gaming HUD"), _("FPS, CPU/GPU temperature and frame-time graph"),
         game(_FakeTel, 144, GALLERY_CFG, "The Witcher 3", ft)),
        ("intro", _("Game start"), _("Animation when a game launches"), game_intro("Witcher 3")),
        ("weather", _("Weather – rain"), _("Drops falling at different speeds"), weather(rain, False)),
        ("weather_snow", _("Weather – snow"), _("Drifting snowflakes"), weather(snow, False)),
        ("weather_night", _("Clear night"), _("Moon and twinkling stars"), weather(night, False)),
        ("weather_sun", _("Tomorrow"), _("Tomorrow's forecast in the evening"), weather(rain, True)),
        ("ai_claude", _("Claude is working"), _("Orange spark, ring turns clockwise"), ai_working("claude")),
        ("ai_codex", _("Codex / ChatGPT is working"), _("Teal >_ prompt, ring turns counter-clockwise"), ai_working("codex")),
        ("ai_both", _("Both are working"), _("Claude and Codex take turns"), ai_working("claude", ["claude", "codex"])),
        ("ai_done", _("AI done"), _("Task finished"), ai_done("claude")),
        ("ai_attn", _("AI waiting"), _("The agent needs your answer"), ai_attention("codex")),
        ("ai_error", _("Error"), _("Something went wrong"), ai_error("codex")),
        ("hot", _("Overheating"), _("High temperature warning"), overheat("CPU", 92)),
        ("pomodoro", _("Pomodoro"), _("Focus countdown with a shrinking frame"), pomodoro(18 * 60 + 30, 25 * 60, "focus", False)),
        ("text", _("Scrolling text"), _("Your own message, rainbow too"), scrolling_text(_("HELLO") + " DITOO", rainbow=True)),
        ("notify", _("Notification"), _("Messages from GitHub, tests, scripts"), notify("BUILD OK", (60, 220, 130))),
        ("viz", _("Visualizer"), _("Reacts to music (built into Ditoo)"), visualizer()),
    ]
    for k, (title, _fn) in EFFECTS.items():
        items.append(("fx_" + k, _(title), _("Ambient effect"), effect(k)))
    return items

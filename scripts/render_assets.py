"""Render README visuals straight from the real scenes: LED-style GIFs and a hero banner.

    python scripts/render_assets.py        → docs/assets/*.gif, *.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ditoo_control import i18n, scenes  # noqa: E402

OUT = ROOT / "docs" / "assets"
BG = (11, 12, 16)
OFF = (22, 23, 30)
FONT_DIR = Path("C:/Windows/Fonts")


def font(size, bold=False):
    for name in (("segoeuib.ttf", "seguisb.ttf") if bold else ("segoeui.ttf",)):
        p = FONT_DIR / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def led(frame, cell=14, pad=10, radius=4):
    """One 16x16 frame drawn like the real panel: rounded LEDs with dark gaps."""
    size = 16 * cell + 2 * pad
    img = Image.new("RGB", (size, size), (5, 5, 7))
    d = ImageDraw.Draw(img)
    g = max(2, cell // 6)
    for y in range(16):
        for x in range(16):
            c = tuple(frame[y * 16 + x])
            if sum(c) <= 12:
                c = OFF
            x0, y0 = pad + x * cell + g // 2, pad + y * cell + g // 2
            d.rounded_rectangle((x0, y0, x0 + cell - g, y0 + cell - g), radius, fill=c)
    return img


def save_gif(path, images, durations):
    images[0].save(path, save_all=True, append_images=images[1:], duration=durations, loop=0, optimize=True, disposal=2)


def scene_gif(name, sc, cell=14, max_frames=60, speed=1.0):
    frames, ms = sc["frames"][:max_frames], sc["ms"][:max_frames]
    imgs = [led(f, cell) for f in frames]
    save_gif(OUT / f"{name}.gif", imgs, [max(40, int(m / speed)) for m in ms])


class Tel:
    def __init__(self, ct, gt, cl, gl):
        self.cpu_temp, self.gpu_temp, self.cpu_load, self.gpu_load = ct, gt, cl, gl


CFG = {"cpu_warn": 80, "cpu_crit": 90, "gpu_warn": 78, "gpu_crit": 86, "fps_good": 60,
       "clock_color": [80, 200, 255], "clock_type": "animated"}


def hud_frames():
    """A live-looking HUD: FPS and frame-time history moving like in a real session."""
    import math
    out, hist = [], []
    for i in range(24):
        fps = 141 + 6 * math.sin(i / 3)
        ft = 1000 / fps
        spike = i in (9, 18)
        hist.append((ft * (3.2 if spike else 1), ft))
        out.append(scenes.game(Tel(63 + (i > 12), 58 + (i > 6), 41 + 8 * math.sin(i / 4), 92), 60 if spike else fps,
                               CFG, "Witcher 3", hist[-16:])["frames"][0])
    return out


def strip(items, path, cell=9, caption=True):
    """Hero banner: a row of animated panels with captions."""
    n_frames = 48
    panel = 16 * cell + 20
    gap, top, bottom = 28, 26, 58 if caption else 26
    width = len(items) * panel + (len(items) - 1) * gap + 80
    height = top + panel + bottom
    f_title = font(17, bold=True)
    pages = []
    for i in range(n_frames):
        img = Image.new("RGB", (width, height), BG)
        d = ImageDraw.Draw(img)
        for j, (title, frames) in enumerate(items):
            x = 40 + j * (panel + gap)
            d.rounded_rectangle((x - 8, top - 8, x + panel + 8, top + panel + 8), 18, fill=(30, 32, 40))
            img.paste(led(frames[i % len(frames)], cell, pad=10, radius=3), (x, top))
            if caption:
                tw = d.textlength(title, font=f_title)
                d.text((x + (panel - tw) / 2, top + panel + 20), title, font=f_title, fill=(200, 204, 216))
        pages.append(img.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    save_gif(path, pages, [90] * n_frames)


def resample(sc, n=48):
    """Spread any scene over n display frames (respecting its own timing) for side-by-side banners."""
    frames, ms = sc["frames"], sc["ms"]
    total = sum(ms)
    out, t = [], 0
    for i in range(n):
        t = (i * 90) % total
        acc = 0
        for f, m in zip(frames, ms, strict=True):
            acc += m
            if acc > t:
                out.append(f)
                break
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    i18n.set_lang("en")
    g = {k: sc for k, _t, _d, sc in scenes.gallery()}
    hud = hud_frames()
    save_gif(OUT / "hud.gif", [led(f) for f in hud], [500] * len(hud))
    clock_fast = dict(g["clock"], ms=[150] * len(g["clock"]["frames"]))
    scene_gif("clock", clock_fast)
    scene_gif("monitor", g["monitor"])
    for key in ("weather", "weather_snow", "weather_night", "ai_claude", "ai_codex", "ai_both", "ai_done", "ai_attn",
                "fx_fire", "fx_plasma", "fx_matrix", "fx_aurora", "fx_life", "intro", "hot", "notify"):
        scene_gif(key.replace("fx_", ""), g[key])
    pomo = scenes.pomodoro(25 * 60 - 1, 25 * 60, "focus", False)
    scene_gif("pomodoro", dict(pomo, ms=[120] * len(pomo["frames"])))
    strip([("Gaming HUD", hud[:24] * 2), ("Claude working", resample(g["ai_claude"])), ("Weather", resample(g["weather"])),
           ("Clock", resample(clock_fast)), ("Ambient", resample(g["fx_aurora"]))], OUT / "hero.gif")
    # still preview for social cards
    led(hud[5], cell=24, pad=20, radius=6).save(OUT / "hud.png")
    print("assets written to", OUT)


if __name__ == "__main__":
    main()

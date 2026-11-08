"""Settings: defaults, load/save and mode metadata."""
import copy
import json
import os

from .i18n import _

APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DitooControl")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
MEDIA_DIR = os.path.join(APP_DIR, "media")

MODES = ["auto", "clock", "monitor", "game", "weather", "ai", "pomodoro", "ambient", "text", "media",
         "visualizer", "lamp", "off"]
_MODE_NAMES = {"auto": "Automatic", "clock": "Clock", "monitor": "PC monitor", "game": "Gaming",
               "weather": "Weather", "ai": "AI agents", "pomodoro": "Pomodoro", "ambient": "Ambient",
               "text": "Text", "media": "Image / GIF", "visualizer": "Visualizer", "lamp": "Lamp", "off": "Off"}
_CONTEXT_NAMES = {"game": "Gaming", "ai": "Working with AI", "desk": "Idle"}

# Screens reachable with the "previous / next" hotkeys, per context
CONTEXT_CYCLES = {
    "game": ["game", "monitor", "clock", "weather"],
    "ai": ["ai", "pomodoro", "clock", "monitor", "weather", "ambient"],
    "desk": ["clock", "weather", "monitor", "ambient", "ai", "pomodoro", "visualizer"],
}


def mode_label(mode):
    return _(_MODE_NAMES.get(mode, mode))


def context_label(ctx):
    return _(_CONTEXT_NAMES.get(ctx, ctx))


DEFAULTS = {
    "lang": "auto",                 # auto | en | cs
    "mac": "",                      # empty = find the paired Ditoo automatically
    "port": 2,
    "mode": "auto",
    "brightness": 70,
    "night": {"enabled": True, "start": 23, "end": 7, "brightness": 15},   # brightness 0 = display off
    "away": {"enabled": True, "minutes": 10, "on_lock": True},           # display off while you're away
    "clock_color": [80, 200, 255],
    "clock_style": 0,
    "clock_type": "animated",
    "effect": "plasma",
    "text": "HELLO",
    "text_color": [255, 255, 255],
    "text_rainbow": False,
    "lamp_color": [255, 150, 60],
    "media": "",
    "city": "",
    "lat": None,
    "lon": None,
    "idle": {"clock": 40, "weather": 10, "monitor": 10, "ambient": 0},
    "rules": {"alerts": True, "games": True, "ai": True, "pomodoro": True, "intro": True, "ai_over_game": False},
    "cpu_warn": 80, "cpu_crit": 90, "gpu_warn": 78, "gpu_crit": 86,
    "fps_good": 60,
    "auto_detect_games": True,
    "games": [
        {"exe": "witcher3.exe", "name": "The Witcher 3"},
        {"exe": "cyberpunk2077.exe", "name": "Cyberpunk 2077"},
        {"exe": "bg3.exe", "name": "Baldur's Gate 3"},
        {"exe": "bg3_dx11.exe", "name": "Baldur's Gate 3"},
        {"exe": "eldenring.exe", "name": "Elden Ring"},
        {"exe": "cs2.exe", "name": "Counter-Strike 2"},
        {"exe": "valorant-win64-shipping.exe", "name": "Valorant"},
        {"exe": "fortniteclient-win64-shipping.exe", "name": "Fortnite"},
        {"exe": "minecraft.windows.exe", "name": "Minecraft"},
        {"exe": "rdr2.exe", "name": "Red Dead Redemption 2"},
        {"exe": "helldivers2.exe", "name": "Helldivers 2"},
        {"exe": "r5apex.exe", "name": "Apex Legends"},
    ],
    "ignore_apps": ["explorer.exe", "chrome.exe", "msedge.exe", "firefox.exe", "discord.exe", "claude.exe",
                    "code.exe", "steamwebhelper.exe", "eacefsubprocess.exe", "easteamproxy.exe",
                    "icloudhome.exe", "spotify.exe", "obs64.exe", "msiafterburner.exe", "applicationframehost.exe",
                    "ditoocontrol.exe", "msedgewebview2.exe"],
    "sound": {"enabled": True, "volume": 0.7, "mute_in_game": True, "quiet_night": True,
              "events": {"done": True, "attention": True, "error": True, "game": False,
                         "pomodoro": True, "alert": True, "notify": True}},
    "pomodoro": {"focus": 25, "break": 5},
    "http_port": 7777,
    "setup_done": False,            # first-run wizard finished
    "hotkeys": {"enabled": True, "prev": "A", "next": "D", "auto": "S", "bright": "W"},
}

# keys whose value is a list – a patch replaces them instead of merging
LIST_KEYS = {"games", "ignore_apps", "clock_color", "text_color", "lamp_color"}


def merge(base, extra):
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = merge(DEFAULTS, json.load(f))
    except (OSError, ValueError):
        cfg = copy.deepcopy(DEFAULTS)
    if cfg["mode"] not in MODES:
        cfg["mode"] = "auto"
    return cfg


def save(cfg):
    os.makedirs(APP_DIR, exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_PATH)

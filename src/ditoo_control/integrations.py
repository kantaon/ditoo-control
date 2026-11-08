"""One-click integrations: Claude Code hooks, Codex notify, Windows autostart, Start-menu shortcut.

Every change makes a timestamped backup first and only touches entries that belong to
Ditoo Control, so turning an integration off leaves the rest of your config intact.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

from .i18n import _

HERE = os.path.dirname(os.path.abspath(__file__))
NOTIFY = os.path.join(HERE, "notify.py")
FROZEN = getattr(sys, "frozen", False)          # running as the packaged DitooControl.exe
# anything containing one of these belongs to us (incl. commands written by older versions)
MARKERS = ("ditoo_notify.py", "ditoo_control", "ditoocontrol.exe")

CLAUDE_SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
CODEX_CONFIG = os.path.join(os.path.expanduser("~"), ".codex", "config.toml")
_PROGRAMS = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
STARTUP_LNK = os.path.join(_PROGRAMS, "Startup", "Ditoo Control.lnk")
START_MENU_LNK = os.path.join(_PROGRAMS, "Ditoo Control.lnk")
CLAUDE_HOOKS = ["UserPromptSubmit", "Notification", "Stop", "SessionEnd"]  # no per-tool hooks: keep Claude fast


def _ours(text):
    t = str(text).lower()
    return any(m in t for m in MARKERS)


def _python(windowless=False):
    exe = sys.executable
    if windowless:
        w = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(w):
            return w
    return exe


def notify_argv(windowless=False):
    """How to run the notify bridge: the bundled exe, or Python + notify.py."""
    if FROZEN:
        return [sys.executable, "--notify"]
    return [_python(windowless), NOTIFY]


def app_argv():
    """How to start the app windowless (autostart / Start menu)."""
    if FROZEN:
        return sys.executable, ""
    return _python(windowless=True), "-m ditoo_control"


def _backup(path):
    if os.path.exists(path):
        shutil.copy2(path, f"{path}.bak-{time.strftime('%Y%m%d-%H%M%S')}")


def _quote(argv):
    return " ".join(f'"{a}"' if " " in a or "\\" in a else a for a in argv)


# ---------------------------------------------------------------- Claude Code
def claude_command():
    return _quote(notify_argv()) + " claude"


def claude_status():
    try:
        with open(CLAUDE_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False
    hooks = data.get("hooks", {})
    return any(_ours(h.get("command", "")) for ev in CLAUDE_HOOKS
               for m in hooks.get(ev, []) for h in m.get("hooks", []))


def claude_set(enable):
    data = {}
    if os.path.exists(CLAUDE_SETTINGS):
        with open(CLAUDE_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)  # refuse to touch a file we can't parse
    _backup(CLAUDE_SETTINGS)
    hooks = data.setdefault("hooks", {})
    for ev in set(CLAUDE_HOOKS) | set(hooks):
        matchers = hooks.get(ev, [])
        for m in matchers:
            m["hooks"] = [h for h in m.get("hooks", []) if not _ours(h.get("command", ""))]
        matchers = [m for m in matchers if m.get("hooks")]
        if enable and ev in CLAUDE_HOOKS:
            matchers.append({"hooks": [{"type": "command", "command": claude_command(), "timeout": 5}]})
        if matchers:
            hooks[ev] = matchers
        else:
            hooks.pop(ev, None)
    if not hooks:
        data.pop("hooks", None)
    os.makedirs(os.path.dirname(CLAUDE_SETTINGS), exist_ok=True)
    with open(CLAUDE_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return claude_status()


# ---------------------------------------------------------------- Codex
def _toml_array(items):
    return "[" + ", ".join(json.dumps(s, ensure_ascii=False) for s in items) + "]"


def _current_notify(text):
    """Top-level ``notify`` array from config.toml (or None)."""
    import tomllib
    try:
        val = tomllib.loads(text).get("notify")
    except tomllib.TOMLDecodeError as e:
        raise RuntimeError(_("Can't read ~/.codex/config.toml: {err}", err=e)) from e
    return val if isinstance(val, list) else None


def codex_status():
    try:
        with open(CODEX_CONFIG, encoding="utf-8") as f:
            return any(_ours(s) for s in (_current_notify(f.read()) or []))
    except (OSError, RuntimeError):
        return False


def codex_set(enable):
    """Codex allows a single notify command. If one exists (the Codex app uses it for its own
    computer-use helper) we keep it working by chaining: ours runs first, then forwards."""
    text = ""
    if os.path.exists(CODEX_CONFIG):
        with open(CODEX_CONFIG, encoding="utf-8") as f:
            text = f.read()
    current = _current_notify(text)
    original = None
    if current and any(_ours(s) for s in current):
        if "--chain" in current:
            original = current[current.index("--chain") + 1:]
    elif current:
        original = current
    if enable:
        cmd = notify_argv(windowless=True) + ["codex"] + (["--chain"] + original if original else [])
        new_line = "notify = " + _toml_array(cmd)
    else:
        new_line = ("notify = " + _toml_array(original)) if original else None
    lines = text.splitlines()
    idx = next((i for i, line in enumerate(lines) if re.match(r"\s*notify\s*=", line)), None)
    if idx is not None:
        end = idx  # a multi-line array continues until the closing bracket
        while "]" not in lines[end] and end + 1 < len(lines):
            end += 1
        del lines[idx:end + 1]
    else:
        idx = next((i for i, line in enumerate(lines) if line.strip().startswith("[")), len(lines))
    if new_line:
        lines.insert(idx, new_line)  # above the first [table] → stays a top-level key
    new_text = "\n".join(lines) + "\n"
    _current_notify(new_text)  # validate before writing
    _backup(CODEX_CONFIG)
    os.makedirs(os.path.dirname(CODEX_CONFIG), exist_ok=True)
    with open(CODEX_CONFIG, "w", encoding="utf-8") as f:
        f.write(new_text)
    return codex_status()


# ---------------------------------------------------------------- shortcuts
def _shortcut(path, args_extra=""):
    target, args = app_argv()
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:LNK);"
          "$s.TargetPath=$env:TGT;$s.Arguments=$env:ARGS;$s.WorkingDirectory=$env:WD;"
          "$s.IconLocation=$env:ICO;$s.Description='Ditoo Control';$s.Save()")
    icon = sys.executable if FROZEN else os.path.join(HERE, "ui", "icon.ico")
    env = dict(os.environ, LNK=path, TGT=target, ARGS=f"{args} {args_extra}".strip(),
               WD=os.path.dirname(target) if FROZEN else os.path.dirname(HERE), ICO=icon)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], env=env, check=True,
                   creationflags=0x08000000, timeout=20)


def autostart_status():
    return os.path.exists(STARTUP_LNK)


def autostart_set(enable):
    if enable:
        _shortcut(STARTUP_LNK, "--hidden")
    elif os.path.exists(STARTUP_LNK):
        os.remove(STARTUP_LNK)
    return autostart_status()


def start_menu_status():
    return os.path.exists(START_MENU_LNK)


def start_menu_set(enable):
    if enable:
        _shortcut(START_MENU_LNK)
    elif os.path.exists(START_MENU_LNK):
        os.remove(START_MENU_LNK)
    return start_menu_status()


def status():
    return {"claude": claude_status(), "codex": codex_status(), "autostart": autostart_status(),
            "start_menu": start_menu_status(),
            "claude_command": claude_command(), "notify_command": _quote(notify_argv()),
            "claude_installed": os.path.isdir(os.path.dirname(CLAUDE_SETTINGS)),
            "codex_installed": os.path.isdir(os.path.dirname(CODEX_CONFIG))}


SETTERS = {"claude": claude_set, "codex": codex_set, "autostart": autostart_set, "start_menu": start_menu_set}

"""Report UI / backend strings that have no translation in a catalogue.

    python scripts/check_i18n.py          # exit code 1 if something is missing
"""
import ast
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "ditoo_control"
UI = PKG / "ui"
LANGS = ["cs"]

# strings that are the same in every language
SAME = {"Ditoo Control", "Ditoo Pro", "FPS", "fps", "CPU", "GPU", "Auto", "English", "Čeština", "Claude Code", "OpenAI Codex",
        "Claude", "Codex", "Pomodoro", "Bluetooth", "PC monitor", "Matrix", "Warp", "Game of Life", "Ambient", "Text",
        "intro", "Test", "C", "Cx", "OK", "AI", "(i)", "i", "/", "+", "—", ", anything.", "Ctrl", "Shift", "Alt",
        "Codex / ChatGPT", "CPU / GPU", "MIN", "II", "Ctrl + Shift + Alt + ",
        "70 %", "TESTS PASSED", "gh run watch", "use strict", "callout hidden", ".nav button",
        "Kantaon", "Kantaon · github.com/kantaon", "github.com/kantaon", "github.com/kantaon/ditoo-control"}


class Texts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = set(), 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg", "symbol"):
            self.skip += 1
        for k, v in attrs:
            if k in ("placeholder", "aria-label", "title", "data-help") and v:
                self.out.add(v.strip())

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg", "symbol"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.out.add(data.strip())


def js_catalog(lang):
    src = (UI / "i18n.js").read_text(encoding="utf-8")
    block = re.search(rf"\b{lang}: \{{(.*?)\n  \}},", src, re.S).group(1)
    keys = set()
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)":', block):
        keys.add(json.loads(f'"{m.group(1)}"'))
    return keys


def js_strings():
    src = (UI / "app.js").read_text(encoding="utf-8")
    found = set()
    for m in re.finditer(r'"((?:[^"\\\n]|\\.)*)"', src):
        s = json.loads(f'"{m.group(1)}"')
        if s == s.strip() and re.search(r"[A-Za-z]{2}", s) and " " in s and not re.search(r"[#{}<>=;]|^/|https?:|\$\{|\.(js|png|exe)$", s.replace("{", "").replace("}", "")) \
                and not s.startswith(("background", "rgb", "btn", "chip", "tile", "card", "dot ", "g-", "wz-", "badge", "hk", "mode")):
            found.add(s)
    for m in re.finditer(r'\bt\("((?:[^"\\]|\\.)*)"', src):
        found.add(json.loads(f'"{m.group(1)}"'))
    return found


def py_strings():
    found = set()
    for f in PKG.glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_" and node.args \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                found.add(node.args[0].value)
    return found


def main():
    sys.path.insert(0, str(ROOT / "src"))
    from ditoo_control import i18n, weather
    p = Texts()
    p.feed((UI / "index.html").read_text(encoding="utf-8"))
    ui = (p.out | js_strings()) - SAME
    backend = (py_strings() | set(weather.WMO.values())) - SAME
    missing = 0
    for lang in LANGS:
        cat = js_catalog(lang)
        for s in sorted(ui - cat):
            print(f"[ui:{lang}] {s}")
            missing += 1
        for s in sorted(backend - set(i18n.CS)):
            print(f"[py:{lang}] {s}")
            missing += 1
    print(f"{missing} missing")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

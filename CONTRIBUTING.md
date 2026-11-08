# Contributing

Thanks for wanting to make Ditoo Control better! Bug reports, new scenes, translations and fixes are all welcome.

## Getting started

```bash
git clone https://github.com/kantaon/ditoo-control
cd ditoo-control
pip install -e ".[dev]"
pythonw -m ditoo_control          # run the app
python -m ditoo_control --server  # engine + API only, UI at http://127.0.0.1:7777
```

Before opening a pull request:

```bash
ruff check .
pytest
python scripts/check_i18n.py
```

## Where things live

| Path | What |
|---|---|
| `src/ditoo_control/engine.py` | decides what the display shows (rules, hotkeys, device worker) |
| `src/ditoo_control/scenes.py` | every screen – pure functions returning 16 × 16 frames |
| `src/ditoo_control/ditoo.py` | Bluetooth driver, see [docs/PROTOCOL.md](docs/PROTOCOL.md) |
| `src/ditoo_control/sensors.py` | Afterburner / RivaTuner shared memory, Windows counters, NVML |
| `src/ditoo_control/server.py`, `ui/` | local API and the desktop UI |
| `src/ditoo_control/integrations.py`, `notify.py` | Claude Code, Codex, shortcuts |

## Adding a scene

1. Write a function in `scenes.py` that returns `anim(...)` or `still(...)`.
2. Keep it pixel-exact: symmetric layouts, whole-pixel motion, loops whose frame count is a multiple of every motion period.
3. Add it to `gallery()` so it shows up in the app and gets tested.
4. `pytest` checks validity and centring automatically; `python scripts/render_assets.py` renders a GIF to look at.

## Translations

UI and backend strings are English. Add a language with a catalogue in `src/ditoo_control/i18n.py` and `src/ditoo_control/ui/i18n.js`, and add its code to `SUPPORTED` / the language switch. `scripts/check_i18n.py` reports missing strings.

## Releases

Bump `__version__` in `src/ditoo_control/__init__.py`, add a `CHANGELOG.md` entry and push a `vX.Y.Z` tag – GitHub Actions builds the installer and the portable zip.

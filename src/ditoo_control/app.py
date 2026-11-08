"""Ditoo Control – desktop entry point.

  ditoo-control                  open the window (also: pythonw -m ditoo_control)
  ditoo-control --hidden         start in the tray (used by autostart)
  ditoo-control --server         headless: engine + local API, no window (development)
  ditoo-control --notify ARGS…   run the hook bridge (used by the packaged .exe)
"""
import argparse
import ctypes
import json
import os
import sys
import threading
import urllib.request
import webbrowser

from . import __version__


def _be_light():
    """Stay out of the way of games: below-normal priority + Windows EcoQoS power throttling."""
    try:
        k32 = ctypes.windll.kernel32
        proc = k32.GetCurrentProcess()
        k32.SetPriorityClass(proc, 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS

        class PowerThrottling(ctypes.Structure):
            _fields_ = [("Version", ctypes.c_ulong), ("ControlMask", ctypes.c_ulong), ("StateMask", ctypes.c_ulong)]
        s = PowerThrottling(1, 0x1, 0x1)  # EXECUTION_SPEED throttling on
        k32.SetProcessInformation(proc, 4, ctypes.byref(s), ctypes.sizeof(s))  # ProcessPowerThrottling
    except Exception:
        pass


def _api(port, path, post=False, timeout=2):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=b"{}" if post else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


class App:
    def __init__(self, hidden=False, headless=False):
        from .engine import Engine
        self.hidden, self.headless = hidden, headless
        self.engine = Engine()
        self.port = self.engine.cfg.get("http_port", 7777)
        self.window = None
        self.tray = None
        self.quitting = False

    # ------------------------------------------------------------------ window
    def show(self):
        if self.window:
            self.window.show()
            self.window.restore()
        else:
            webbrowser.open(f"http://127.0.0.1:{self.port}/")

    def _on_closing(self):
        if self.quitting:
            return True
        self.window.hide()  # keep running in the tray
        return False

    def quit(self):
        self.quitting = True
        try:
            if self.tray:
                self.tray.stop()
        except Exception:
            pass
        self.engine.stop()
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
        os._exit(0)

    # ------------------------------------------------------------------ tray
    def _tray(self):
        try:
            import pystray
        except ImportError:
            return
        from .config import MODES, mode_label
        from .i18n import _
        from .icon import render
        e = self.engine

        def mode_item(m):
            return pystray.MenuItem(lambda _i, m=m: mode_label(m), lambda *_a: e.set_mode(m),
                                    checked=lambda _i, m=m: e.cfg["mode"] == m, radio=True)

        def toggle_sound(*_a):
            e.update_config({"sound": {"enabled": not e.cfg["sound"]["enabled"]}})

        menu = pystray.Menu(
            pystray.MenuItem(lambda _i: _("Open Ditoo Control"), lambda *_a: self.show(), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda _i: _("Mode"), pystray.Menu(*[mode_item(m) for m in MODES])),
            pystray.MenuItem(lambda _i: _("Sounds"), toggle_sound, checked=lambda _i: e.cfg["sound"]["enabled"]),
            pystray.MenuItem(lambda _i: _("Reconnect Ditoo"), lambda *_a: e.device.reconnect()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda _i: _("Quit"), lambda *_a: self.quit()),
        )
        self.tray = pystray.Icon("DitooControl", render(64), "Ditoo Control", menu)
        self.tray.run_detached()

    # ------------------------------------------------------------------ run
    def run(self):
        from . import server
        try:
            server.serve(self.engine, self, self.port)
        except OSError:
            try:  # already running → bring that instance to the front
                if _api(self.port, "/api/ping").get("app") == "ditoo-control":
                    _api(self.port, "/api/show", post=True)
            except Exception:
                pass
            return
        _be_light()
        self.engine.start()
        if self.headless:
            threading.Event().wait()
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DitooControl.App")
        except Exception:
            pass
        self._tray()
        try:
            import webview
        except ImportError:
            if not self.hidden:
                webbrowser.open(f"http://127.0.0.1:{self.port}/")
            threading.Event().wait()
            return
        from .config import APP_DIR
        self.window = webview.create_window(
            "Ditoo Control", f"http://127.0.0.1:{self.port}/", width=1280, height=860,
            min_size=(960, 640), background_color="#0B0C10", hidden=self.hidden, text_select=False)
        self.window.events.closing += self._on_closing
        webview.start(gui="edgechromium", private_mode=False, storage_path=os.path.join(APP_DIR, "webview"))
        if not self.quitting:
            self.quit()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--notify"]:
        from . import notify
        notify.main(["notify"] + argv[1:])
        return
    ap = argparse.ArgumentParser(prog="ditoo-control", description="Make a Divoom Ditoo Pro react to your PC.")
    ap.add_argument("--hidden", action="store_true", help="start minimised to the tray")
    ap.add_argument("--server", action="store_true", help="run headless (engine + local API only)")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)
    App(hidden=args.hidden, headless=args.server).run()


if __name__ == "__main__":
    main()

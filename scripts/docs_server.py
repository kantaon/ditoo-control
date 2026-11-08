"""Demo instance for documentation screenshots: temporary settings, no Bluetooth, sample activity.

    python scripts/docs_server.py [port] [lang]
"""
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

os.environ["APPDATA"] = tempfile.mkdtemp(prefix="ditoo-docs-")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ditoo_control import config, server  # noqa: E402
from ditoo_control.engine import Engine  # noqa: E402

port = int(sys.argv[1]) if len(sys.argv) > 1 else 7788
lang = sys.argv[2] if len(sys.argv) > 2 else "en"
cfg = config.merge(config.DEFAULTS, {"lang": lang, "setup_done": True, "city": "Prague", "lat": 50.0755, "lon": 14.4378,
                                     "mac": "AA:BB:CC:DD:EE:FF", "away": {"enabled": False}})
config.save(cfg)

e = Engine()
e.device.status = "connected"          # pretend: screenshots must not touch real hardware
e.device.start = lambda: None
threading.Thread(target=e._loop, daemon=True).start()
threading.Thread(target=e._weather_loop, daemon=True).start()
server.serve(e, None, port)

e.log("Ditoo Control started")
e.log("Connected to AA:BB:CC:DD:EE:FF (channel 2)")
e.ai_event("codex", "done", "Refactored the parser")
time.sleep(0.2)
e.ai_event("claude", "working")
print(f"docs server on http://127.0.0.1:{port}/", flush=True)
threading.Event().wait()

"""Local HTTP API on 127.0.0.1 – serves the UI and receives hook events.

Security model (local-only app, no login):
- binds to 127.0.0.1 and rejects foreign Host headers (DNS rebinding);
- rejects browser requests coming from other websites (Sec-Fetch-Site) so a web page
  can't trigger anything, while curl / scripts / hooks keep working;
- state-changing POSTs require a JSON body (forces a CORS preflight we never answer);
- static files are served only from the bundled ui/ folder and the media folder.
"""
import base64
import json
import mimetypes
import os
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __author__, __author_url__, __repo__, __version__, i18n, integrations, scenes, sounds
from . import weather as weather_mod
from .config import APP_DIR, DEFAULTS, MEDIA_DIR, MODES, mode_label
from .engine import MEDIA_EXT, encode_scene
from .i18n import _

UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
ALLOWED_HOSTS = re.compile(r"^(127\.0\.0\.1|localhost)(:\d+)?$")
MAX_UPLOAD = 20 * 1024 * 1024
OPEN_TARGETS = {
    "bluetooth": "ms-settings:bluetooth",
    "sound": "ms-settings:sound",
    "afterburner": "https://www.msi.com/Landing/afterburner/graphics-cards",
    "rtss": "https://www.guru3d.com/download/rtss-rivatuner-statistics-server-download/",
    "webview2": "https://developer.microsoft.com/microsoft-edge/webview2/",
    "author": __author_url__,
    "repo": __repo__,
    "issues": __repo__ + "/issues",
    "media": "dir:media",
    "config": "dir:config",
}
_gallery = {"rev": None, "items": None}
_gallery_lock = threading.Lock()


def gallery_payload(lang_rev):
    with _gallery_lock:
        if _gallery["rev"] != lang_rev:
            _gallery["items"] = [{"id": k, "title": t, "desc": d, **encode_scene(sc)}
                                 for k, t, d, sc in scenes.gallery()]
            _gallery["rev"] = lang_rev
        return _gallery["items"]


def _inside(base, path):
    base, path = os.path.realpath(base), os.path.realpath(path)
    return os.path.commonpath([base, path]) == base


def sanitize_patch(patch):
    """Only known settings, with the type of the default value."""
    out = {}
    for k, v in (patch or {}).items():
        if k not in DEFAULTS:
            continue
        d = DEFAULTS[k]
        same_kind = isinstance(v, type(d)) or (isinstance(d, (int, float)) and isinstance(v, (int, float)))
        if d is None or same_kind:
            out[k] = v
    return out


class Handler(BaseHTTPRequestHandler):
    engine = None
    app = None
    server_version = f"DitooControl/{__version__}"
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    # ------------------------------------------------------------------ plumbing
    def _allowed(self):
        if not ALLOWED_HOSTS.match(self.headers.get("Host", "")):
            return False
        site = self.headers.get("Sec-Fetch-Site")
        return site in (None, "same-origin", "none")

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if not isinstance(body, (bytes, bytearray)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if ctype.startswith("text/html"):
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
                             "connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_UPLOAD * 1.4:
            raise ValueError("request too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def _file(self, base, rel):
        path = os.path.join(base, rel)
        if not _inside(base, path) or not os.path.isfile(path):
            return self._send(404, {"error": "not found"})
        with open(path, "rb") as f:
            data = f.read()
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith(("javascript", "json")):
            ctype += "; charset=utf-8"
        self._send(200, data, ctype)

    # ------------------------------------------------------------------ GET
    def do_GET(self):
        if not self._allowed():
            return self._send(403, {"error": "forbidden"})
        u = urllib.parse.urlparse(self.path)
        q = {k: v[-1] for k, v in urllib.parse.parse_qs(u.query).items()}
        e, p = self.engine, u.path
        if p in ("/", "/index.html"):
            return self._file(UI_DIR, "index.html")
        if p.startswith("/ui/"):
            return self._file(UI_DIR, urllib.parse.unquote(p[4:]))
        if p.startswith("/media/"):
            return self._file(MEDIA_DIR, os.path.basename(urllib.parse.unquote(p[7:])))
        if p == "/api/ping":
            return self._send(200, {"ok": True, "app": "ditoo-control", "version": __version__})
        if p == "/api/state":
            return self._send(200, e.state())
        if p == "/api/preview":
            return self._send(200, e.preview())
        if p == "/api/config":
            return self._send(200, {
                "config": e.cfg, "version": __version__, "lang": i18n.LANG, "author": __author__, "repo": __repo__,
                "modes": [{"id": m, "label": mode_label(m)} for m in MODES],
                "effects": scenes.effect_names(),
                "sounds": {k: _(v[0]) for k, v in sounds.SOUNDS.items()},
                "integrations": integrations.status()})
        if p == "/api/gallery":
            return self._send(200, gallery_payload(e.lang_rev))
        if p == "/api/geocode":
            try:
                return self._send(200, weather_mod.geocode(q.get("q", "")[:80], i18n.LANG))
            except Exception as ex:
                return self._send(502, {"error": str(ex)})
        # hook endpoints accept GET so tiny scripts / curl / hooks can call them
        if p == "/api/ai":
            ok = e.ai_event(q.get("source", "agent"), q.get("state", ""), q.get("detail", ""))
            return self._send(200 if ok else 400, {"ok": ok})
        if p == "/api/notify":
            color = q.get("color", "ffc800")
            if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
                color = "ffc800"
            ok = e.notify(q.get("text", ""), tuple(int(color[i:i + 2], 16) for i in (0, 2, 4)),
                          sound=q.get("sound", "1") != "0")
            return self._send(200 if ok else 400, {"ok": ok})
        return self._send(404, {"error": "not found"})

    # ------------------------------------------------------------------ POST
    def do_POST(self):
        if not self._allowed():
            return self._send(403, {"error": "forbidden"})
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            return self._send(415, {"error": "json required"})
        e = self.engine
        p = urllib.parse.urlparse(self.path).path
        try:
            body = self._json()
            if p == "/api/mode":
                if not e.set_mode(body.get("mode")):
                    return self._send(400, {"error": "unknown mode"})
            elif p == "/api/config":
                e.update_config(sanitize_patch(body))
            elif p == "/api/device":
                (e.device.reconnect if body.get("action") == "connect" else e.device.disconnect)()
            elif p == "/api/pomodoro":
                e.pomodoro_action(body.get("action"))
            elif p == "/api/try":
                if not e.try_scene(body.get("id"), int(body.get("seconds", 12))):
                    return self._send(404, {"error": "unknown scene"})
            elif p == "/api/notify":
                color = body.get("color", (255, 200, 0))
                if not (isinstance(color, list) and len(color) == 3):
                    color = (255, 200, 0)
                e.notify(str(body.get("text", "")), tuple(max(0, min(255, int(c))) for c in color))
            elif p == "/api/ai":
                e.ai_event(body.get("source", "agent"), body.get("state", ""), body.get("detail", ""))
            elif p == "/api/sound":
                if body.get("name") in sounds.SOUNDS:
                    e.sound(body["name"], force=True)
            elif p == "/api/media":
                return self._upload(body)
            elif p == "/api/media/delete":
                name = os.path.basename(str(body.get("name", "")))
                path = os.path.join(MEDIA_DIR, name)
                if name and _inside(MEDIA_DIR, path) and os.path.isfile(path):
                    os.remove(path)
                e.media_cache.pop(name, None)
            elif p == "/api/integration":
                fn = integrations.SETTERS.get(body.get("kind"))
                if not fn:
                    return self._send(404, {"error": "unknown integration"})
                fn(bool(body.get("enable")))
                return self._send(200, integrations.status())
            elif p == "/api/open":
                target = OPEN_TARGETS.get(body.get("target"))
                if not target:
                    return self._send(404, {"error": "unknown target"})
                if target.startswith("dir:"):
                    path = {"media": MEDIA_DIR, "config": APP_DIR}[target[4:]]
                    os.makedirs(path, exist_ok=True)
                    os.startfile(path)
                else:
                    os.startfile(target)  # fixed allow-list: Windows settings page or a known URL
            elif p == "/api/show":
                if self.app:
                    self.app.show()
            elif p == "/api/quit":
                if self.app:
                    threading.Thread(target=self.app.quit, daemon=True).start()
            else:
                return self._send(404, {"error": "not found"})
        except Exception as ex:
            return self._send(400, {"error": str(ex)})
        return self._send(200, {"ok": True})

    def _upload(self, body):
        e = self.engine
        name = re.sub(r"[^\w.\- ]", "_", os.path.basename(str(body.get("name", "image.png"))))[:80]
        if not name.lower().endswith(MEDIA_EXT):
            return self._send(400, {"error": _("Not a supported image file")})
        data = base64.b64decode(str(body.get("data", "")).split(",")[-1], validate=False)
        if not data or len(data) > MAX_UPLOAD:
            return self._send(400, {"error": _("Not a supported image file")})
        os.makedirs(MEDIA_DIR, exist_ok=True)
        path = os.path.join(MEDIA_DIR, name)
        with open(path, "wb") as f:
            f.write(data)
        e.media_cache.pop(name, None)
        if e.media_scene(name) is None:
            os.remove(path)
            return self._send(400, {"error": _("Not a supported image file")})
        e.update_config({"media": name})
        e.set_mode("media")
        return self._send(200, {"ok": True, "name": name})


def serve(engine, app=None, port=7777):
    Handler.engine, Handler.app = engine, app
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True, name="ditoo-http").start()
    return httpd

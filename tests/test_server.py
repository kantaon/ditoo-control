"""Local API: security checks and basic endpoints (engine not started → no Bluetooth)."""
import http.client
import json
import socket

import pytest

from ditoo_control import server
from ditoo_control.engine import Engine


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def api():
    port = free_port()
    httpd = server.serve(Engine(), None, port)

    def call(method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        h = {"Host": f"127.0.0.1:{port}"}
        h.update(headers or {})
        data = None
        if body is not None:
            data = json.dumps(body)
            h.setdefault("Content-Type", "application/json")
        c.request(method, path, data, h)
        r = c.getresponse()
        raw = r.read()
        return r.status, (json.loads(raw) if r.getheader("Content-Type", "").startswith("application/json") else raw)

    yield call
    httpd.shutdown()


def test_ping_and_state(api):
    assert api("GET", "/api/ping")[1]["app"] == "ditoo-control"
    status, st = api("GET", "/api/state")
    assert status == 200 and "device" in st and "telemetry" in st


def test_foreign_host_is_rejected(api):
    assert api("GET", "/api/state", headers={"Host": "evil.example"})[0] == 403


def test_cross_site_browser_requests_are_rejected(api):
    assert api("GET", "/api/notify?text=hi", headers={"Sec-Fetch-Site": "cross-site"})[0] == 403


def test_post_requires_json(api):
    assert api("POST", "/api/mode", body={"mode": "auto"}, headers={"Content-Type": "text/plain"})[0] == 415


def test_unknown_mode_is_rejected(api):
    assert api("POST", "/api/mode", body={"mode": "nope"})[0] == 400


def test_static_files_cannot_escape_the_ui_folder(api):
    assert api("GET", "/ui/../server.py")[0] == 404
    assert api("GET", "/ui/%2e%2e/server.py")[0] == 404
    assert api("GET", "/")[0] == 200


def test_hook_endpoint(api):
    assert api("GET", "/api/ai?source=claude&state=working")[1]["ok"]
    assert api("GET", "/api/ai?source=claude&state=bogus")[0] == 400


def test_open_only_allows_known_targets(api):
    assert api("POST", "/api/open", body={"target": "C:\\Windows\\System32\\calc.exe"})[0] == 404


def test_sanitize_patch_drops_unknown_keys_and_wrong_types():
    patch = server.sanitize_patch({"brightness": 50, "evil": 1, "mode": 5, "games": [], "lat": 50.1})
    assert patch == {"brightness": 50, "games": [], "lat": 50.1}


def test_gallery(api):
    items = api("GET", "/api/gallery")[1]
    assert len(items) > 20 and all(len(i["frames"][0]) == 1536 for i in items)

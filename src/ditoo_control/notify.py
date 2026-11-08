"""Bridge used by Claude Code hooks, the Codex ``notify`` setting and your own scripts.

  notify.py claude                 Claude Code hook – reads the hook JSON from stdin
  notify.py codex '{json}'         Codex notify – JSON passed as the last argument
  notify.py codex --chain CMD… '{json}'
                                   same, and forwards the payload to the notify command
                                   that was configured before (e.g. the Codex app's own)
  notify.py claude working         manual: working | done | error | attention | idle
  notify.py text "BUILD OK"        scrolling notification on the display

Standard library only (it is executed by path, outside the package). It never prints
and always exits 0, so it can't disturb the tool that calls it.
"""
import json
import os
import sys
import urllib.parse

# Claude Code hook events → agent state
CLAUDE_EVENTS = {
    "UserPromptSubmit": "working",
    "PostToolUse": "working",        # also clears "waiting" once a permission was granted
    "Stop": "done",
    "SessionEnd": "idle",
    "Notification": None,            # decided by notification_type, see below
}
# Claude Code sends "Notification" both when it needs a permission and when it has just been
# idle for a while ("Claude is waiting for your input"). Only the first one needs the user.
ATTENTION_TYPES = {"permission_prompt", "elicitation_dialog"}
IGNORED_TYPES = {"idle_prompt", "auth_success"}


def port():
    try:
        p = os.path.join(os.environ.get("APPDATA", ""), "DitooControl", "config.json")
        with open(p, encoding="utf-8") as f:
            return int(json.load(f).get("http_port", 7777))
    except (OSError, ValueError, TypeError):
        return 7777


def send(path, **params):
    """Fire-and-forget GET to the local app (raw socket: hooks run on every tool call, keep it fast)."""
    import socket
    query = urllib.parse.urlencode(params)
    req = f"GET {path}?{query} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n".encode()
    try:
        with socket.create_connection(("127.0.0.1", port()), timeout=0.5) as s:
            s.sendall(req)
            s.recv(64)
    except OSError:
        pass


def chain(cmd, payload):
    import subprocess
    try:
        subprocess.Popen(cmd + [payload], creationflags=0x08000000 | 0x00000008,  # no window, detached
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def claude_state(data):
    event = data.get("hook_event_name", "")
    if event != "Notification":
        return CLAUDE_EVENTS.get(event)
    ntype = data.get("notification_type", "")
    if ntype in ATTENTION_TYPES:
        return "attention"
    if ntype in IGNORED_TYPES:
        return None
    msg = (data.get("message") or "").lower()          # older Claude Code without notification_type
    if "permission" in msg or "approve" in msg:
        return "attention"
    return None


def _read_std_handle():
    """A windowed .exe has no sys.stdin, but the hook's pipe is still our standard input handle."""
    try:
        import ctypes
        import msvcrt
        handle = ctypes.windll.kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        if not handle or handle == ctypes.c_void_p(-1).value:
            return ""
        with os.fdopen(msvcrt.open_osfhandle(handle, os.O_RDONLY), "rb") as f:
            return f.read().decode("utf-8", "replace")
    except Exception:
        return ""


def read_stdin():
    try:
        if sys.stdin is None:
            raw = _read_std_handle()
        elif sys.stdin.isatty():
            return {}
        else:
            raw = sys.stdin.read()
        return json.loads(raw or "{}")
    except (ValueError, OSError):
        return {}


def main(argv):
    if len(argv) < 2:
        return
    if "--chain" in argv:
        i = argv.index("--chain")
        payload = argv[-1] if len(argv) > i + 1 and argv[-1].lstrip().startswith("{") else None
        original = argv[i + 1:-1] if payload else argv[i + 1:]
        if original and payload:
            chain(original, payload)
        argv = argv[:i] + ([payload] if payload else [])
    source = argv[1].lower()
    arg = argv[2] if len(argv) > 2 else None
    if source == "text" and arg:
        send("/api/notify", text=arg)
        return
    if arg and arg.lstrip().startswith("{"):         # Codex notify payload
        try:
            data = json.loads(arg)
        except ValueError:
            return
        if data.get("type") == "agent-turn-complete":
            send("/api/ai", source=source, state="done", detail=(data.get("last-assistant-message") or "")[:100])
        return
    if arg:
        send("/api/ai", source=source, state=arg)
        return
    data = read_stdin()
    state = claude_state(data)
    if state:
        detail = data.get("message") or data.get("tool_name") or ""
        send("/api/ai", source=source, state=state, detail=str(detail)[:100])


if __name__ == "__main__":
    try:
        main(sys.argv)
    except Exception:
        pass

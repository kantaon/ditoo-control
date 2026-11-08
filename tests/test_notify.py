"""The hook bridge: Claude Code event mapping, Codex payloads, chaining."""
import json

import pytest

from ditoo_control import notify


@pytest.fixture
def sent(monkeypatch):
    calls = []
    monkeypatch.setattr(notify, "send", lambda path, **kw: calls.append((path, kw)))
    return calls


@pytest.mark.parametrize("data, state", [
    ({"hook_event_name": "UserPromptSubmit"}, "working"),
    ({"hook_event_name": "PostToolUse", "tool_name": "Bash"}, "working"),
    ({"hook_event_name": "Stop"}, "done"),
    ({"hook_event_name": "SessionEnd"}, "idle"),
    ({"hook_event_name": "Notification", "notification_type": "permission_prompt"}, "attention"),
    ({"hook_event_name": "Notification", "notification_type": "idle_prompt"}, None),
    ({"hook_event_name": "Notification", "message": "Claude needs your permission to use Bash"}, "attention"),
    ({"hook_event_name": "Notification", "message": "Claude is waiting for your input"}, None),
    ({"hook_event_name": "PreCompact"}, None),
])
def test_claude_events(data, state):
    assert notify.claude_state(data) == state


def test_codex_turn_complete(sent):
    notify.main(["notify", "codex", json.dumps({"type": "agent-turn-complete", "last-assistant-message": "ok"})])
    assert sent == [("/api/ai", {"source": "codex", "state": "done", "detail": "ok"})]


def test_codex_chain_forwards_payload(sent, monkeypatch):
    chained = []
    monkeypatch.setattr(notify, "chain", lambda cmd, payload: chained.append((cmd, payload)))
    payload = json.dumps({"type": "agent-turn-complete"})
    notify.main(["notify", "codex", "--chain", "C:\\app\\helper.exe", "turn-ended", payload])
    assert chained == [(["C:\\app\\helper.exe", "turn-ended"], payload)]
    assert sent[0][1]["state"] == "done"


def test_manual_state_and_text(sent):
    notify.main(["notify", "agent", "working"])
    notify.main(["notify", "text", "BUILD OK"])
    assert sent == [("/api/ai", {"source": "agent", "state": "working"}), ("/api/notify", {"text": "BUILD OK"})]


def test_never_raises_without_a_running_app(monkeypatch):
    monkeypatch.setattr(notify, "port", lambda: 1)  # nothing listens there
    notify.send("/api/ai", source="x", state="done")

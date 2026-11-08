"""Integrations must only touch their own entries and be fully reversible."""
import json
import tomllib

import pytest

from ditoo_control import integrations as I


@pytest.fixture
def claude_file(tmp_path, monkeypatch):
    p = tmp_path / ".claude" / "settings.json"
    p.parent.mkdir()
    p.write_text(json.dumps({"model": "x", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "my-own-hook"}]}]}}))
    monkeypatch.setattr(I, "CLAUDE_SETTINGS", str(p))
    return p


@pytest.fixture
def codex_file(tmp_path, monkeypatch):
    p = tmp_path / ".codex" / "config.toml"
    p.parent.mkdir()
    p.write_text('model = "m"\nnotify = ["C:\\\\Codex\\\\helper.exe", "turn-ended"]\n[features]\nx = true\n')
    monkeypatch.setattr(I, "CODEX_CONFIG", str(p))
    return p


def test_claude_round_trip_keeps_user_hooks(claude_file):
    original = json.loads(claude_file.read_text())
    assert I.claude_set(True)
    data = json.loads(claude_file.read_text())
    assert data["model"] == "x"
    assert any(h["command"] == "my-own-hook" for m in data["hooks"]["Stop"] for h in m["hooks"])
    for ev in I.CLAUDE_HOOKS:
        assert any(I._ours(h["command"]) for m in data["hooks"][ev] for h in m["hooks"])
    assert I.claude_set(True)                 # idempotent: no duplicates
    data = json.loads(claude_file.read_text())
    assert sum(I._ours(h["command"]) for m in data["hooks"]["Stop"] for h in m["hooks"]) == 1
    assert not I.claude_set(False)
    assert json.loads(claude_file.read_text()) == original


def test_claude_replaces_entries_from_old_install_paths(claude_file):
    data = json.loads(claude_file.read_text())
    data["hooks"]["Stop"].append({"hooks": [{"type": "command", "command": '"py" "C:\\old\\ditoo_notify.py" claude'}]})
    claude_file.write_text(json.dumps(data))
    I.claude_set(True)
    cmds = [h["command"] for m in json.loads(claude_file.read_text())["hooks"]["Stop"] for h in m["hooks"]]
    assert not any("C:\\old" in c for c in cmds)


def test_codex_chains_existing_notify_and_restores_it(codex_file):
    before = tomllib.loads(codex_file.read_text())
    assert I.codex_set(True)
    after = tomllib.loads(codex_file.read_text())
    assert after["notify"][-4:] == ["codex", "--chain", "C:\\Codex\\helper.exe", "turn-ended"]
    assert after["features"] == before["features"] and after["model"] == "m"
    assert I.codex_set(True)                  # re-enabling keeps a single chain
    assert tomllib.loads(codex_file.read_text())["notify"].count("--chain") == 1
    assert not I.codex_set(False)
    assert tomllib.loads(codex_file.read_text()) == before


def test_codex_without_previous_notify(codex_file):
    codex_file.write_text("[features]\nx = true\n")
    I.codex_set(True)
    data = tomllib.loads(codex_file.read_text())
    assert "--chain" not in data["notify"] and data["features"] == {"x": True}
    I.codex_set(False)
    assert "notify" not in tomllib.loads(codex_file.read_text())


def test_broken_codex_config_is_left_alone(codex_file):
    codex_file.write_text("this is = = not toml")
    with pytest.raises(RuntimeError):
        I.codex_set(True)
    assert codex_file.read_text() == "this is = = not toml"

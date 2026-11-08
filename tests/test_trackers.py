from ditoo_control import config, trackers


def test_stable_ignores_jitter_and_follows_real_changes():
    s = trackers.Stable(step=1, jump=3, confirm=3)
    assert s.update(60) == 60
    for v in (60.6, 59.5, 60.4, 59.6):        # jitter below one degree
        assert s.update(v) == 60
    assert s.update(61.2) == 60               # 1st confirmation
    assert s.update(61.2) == 60               # 2nd
    assert round(s.update(61.2), 1) == 61.2   # 3rd → accepted
    assert s.update(70) == 70                 # big jump is immediate


def test_ai_attention_and_flash():
    ai = trackers.AITracker()
    assert ai.event("claude", "working")
    assert ai.current() == ("working", "claude")
    ai.event("claude", "attention")
    assert ai.current() == ("attention", "claude")
    ai.event("claude", "working")             # permission granted → back to work
    assert ai.current() == ("working", "claude")
    ai.event("claude", "done")
    assert ai.current() == ("done", "claude")
    ai.sources["claude"]["since"] -= ai.FLASH + 1
    assert ai.current() == ("idle", None)


def test_ai_rejects_unknown_states():
    assert not trackers.AITracker().event("claude", "dancing")


def test_ai_attention_expires():
    ai = trackers.AITracker()
    ai.event("codex", "attention")
    ai.sources["codex"]["since"] -= ai.ATTN_TTL + 1
    assert ai.current() == ("idle", None)


def test_multiple_agents_working():
    ai = trackers.AITracker()
    ai.event("claude", "working")
    ai.event("codex", "working")
    assert ai.working() == ["claude", "codex"]


def test_pomodoro_lifecycle():
    cfg = config.merge(config.DEFAULTS, {"pomodoro": {"focus": 1, "break": 1}})
    p = trackers.Pomodoro()
    assert not p.running
    p.action(cfg, "start")
    assert p.running and p.phase == "focus" and p.total == 60
    p.action(cfg, "pause")
    left = p.remaining()
    assert p.paused and p.remaining() == left
    p.action(cfg, "resume")
    p.end -= 120                               # time is up
    assert p.tick(cfg) and p.phase == "break" and p.rounds == 1
    p.action(cfg, "stop")
    assert not p.running and p.remaining() == 0


def test_config_merge_keeps_unknown_defaults():
    merged = config.merge(config.DEFAULTS, {"night": {"brightness": 5}})
    assert merged["night"]["brightness"] == 5
    assert merged["night"]["start"] == config.DEFAULTS["night"]["start"]

"""State the engine keeps between ticks: smoothed telemetry, AI agents, games, pomodoro."""
import collections
import threading
import time

from . import sensors


class Stable:
    """Calm number for a 16x16 display: EMA smoothing + hysteresis, so digits and bars
    only move when the change is real (no 63↔64 flicker every second)."""

    def __init__(self, step=1.0, jump=3.0, confirm=3, alpha=1.0):
        self.step, self.jump, self.confirm, self.alpha = step, jump, confirm, alpha
        self.value = self.ema = None
        self.n = 0

    def update(self, raw):
        if raw is None:
            self.value = self.ema = None
            return None
        self.ema = raw if self.ema is None else self.ema + self.alpha * (raw - self.ema)
        v = self.ema
        if self.value is None or abs(v - self.value) >= self.jump:
            self.value, self.n = v, 0
        elif abs(v - self.value) >= self.step:
            self.n += 1
            if self.n >= self.confirm:
                self.value, self.n = v, 0
        else:
            self.n = 0
        return self.value


class DisplayValues:
    """What the panel shows – smoothed copies of the raw telemetry."""

    def __init__(self):
        self.s = {"cpu_temp": Stable(1, 3, 3), "gpu_temp": Stable(1, 3, 3),
                  "cpu_load": Stable(6.25, 25, 2, 0.4), "gpu_load": Stable(6.25, 25, 2, 0.4),
                  "fps": Stable(2, 12, 2, 0.45)}
        self.cpu_temp = self.gpu_temp = self.cpu_load = self.gpu_load = self.framerate = None

    def update(self, tel, fps):
        for k in ("cpu_temp", "gpu_temp", "cpu_load", "gpu_load"):
            setattr(self, k, self.s[k].update(getattr(tel, k)))
        self.framerate = self.s["fps"].update(fps)
        return self


class AITracker:
    """Latest state per agent (claude, codex, …) as reported by hooks."""
    STATES = ("working", "done", "error", "attention", "idle")
    FLASH = 6               # seconds a done / error confirmation stays on screen
    WORK_TTL = 45 * 60      # a missed "done" never keeps the spinner forever
    ATTN_TTL = 10 * 60

    def __init__(self):
        self.sources = {}
        self.events = collections.deque(maxlen=30)
        self.lock = threading.Lock()

    def event(self, source, state, detail=""):
        source = (source or "agent").lower()[:20]
        state = (state or "").lower()
        if state not in self.STATES:
            return False
        now = time.time()
        with self.lock:
            prev = self.sources.get(source, {}).get("state")
            self.sources[source] = {"state": state, "since": now, "detail": (detail or "")[:120]}
            if state != prev or state in ("done", "error"):
                self.events.appendleft({"t": now, "source": source, "state": state, "detail": (detail or "")[:120]})
        return True

    def current(self):
        now = time.time()
        with self.lock:
            items = list(self.sources.items())
        flash = [(s, v) for s, v in items if v["state"] in ("done", "error") and now - v["since"] < self.FLASH]
        if flash:
            s, v = max(flash, key=lambda x: x[1]["since"])
            return v["state"], s
        for want, ttl in (("attention", self.ATTN_TTL), ("working", self.WORK_TTL)):
            hits = [(s, v) for s, v in items if v["state"] == want and now - v["since"] < ttl]
            if hits:
                return want, max(hits, key=lambda x: x[1]["since"])[0]
        return "idle", None

    def working(self):
        now = time.time()
        with self.lock:
            items = sorted(self.sources.items(), key=lambda x: x[1]["since"])
        return [s for s, v in items if v["state"] == "working" and now - v["since"] < self.WORK_TTL]

    def as_dict(self):
        state, src = self.current()
        with self.lock:
            return {"state": state, "source": src,
                    "sources": {k: dict(v) for k, v in self.sources.items()},
                    "events": list(self.events)[:12]}


class GameDetector:
    """A game is running if a listed .exe exists, or (auto) a fullscreen window that RTSS renders."""
    GRACE = 6  # seconds before a vanished game counts as closed (alt-tab, loading screens)

    def __init__(self):
        self.active = None  # {"exe", "name", "pid", "since", "auto"}
        self.last_seen = 0
        self.candidates = []

    def update(self, cfg, tel):
        procs = sensors.processes()
        by_name = {}
        for pid, exe in procs.items():
            by_name.setdefault(exe, pid)
        found = None
        for g in cfg["games"]:
            exe = g["exe"].lower()
            if exe in by_name:
                found = {"exe": exe, "name": g.get("name") or exe, "pid": by_name[exe], "auto": False}
                break
        fg_pid, full = sensors.foreground()
        ignore = {a.lower() for a in cfg["ignore_apps"]}
        known = {g["exe"].lower() for g in cfg["games"]}
        cands = []
        for pid, (exe, fps, _ft) in tel.rtss.items():
            if exe and exe not in ignore and exe not in known and pid in procs and fps > 1:
                cands.append({"exe": exe, "fps": round(fps), "foreground": pid == fg_pid and full})
        self.candidates = sorted(cands, key=lambda c: -c["fps"])[:6]
        if not found and cfg["auto_detect_games"] and full and fg_pid in tel.rtss:
            exe, fps = tel.rtss[fg_pid][:2]
            if exe not in ignore and fps >= 10:
                pretty = exe.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
                found = {"exe": exe, "name": pretty, "pid": fg_pid, "auto": True}
        now = time.time()
        if found:
            self.last_seen = now
            if not self.active or self.active["exe"] != found["exe"]:
                found["since"] = now
                self.active = found
            else:
                self.active["pid"] = found["pid"]
        elif self.active and now - self.last_seen > self.GRACE:
            self.active = None
        return self.active

    def frametime(self, tel):
        if not self.active:
            return None
        e = tel.rtss.get(self.active["pid"])
        return e[2] if e and e[2] > 0 else None

    def fps(self, tel):
        if not self.active:
            return None
        e = tel.rtss.get(self.active["pid"])
        if e and e[1] > 0:
            return e[1]
        return tel.framerate


class Pomodoro:
    """Focus / break timer. Only ever started explicitly."""

    def __init__(self):
        self.running = False
        self.paused = False
        self.phase = "focus"
        self.end = 0
        self.left = 0
        self.total = 0
        self.rounds = 0

    def start(self, cfg, phase="focus"):
        self.phase = phase
        self.total = max(1, int(cfg["pomodoro"]["focus" if phase == "focus" else "break"])) * 60
        self.end = time.time() + self.total
        self.running, self.paused = True, False

    def remaining(self):
        if not self.running:
            return 0
        return self.left if self.paused else max(0, self.end - time.time())

    def tick(self, cfg):
        """Advance to the next phase when time is up. Returns True on a phase change."""
        if self.running and not self.paused and self.remaining() <= 0:
            if self.phase == "focus":
                self.rounds += 1
                self.start(cfg, "break")
            else:
                self.start(cfg, "focus")
            return True
        return False

    def action(self, cfg, what):
        if what == "start":
            self.start(cfg, "focus")
        elif what == "pause" and self.running and not self.paused:
            self.left, self.paused = self.remaining(), True
        elif what == "resume" and self.running and self.paused:
            self.end, self.paused = time.time() + self.left, False
        elif what == "skip" and self.running:
            self.start(cfg, "break" if self.phase == "focus" else "focus")
        elif what == "stop":
            self.running = self.paused = False
            self.rounds = 0

    def as_dict(self):
        return {"running": self.running, "paused": self.paused, "phase": self.phase,
                "remaining": round(self.remaining()), "total": self.total, "rounds": self.rounds}

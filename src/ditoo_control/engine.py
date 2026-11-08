"""The brain: decides every second what the display shows and keeps the device in sync."""
import collections
import ctypes
import ctypes.wintypes as wt
import os
import threading
import time

from . import config, i18n, scenes, sensors
from .config import CONTEXT_CYCLES, MEDIA_DIR, MODES, context_label, mode_label
from .ditoo import Ditoo, find_paired
from .i18n import _
from .sounds import Sounds
from .trackers import AITracker, DisplayValues, GameDetector, Pomodoro
from .weather import Weather

MEDIA_EXT = (".png", ".gif", ".jpg", ".jpeg", ".webp", ".bmp")


class DeviceWorker(threading.Thread):
    """Owns the Bluetooth link. Applies only the newest wanted scene (coalescing), reconnects
    with back-off, and never blocks the engine loop."""

    def __init__(self, engine):
        super().__init__(daemon=True, name="ditoo-device")
        self.e = engine
        self.dev = None
        self.wanted = None
        self.applied_key = None
        self.applied_at = 0.0
        self.brightness_wanted = None
        self.brightness_applied = None
        self.wake = threading.Event()
        self.status = "disconnected"
        self.error = ""
        self.enabled = True
        self.next_try = 0.0
        self.backoff = 3
        self.last_sync = 0.0
        self.stop_flag = False

    def want(self, scene, brightness):
        self.wanted, self.brightness_wanted = scene, brightness
        self.wake.set()

    def reconnect(self):
        self.enabled = True
        self.next_try = 0
        self.backoff = 3
        if self.dev:
            self.dev.close()
        self.wake.set()

    def disconnect(self):
        self.enabled = False
        if self.dev:
            self.dev.close()
        self.status = "disconnected"
        self.wake.set()

    def _resolve_mac(self, cfg):
        if cfg["mac"]:
            return cfg["mac"]
        found = find_paired()
        if not found:
            self.status, self.error = "error", _("No Ditoo paired with this PC yet – pair it in Windows Bluetooth settings.")
            return None
        name, mac = found[0]
        self.e.log(_("Found {name} ({mac})", name=name, mac=mac))
        self.e.update_config({"mac": mac}, reconnect=False)
        return mac

    def _connect(self, cfg):
        if time.time() < self.next_try:
            return False
        mac = self._resolve_mac(cfg)
        if not mac:
            self.next_try = time.time() + 15
            return False
        if not self.dev or self.dev.mac != mac:
            if self.dev:
                self.dev.close()
            self.dev = Ditoo(mac, cfg["port"], log=self.e.log)
        self.status = "connecting"
        if not self.dev.connect():
            self.status = "error"
            self.error = _("Ditoo not found. Is it switched on and charged, paired with this PC "
                           "and disconnected from your phone?")
            self.next_try = time.time() + self.backoff
            self.backoff = min(60, self.backoff * 2)
            return False
        self.status, self.error, self.backoff = "connected", "", 3
        self.applied_key = self.brightness_applied = None
        self.last_sync = 0
        if cfg["port"] != self.dev.port:
            self.e.update_config({"port": self.dev.port}, reconnect=False)
        return True

    def _apply(self, sc):
        if sc["kind"] == "native":
            method, kw = sc["native"]
            getattr(self.dev, method)(**kw)
        elif sc["kind"] == "image":
            self.dev.image(sc["frames"][0])
        else:
            self.dev.animation(list(zip(sc["frames"], sc["ms"], strict=True)))

    def run(self):
        while not self.stop_flag:
            self.wake.wait(1.0)
            self.wake.clear()
            if not self.enabled:
                continue
            if not (self.dev and self.dev.connected) and not self._connect(self.e.cfg):
                continue
            try:
                if time.time() - self.last_sync > 6 * 3600:
                    self.dev.sync_time()
                    self.last_sync = time.time()
                if self.brightness_wanted is not None and self.brightness_wanted != self.brightness_applied:
                    self.dev.brightness(self.brightness_wanted)
                    self.brightness_applied = self.brightness_wanted
                sc = self.wanted
                if sc and sc["key"] != self.applied_key:
                    same_family = self.applied_key and sc["key"][0] == self.applied_key[0]
                    if same_family and time.time() - self.applied_at < sc.get("throttle", 0) - 0.15:
                        continue  # live data: at most one update per throttle period
                    self.applied_at = time.time()
                    self._apply(sc)
                    self.applied_key = sc["key"]
            except OSError as ex:
                self.e.log(_("Transfer error: {err}", err=ex))
                self.dev.close()
                self.status, self.error = "error", _("Connection lost, retrying…")
                self.next_try = time.time() + 2


class Engine:
    def __init__(self):
        os.makedirs(MEDIA_DIR, exist_ok=True)
        self.cfg = config.load()
        i18n.set_lang(self.cfg["lang"])
        self.lang_rev = 0
        self.lock = threading.RLock()
        self.tel = sensors.Telemetry()
        self.disp = DisplayValues()
        self.ft_hist = collections.deque(maxlen=16)
        self.ai = AITracker()
        self.games = GameDetector()
        self.pomo = Pomodoro()
        self.weather = Weather()
        self.logs = collections.deque(maxlen=100)
        self.sounds = Sounds(log=self.log)
        self.history = {k: collections.deque(maxlen=90) for k in ("cpu_temp", "gpu_temp", "cpu_load", "gpu_load", "fps")}
        self.scene = scenes.off()
        self.reason = ""
        self.context = "desk"
        self.preview_rev = 0
        self._preview_key = None
        self.pinned = None          # screen chosen with a hotkey while in auto mode
        self.pinned_ctx = None
        self.intro_until = 0.0
        self.intro_game = None
        self._intro = None
        self.idle_idx = 0
        self.idle_since = time.time()
        self.alert_on = None
        self.away = False           # user idle / PC locked → display off
        self.notice = None          # (scene, until)
        self.trial = None           # (scene, until) – gallery "try on device"
        self.media_cache = {}
        self.device = DeviceWorker(self)
        self.running = True
        self._tick_event = threading.Event()
        self._hotkey_thread_id = None

    # ------------------------------------------------------------------ helpers
    def log(self, msg):
        self.logs.appendleft({"t": time.time(), "msg": str(msg)})

    def save(self):
        with self.lock:
            config.save(self.cfg)

    def update_config(self, patch, reconnect=True):
        with self.lock:
            self.cfg = config.merge(self.cfg, patch)
            if self.cfg["mode"] not in MODES:
                self.cfg["mode"] = "auto"
            config.save(self.cfg)
        if "lang" in patch:
            i18n.set_lang(self.cfg["lang"])
            scenes.clear_cache()
            self.lang_rev += 1
        if "lat" in patch or "lon" in patch:
            self.weather.invalidate()
        if reconnect and ("mac" in patch or "port" in patch):
            self.device.reconnect()
        self.kick()

    def set_mode(self, mode):
        if mode not in MODES:
            return False
        with self.lock:
            self.cfg["mode"] = mode
            self.pinned = None
            self.trial = None
            config.save(self.cfg)
        self.log(_("Mode: {mode}", mode=mode_label(mode)))
        self.kick()
        return True

    def kick(self):
        self._tick_event.set()

    def is_night(self):
        n = self.cfg["night"]
        h = time.localtime().tm_hour
        s, e = n["start"], n["end"]
        return (h >= s or h < e) if s > e else (s <= h < e)

    def brightness(self):
        """0 really switches the LEDs off – used for Off mode, when you're away and for a dark night."""
        if self.cfg["mode"] == "off" or self.away:
            return 0
        if self.cfg["night"]["enabled"] and self.is_night():
            return min(self.cfg["brightness"], self.cfg["night"]["brightness"])
        return self.cfg["brightness"]

    def _update_away(self):
        a = self.cfg["away"]
        away = False
        if a["enabled"] and not self.games.active:
            away = (a["on_lock"] and sensors.session_locked()) or sensors.idle_seconds() >= a["minutes"] * 60
        if away != self.away:
            self.away = away
            self.log(_("You're away – display off to save the battery") if away else _("Welcome back – display on"))

    def has_location(self):
        return self.cfg.get("lat") is not None and self.cfg.get("lon") is not None

    # ------------------------------------------------------------------ sounds
    def sound(self, event, force=False):
        s = self.cfg["sound"]
        if not force:
            if not s["enabled"] or not s["events"].get(event, False):
                return
            if s["mute_in_game"] and self.games.active:
                return
            if s["quiet_night"] and self.is_night():
                return
        self.sounds.play(event, s["volume"], cooldown=0 if force else 3)

    # ------------------------------------------------------------------ AI + notifications
    def ai_event(self, source, state, detail=""):
        prev = self.ai.sources.get((source or "agent").lower()[:20], {}).get("state")
        if not self.ai.event(source, state, detail):
            return False
        if state == prev and state == "working":
            return True  # PostToolUse heartbeats: nothing new to log or redraw
        self.log(f"{scenes.agent_name(source)}: {_(state)}")
        if state in ("done", "error", "attention"):
            self.sound(state)
        self.kick()
        return True

    def notify(self, text, color=(255, 200, 0), sound=True):
        text = (text or "").strip()[:60]
        if not text:
            return False
        sc = scenes.notify(text, tuple(color))
        self.notice = (sc, time.time() + max(4.0, sum(sc["ms"]) / 1000 * 2))
        self.log(_("Notification: {text}", text=text))
        if sound:
            self.sound("notify")
        self.kick()
        return True

    def try_scene(self, gid, seconds=12):
        if gid == "test":  # setup wizard: unmistakable test pattern
            self.trial = (scenes.test_pattern(), time.time() + max(3, min(60, seconds)))
            self.kick()
            return True
        for k, title, _desc, sc in scenes.gallery():
            if k == gid:
                self.trial = (sc, time.time() + max(3, min(60, seconds)))
                self.log(_("Preview on Ditoo: {title}", title=title))
                self.kick()
                return True
        return False

    def pomodoro_action(self, what):
        self.pomo.action(self.cfg, what)
        if what == "stop":
            if self.pinned == "pomodoro":
                self.pinned = None
            if self.cfg["mode"] == "pomodoro":
                self.cfg["mode"] = "auto"
                self.save()
            self.log(_("Pomodoro stopped"))
        elif what == "start":
            self.log(_("Pomodoro started"))
        self.kick()

    # ------------------------------------------------------------------ hotkeys
    def cycle(self, step):
        ctx = self.context
        cyc = CONTEXT_CYCLES[ctx]
        cur = self.pinned
        i = cyc.index(cur) if cur in cyc else (-1 if step > 0 else 0)
        self.pinned = cyc[(i + step) % len(cyc)]
        self.pinned_ctx = ctx
        if self.cfg["mode"] != "auto":
            self.cfg["mode"] = "auto"
            self.save()
        self.log(_("Shortcut: {screen} ({context})", screen=mode_label(self.pinned), context=context_label(ctx)))
        self.kick()

    def unpin(self):
        self.pinned = None
        self.trial = None
        if self.cfg["mode"] != "auto":
            self.set_mode("auto")
        self.log(_("Shortcut: back to automatic"))
        self.kick()

    # ------------------------------------------------------------------ media
    def media_list(self):
        try:
            return [f for f in sorted(os.listdir(MEDIA_DIR)) if f.lower().endswith(MEDIA_EXT)]
        except OSError:
            return []

    def media_scene(self, name):
        if not name:
            return None
        name = os.path.basename(name)
        path = os.path.join(MEDIA_DIR, name)
        try:
            mt = os.path.getmtime(path)
        except OSError:
            return None
        cached = self.media_cache.get(name)
        if not cached or cached[0] != mt:
            try:
                frames, ms = scenes.load_media(path)
            except Exception as e:
                self.log(_("Image can't be loaded: {err}", err=e))
                return None
            cached = (mt, scenes.media(frames, ms, name))
            self.media_cache[name] = cached
        return cached[1]

    # ------------------------------------------------------------------ scene selection
    def _screen(self, screen, game=None):
        cfg = self.cfg
        if screen == "clock":
            return scenes.clock(cfg)
        if screen == "monitor":
            return scenes.monitor(self.disp, cfg)
        if screen == "game":
            return scenes.game(self.disp, self.disp.framerate, cfg, game["name"] if game else _("no game"),
                               list(self.ft_hist))
        if screen in ("weather", "weather_tomorrow"):
            if not self.has_location():
                return scenes.weather_unset()
            return scenes.weather(self.weather.data, screen == "weather_tomorrow", cfg["city"])
        if screen == "ai":
            state, src = self.ai.current()
            if state == "working":
                return scenes.ai_working(src, self.ai.working())
            return {"attention": scenes.ai_attention, "done": scenes.ai_done,
                    "error": scenes.ai_error}.get(state, lambda _s: scenes.ai_idle())(src)
        if screen == "pomodoro":
            p = self.pomo
            if not p.running:  # never start the timer just by showing the screen
                return scenes.pomodoro_ready(cfg["pomodoro"]["focus"])
            return scenes.pomodoro(p.remaining(), p.total, p.phase, p.paused)
        if screen == "ambient":
            return scenes.effect(cfg["effect"])
        if screen == "text":
            return scenes.scrolling_text(cfg["text"], cfg["text_color"], cfg.get("text_rainbow", False))
        if screen == "media":
            return self.media_scene(cfg["media"]) or scenes.media_missing()
        if screen == "visualizer":
            return scenes.visualizer(0)
        if screen == "lamp":
            return scenes.lamp(cfg["lamp_color"])
        return scenes.off()

    def _idle_rotation(self):
        h = time.localtime().tm_hour
        seq = []
        for name in ("clock", "weather", "monitor", "ambient"):
            sec = int(self.cfg["idle"].get(name, 0) or 0)
            if sec <= 0 or (name == "weather" and not self.has_location()):
                continue
            seq.append((name, sec))
            if name == "weather" and h >= 17:
                seq.append(("weather_tomorrow", max(5, sec)))
        if not seq:
            return "clock", _("Idle – clock")
        if self.idle_idx >= len(seq):
            self.idle_idx = 0
        if time.time() - self.idle_since >= seq[self.idle_idx][1]:
            self.idle_idx = (self.idle_idx + 1) % len(seq)
            self.idle_since = time.time()
        return seq[self.idle_idx][0], _("Idle – rotating screens")

    def _auto(self, game):
        cfg, rules = self.cfg, self.cfg["rules"]
        t = self.tel
        ai_state, ai_src = self.ai.current()
        ctx = "game" if game else "ai" if ai_state in ("working", "attention") else "desk"
        if ctx != self.context:
            self.context = ctx
            if self.pinned and self.pinned_ctx != ctx:
                self.pinned = None
        # 1) overheating
        if rules["alerts"]:
            hot = None
            for which, temp, crit in (("CPU", t.cpu_temp, cfg["cpu_crit"]), ("GPU", t.gpu_temp, cfg["gpu_crit"])):
                if temp is not None and temp >= (crit - 3 if self.alert_on == which else crit):
                    hot = (which, temp)
                    break
            if hot and self.alert_on != hot[0]:
                self.log(_("Warning: {part} {temp} °C", part=hot[0], temp=int(hot[1])))
                self.sound("alert")
            self.alert_on = hot[0] if hot else None
            if hot:
                return scenes.overheat(*hot), _("Careful: {part} is at {temp} °C", part=hot[0], temp=int(hot[1]))
        # 2) notification
        if self.notice and time.time() < self.notice[1]:
            return self.notice[0], _("Incoming notification")
        # 3) hotkey pin
        if self.pinned:
            return self._screen(self.pinned, game), _("Picked with a shortcut · context {context}", context=context_label(ctx))
        # 4) AI finished / failed – short flash
        if rules["ai"] and ai_state in ("done", "error") and (not game or rules["ai_over_game"]):
            name = scenes.agent_name(ai_src)
            if ai_state == "done":
                return scenes.ai_done(ai_src), _("{agent} finished the task", agent=name)
            return scenes.ai_error(ai_src), _("{agent} reports an error", agent=name)
        # 5) gaming
        if rules["games"] and game:
            if self.intro_game != game["exe"]:
                self.intro_game = game["exe"]
                self.sound("game")
                if rules["intro"]:
                    self._intro = scenes.game_intro(game["name"])
                    self.intro_until = time.time() + sum(self._intro["ms"]) / 1000 + 1.5
            if self._intro and time.time() < self.intro_until:
                return self._intro, _("Game started: {name}", name=game["name"])
            why = _("Playing {name}", name=game["name"]) + (_(" · detected automatically") if game["auto"] else "")
            return scenes.game(self.disp, self.disp.framerate, cfg, game["name"], list(self.ft_hist)), why
        if not game:
            self.intro_game = None
            self._intro = None
        # 6) pomodoro
        if rules["pomodoro"] and self.pomo.running:
            p = self.pomo
            return scenes.pomodoro(p.remaining(), p.total, p.phase, p.paused), _("Pomodoro running")
        # 7) AI working / needs attention
        if rules["ai"] and ai_state == "attention":
            return scenes.ai_attention(ai_src), _("{agent} is waiting for your reply", agent=scenes.agent_name(ai_src))
        if rules["ai"] and ai_state == "working":
            agents = self.ai.working() or [ai_src]
            names = " + ".join(scenes.agent_name(a) for a in agents[:2])
            why = (_("{agents} are working on a task", agents=names) if len(agents) > 1
                   else _("{agent} is working on a task", agent=names))
            return scenes.ai_working(ai_src, agents), why
        # 8) idle rotation
        screen, why = self._idle_rotation()
        return self._screen(screen), why

    def compute(self):
        game = self.games.active
        if self.away and not self.trial:
            return scenes.off(), _("You're away – display off to save the battery")
        if self.trial:
            if time.time() < self.trial[1]:
                return self.trial[0], _("Gallery preview")
            self.trial = None
        if self.cfg["mode"] == "auto":
            return self._auto(game)
        self.context = "game" if game else "desk"
        return self._screen(self.cfg["mode"], game), _("Manually selected mode")

    # ------------------------------------------------------------------ threads
    def start(self):
        self.device.start()
        threading.Thread(target=self._loop, daemon=True, name="ditoo-engine").start()
        threading.Thread(target=self._weather_loop, daemon=True, name="ditoo-weather").start()
        threading.Thread(target=self._hotkey_loop, daemon=True, name="ditoo-hotkeys").start()
        self.log(_("Ditoo Control started"))

    def _weather_loop(self):
        while self.running:
            if self.has_location():
                try:
                    self.weather.get(self.cfg["lat"], self.cfg["lon"])
                except Exception:
                    pass
            time.sleep(60)

    def _tick(self, now, state):
        self.tel.refresh()
        if now - state["game_check"] > 2:
            prev = self.games.active
            self.games.update(self.cfg, self.tel)
            if self.games.active and not prev:
                self.log(_("Game detected: {name}", name=self.games.active["name"]))
            elif prev and not self.games.active:
                self.log(_("Game closed: {name}", name=prev["name"]))
            state["game_check"] = now
        self._update_away()
        fps = self.games.fps(self.tel)
        self.disp.update(self.tel, fps or self.tel.framerate)
        if self.pomo.tick(self.cfg):
            self.log(_("Pomodoro: break") if self.pomo.phase == "break" else _("Pomodoro: focus"))
            self.sound("pomodoro")
        if now - state["frametime"] >= 1:
            state["frametime"] = now
            if self.games.active:
                self.ft_hist.append((self.games.frametime(self.tel), 1000.0 / fps if fps else None))
            else:
                self.ft_hist.clear()
        if now - state["history"] >= 2:
            t = self.tel
            for k, v in (("cpu_temp", t.cpu_temp), ("gpu_temp", t.gpu_temp), ("cpu_load", t.cpu_load),
                         ("gpu_load", t.gpu_load), ("fps", fps)):
                self.history[k].append(None if v is None else round(v, 1))
            state["history"] = now
        with self.lock:
            scene, reason = self.compute()
            self.scene, self.reason = scene, reason
            if scene["key"] != self._preview_key:
                self._preview_key = scene["key"]
                self.preview_rev += 1
        self.device.want(scene, self.brightness())

    def _loop(self):
        state = {"game_check": 0.0, "frametime": 0.0, "history": 0.0}
        while self.running:
            try:
                self._tick(time.time(), state)
            except Exception as ex:  # never let the loop die
                self.log(_("Internal error: {err}", err=repr(ex)))
            self._tick_event.wait(1.0)
            self._tick_event.clear()

    def _hotkey_loop(self):
        """Global hotkeys: Ctrl+Shift+Alt + letter. (Ctrl+Alt alone is AltGr on many European layouts.)"""
        hk = self.cfg["hotkeys"]
        if not hk.get("enabled", True):
            return
        user32 = ctypes.windll.user32
        self._hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        mod = 0x0001 | 0x0002 | 0x0004 | 0x4000  # ALT | CTRL | SHIFT | NOREPEAT
        actions = {1: "prev", 2: "next", 3: "auto", 4: "bright"}
        failed = []
        for hid, name in actions.items():
            key = (hk.get(name) or "").upper()[:1]
            if not key or not user32.RegisterHotKey(None, hid, mod, ord(key)):
                failed.append(key or name)
        if failed:
            self.log(_("Hotkeys already used by another app: {keys}", keys=", ".join(failed)))
        msg = wt.MSG()
        while self.running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message != 0x0312:  # WM_HOTKEY
                continue
            act = actions.get(msg.wParam)
            if act == "prev":
                self.cycle(-1)
            elif act == "next":
                self.cycle(1)
            elif act == "auto":
                self.unpin()
            elif act == "bright":
                b = self.cfg["brightness"]
                nb = 100 if b < 40 else 20 if b >= 100 else min(100, b + 30)
                self.update_config({"brightness": nb})
                self.log(_("Shortcut: brightness {value} %", value=nb))
        for hid in actions:
            user32.UnregisterHotKey(None, hid)

    # ------------------------------------------------------------------ UI snapshot
    def state(self):
        cfg = self.cfg
        g = self.games.active
        fps = self.games.fps(self.tel)
        ft = self.games.frametime(self.tel)
        dev = self.device
        key = self.scene.get("key", ("",))
        return {
            "lang": i18n.LANG, "lang_rev": self.lang_rev,
            "device": {"status": dev.status, "error": dev.error, "mac": cfg["mac"], "port": cfg["port"],
                       "enabled": dev.enabled},
            "mode": cfg["mode"], "mode_label": mode_label(cfg["mode"]),
            "scene": {"label": self.scene.get("label", ""), "kind": self.scene.get("kind"), "id": str(key[0])},
            "reason": self.reason, "context": self.context, "context_label": context_label(self.context),
            "pinned": self.pinned, "trial": bool(self.trial),
            "preview_rev": self.preview_rev,
            "brightness": cfg["brightness"], "brightness_effective": self.brightness(),
            "night": self.is_night(), "away": self.away,
            "telemetry": self.tel.as_dict(),
            "history": {k: list(v) for k, v in self.history.items()},
            "game": ({"name": g["name"], "exe": g["exe"], "auto": g["auto"], "since": g["since"],
                      "fps": None if fps is None else round(fps),
                      "frametime": None if ft is None else round(ft, 1)} if g else None),
            "candidates": self.games.candidates,
            "ai": self.ai.as_dict(),
            "pomodoro": self.pomo.as_dict(),
            "weather": self._weather_view(),
            "weather_error": self.weather.error,
            "logs": list(self.logs)[:40],
            "media": self.media_list(),
            "sound_available": self.sounds.available,
        }

    def _weather_view(self):
        w = self.weather.data
        if not w or not self.has_location():
            return None
        w = dict(w, text=_(w["text"]))
        w["tomorrow"] = dict(w["tomorrow"], text=_(w["tomorrow"]["text"]))
        return w

    def preview(self):
        return {"rev": self.preview_rev, **encode_scene(self.scene)}

    def stop(self):
        self.running = False
        self.device.stop_flag = True
        self.device.wake.set()
        if self._hotkey_thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._hotkey_thread_id, 0x0012, 0, 0)  # WM_QUIT
        if self.device.dev:
            self.device.dev.close()


def encode_scene(sc):
    """Scene → JSON for the UI: frames as hex strings (768 bytes → 1536 chars each)."""
    return {"kind": sc.get("kind"), "ms": sc.get("ms", []),
            "frames": [bytes(c for p in f for c in p).hex() for f in sc.get("frames", [])]}

"""8-bit notification sounds played straight to the Ditoo Pro speaker.

Windows keeps your normal speakers as the default output; we open the Ditoo's own
audio endpoint (A2DP) only for these short jingles.
"""
import threading
import time

try:
    import numpy as np
    import sounddevice as sd
except ImportError:  # sounds are optional
    np = sd = None

from .i18n import _

RATE = 44100

NOTE = {n: 440.0 * 2 ** ((i - 9) / 12) for i, n in enumerate(
    ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def _freq(name):
    """'C5', 'G#4' -> Hz"""
    pitch, octave = name[:-1], int(name[-1])
    return NOTE[pitch] * 2 ** (octave - 4)


def _tone(freq, dur, wave="square", vol=0.35, slide=0.0):
    n = int(RATE * dur)
    t = np.arange(n) / RATE
    f = freq * (1 + slide * t / max(dur, 1e-3))
    phase = np.cumsum(2 * np.pi * f / RATE)
    if wave == "square":
        s = np.sign(np.sin(phase)) * 0.6
    elif wave == "triangle":
        s = 2 / np.pi * np.arcsin(np.sin(phase))
    elif wave == "noise":
        s = np.random.default_rng(1).uniform(-1, 1, n)
    else:
        s = np.sin(phase)
    env = np.minimum(1, np.minimum(t / 0.004, (dur - t) / 0.03).clip(0))
    return (s * env * vol).astype(np.float32)


def _seq(notes, wave="square", gap=0.012):
    parts = []
    for item in notes:
        name, dur = item[0], item[1]
        if name == "-":
            parts.append(np.zeros(int(RATE * dur), np.float32))
        else:
            parts.append(_tone(_freq(name), dur, item[2] if len(item) > 2 else wave))
        parts.append(np.zeros(int(RATE * gap), np.float32))
    return np.concatenate(parts)


SOUNDS = {
    "done": ("Done", lambda: _seq([("C5", .07), ("E5", .07), ("G5", .07), ("C6", .18, "triangle")])),
    "attention": ("Waiting for you", lambda: _seq([("A5", .09, "triangle"), ("-", .06), ("A5", .09, "triangle"), ("E6", .16, "triangle")])),
    "error": ("Error", lambda: _seq([("E4", .12), ("C4", .12), ("G#3", .26)])),
    "game": ("Game start", lambda: _seq([("G4", .05), ("C5", .05), ("E5", .05), ("G5", .05), ("C6", .05), ("E6", .05), ("G6", .2, "triangle")], gap=0.004)),
    "pomodoro": ("Pomodoro", lambda: _seq([("E6", .12, "sine"), ("C6", .12, "sine"), ("G5", .3, "sine")])),
    "alert": ("Overheating", lambda: _seq([("A5", .1), ("D5", .1)] * 3)),
    "notify": ("Notification", lambda: _seq([("B5", .06, "triangle"), ("E6", .14, "triangle")])),
}


class Sounds:
    def __init__(self, log=print):
        self.log = log
        self.available = sd is not None
        self.device = None
        self.last = {}
        self.lock = threading.Lock()

    def candidates(self, hint="DitooPro"):
        """Ditoo stereo (A2DP) endpoints, best host API first. Bluetooth endpoints come and go,
        so PortAudio is re-initialised to get a fresh list every time."""
        if not self.available:
            return []
        try:
            sd._terminate()
            sd._initialize()
            apis = sd.query_hostapis()
            out = []
            for i, d in enumerate(sd.query_devices()):
                api = apis[d["hostapi"]]["name"]
                rank = {"Windows WASAPI": 0, "Windows DirectSound": 1, "MME": 2}.get(api)
                if rank is None or d["max_output_channels"] < 2:
                    continue  # skip WDM-KS and the mono hands-free (phone call) profile
                if hint.lower() in d["name"].lower() and "Hands-Free" not in d["name"]:
                    out.append((rank, i))
            return [i for _r, i in sorted(out)]
        except Exception as e:
            self.log(f"Sound: {e}")
            return []

    def find_device(self, hint="DitooPro"):
        c = self.candidates(hint)
        return c[0] if c else None

    def play(self, name, volume=1.0, cooldown=3.0):
        if not self.available or name not in SOUNDS:
            return False
        now = time.time()
        if now - self.last.get(name, 0) < cooldown:
            return False
        self.last[name] = now
        threading.Thread(target=self._play, args=(name, volume), daemon=True).start()
        return True

    def _play(self, name, volume):
        with self.lock:
            devs = self.candidates()
            if not devs:
                self.log(_("Sound: Ditoo is not connected as a speaker"))
                return
            # Bluetooth audio needs a moment to wake up, so lead in with silence
            data = np.concatenate([np.zeros(int(RATE * 0.35), np.float32), SOUNDS[name][1]() * volume])
            err = None
            for dev in devs:
                try:
                    sd.play(data, RATE, device=dev, blocking=True)
                    return
                except Exception as e:
                    err = e
            self.log(_("Sound could not be played: {err}", err=err))

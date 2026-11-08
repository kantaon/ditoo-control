"""Bluetooth (classic RFCOMM/SPP) driver for the Divoom Ditoo Pro, 16x16 px.

Frame:  01 | len u16le | cmd | args... | checksum u16le | 02
        len = len(args) + 3, checksum = sum(len bytes + cmd + args) & 0xFFFF
"""
import datetime
import math
import socket
import threading
import time

from .i18n import _

SIZE = 16

CMD_DATETIME = 0x18
CMD_TIME_TYPE = 0x2D
CMD_IMAGE = 0x44
CMD_VIEW = 0x45
CMD_ANIM = 0x49
CMD_BRIGHTNESS = 0x74

ANIM_CHUNK = 200
MAX_FRAMES = 60


def _u16(n):
    return [n & 0xFF, (n >> 8) & 0xFF]


def build_message(cmd, args=()):
    payload = _u16(len(args) + 3) + [cmd] + list(args)
    return bytes([0x01] + payload + _u16(sum(payload) & 0xFFFF) + [0x02])


def _reduce_palette(pixels):
    """Divoom frames allow max 256 colours; crush precision until we fit."""
    shift = 0
    while len(set(pixels)) > 256 and shift < 7:
        shift += 1
        mask = 0xFF << shift & 0xFF
        pixels = [(r & mask, g & mask, b & mask) for r, g, b in pixels]
    return pixels


def encode_frame(pixels, time_ms=0):
    """pixels: 256 (r, g, b) tuples, row-major from top-left."""
    pixels = _reduce_palette([tuple(int(c) & 0xFF for c in p) for p in pixels])
    palette, index, idxs = [], {}, []
    for p in pixels:
        if p not in index:
            index[p] = len(palette)
            palette.append(p)
        idxs.append(index[p])
    n = len(palette)
    bpp = max(1, math.ceil(math.log2(n))) if n > 1 else 1
    packed, acc, nbits = [], 0, 0
    for i in idxs:
        acc |= i << nbits
        nbits += bpp
        while nbits >= 8:
            packed.append(acc & 0xFF)
            acc >>= 8
            nbits -= 8
    if nbits:
        packed.append(acc & 0xFF)
    body = _u16(time_ms) + [0x00, n & 0xFF]
    for r, g, b in palette:
        body += [r, g, b]
    body += packed
    return bytes([0xAA] + _u16(len(body) + 3) + body)


def find_paired(hints=("ditoo", "divoom", "pixoo", "timoo", "tivoo")):
    """Paired Divoom devices from the Windows Bluetooth registry → [(name, "AA:BB:..")]."""
    try:
        import winreg
    except ImportError:
        return []
    out = []
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices")
    except OSError:
        return []
    with root:
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(root, i)
            except OSError:
                break
            i += 1
            try:
                with winreg.OpenKey(root, sub) as k:
                    raw = winreg.QueryValueEx(k, "Name")[0]
            except OSError:
                continue
            name = bytes(raw).split(b"\0", 1)[0].decode("utf-8", "replace")
            if len(sub) == 12 and any(h in name.lower() for h in hints):
                out.append((name, ":".join(sub[j:j + 2] for j in range(0, 12, 2)).upper()))
    # the audio/SPP radio carries the control channel
    out.sort(key=lambda d: ("audio" not in d[0].lower(), d[0]))
    return out


class Ditoo:
    def __init__(self, mac, port=2, log=print):
        self.mac = mac
        self.port = port
        self.log = log
        self.sock = None
        self.lock = threading.RLock()
        self._last_image = None

    # ---------- connection ----------
    @property
    def connected(self):
        return self.sock is not None

    def connect(self):
        with self.lock:
            if self.sock:
                return True
            ports = [self.port] + [p for p in (2, 1, 4) if p != self.port]
            for port in ports:
                s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                s.settimeout(10)
                try:
                    s.connect((self.mac, port))
                except OSError as e:
                    s.close()
                    self.log(_("Channel {port}: {err}", port=port, err=e.strerror or e))
                    continue
                s.settimeout(5)
                self.sock, self.port = s, port
                self._last_image = None
                threading.Thread(target=self._drain, args=(s,), daemon=True).start()
                time.sleep(0.5)
                self.log(_("Connected to {mac} (channel {port})", mac=self.mac, port=port))
                return True
            return False

    def close(self):
        with self.lock:
            if self.sock:
                try:
                    self.sock.close()
                except OSError:
                    pass
            self.sock = None

    def _drain(self, s):
        """The device sends acks; read them so buffers never fill up."""
        s.settimeout(None)
        while self.sock is s:
            try:
                if not s.recv(512):
                    break
            except OSError:
                break
        if self.sock is s:
            self.log(_("Connection to the device lost"))
            self.close()

    def send(self, cmd, args=()):
        msg = build_message(cmd, args)
        with self.lock:
            if not self.sock and not self.connect():
                raise ConnectionError(_("Ditoo is not reachable"))
            try:
                self.sock.sendall(msg)
            except OSError:
                self.close()
                raise

    # ---------- commands ----------
    def brightness(self, value):
        self.send(CMD_BRIGHTNESS, [max(0, min(100, int(value)))])

    def sync_time(self, now=None):
        now = now or datetime.datetime.now()
        self.send(CMD_DATETIME, [now.year % 100, now.year // 100, now.month, now.day,
                                 now.hour, now.minute, now.second, now.isoweekday() % 7])

    def clock(self, style=0, color=(255, 255, 255), h24=True, weather=False, temp=False, calendar=False):
        self._last_image = None
        self.send(CMD_TIME_TYPE, [1 if h24 else 0])
        self.send(CMD_VIEW, [0x00, 1 if h24 else 0, style, 0x01,
                             int(weather), int(temp), int(calendar), *color])

    def light(self, color, brightness=100):
        self._last_image = None
        self.send(CMD_VIEW, [0x01, *color, brightness, 0x00, 0x01, 0, 0, 0, 0])

    def visualizer(self, n=0):
        self._last_image = None
        self.send(CMD_VIEW, [0x04, n])

    def image(self, pixels, force=False):
        """Show a static 16x16 image. Skips identical repeats to save airtime."""
        frame = encode_frame(pixels)
        if not force and frame == self._last_image:
            return
        self.send(CMD_IMAGE, [0x00, 0x0A, 0x0A, 0x04] + list(frame))
        self._last_image = frame

    def animation(self, frames, frame_ms=100):
        """frames: list of pixel lists, or (pixels, ms) tuples. The device loops it."""
        data = b""
        for f in frames[:MAX_FRAMES]:
            pixels, ms = f if isinstance(f, tuple) else (f, frame_ms)
            data += encode_frame(pixels, ms)
        total = len(data)
        with self.lock:
            for k in range(0, total, ANIM_CHUNK):
                self.send(CMD_ANIM, _u16(total) + [k // ANIM_CHUNK] + list(data[k:k + ANIM_CHUNK]))
        self._last_image = None

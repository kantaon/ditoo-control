"""PC telemetry on Windows without extra dependencies.

- MSI Afterburner shared memory (MAHM): CPU/GPU temperature, usage, power, framerate
- RivaTuner Statistics Server shared memory (RTSS): per-process FPS of hooked 3D apps
- Toolhelp snapshot: running process names
- Foreground window: is something running fullscreen?
"""
import ctypes
import ctypes.wintypes as wt
import mmap
import os
import struct
import time

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


def _open_map(name, size):
    try:
        return mmap.mmap(-1, size, tagname=name, access=mmap.ACCESS_READ)
    except (OSError, ValueError):
        return None


def read_afterburner():
    """Returns {source name: value} or {} when Afterburner is not running."""
    m = _open_map("MAHMSharedMemory", 32)
    if not m:
        return {}
    try:
        sig, ver, hsz, n, esz = struct.unpack_from("<5I", m, 0)
        if sig != 0x4D41484D or n == 0 or n > 1024:
            return {}
    finally:
        m.close()
    m = _open_map("MAHMSharedMemory", hsz + n * esz)
    if not m:
        return {}
    out = {}
    try:
        for i in range(n):
            o = hsz + i * esz
            name = m[o:o + 260].split(b"\0", 1)[0].decode("latin1")
            val = struct.unpack_from("<f", m, o + 1300)[0]
            if val < 3.0e38:  # FLT_MAX = no data
                out[name] = val
    finally:
        m.close()
    return out


def rtss_running():
    """RivaTuner Statistics Server is running (its shared memory exists), even if no game is hooked yet."""
    m = _open_map("RTSSSharedMemoryV2", 4)
    if not m:
        return False
    try:
        return struct.unpack_from("<I", m, 0)[0] == 0x52545353
    finally:
        m.close()


def read_rtss():
    """Returns {pid: (exe_name, fps, frametime_ms)} for apps RTSS is currently hooking."""
    m = _open_map("RTSSSharedMemoryV2", 64)
    if not m:
        return {}
    try:
        sig, ver, esz, off, n = struct.unpack_from("<5I", m, 0)
        if sig != 0x52545353 or n > 4096:
            return {}
    finally:
        m.close()
    m = _open_map("RTSSSharedMemoryV2", off + esz * n)
    if not m:
        return {}
    out = {}
    try:
        for i in range(n):
            o = off + i * esz
            pid = struct.unpack_from("<I", m, o)[0]
            if not pid:
                continue
            path = m[o + 4:o + 264].split(b"\0", 1)[0].decode("mbcs", "replace")
            _flags, t0, t1, frames, frame_us = struct.unpack_from("<5I", m, o + 264)
            fps = 1000.0 * frames / (t1 - t0) if t1 > t0 and frames else 0.0
            out[pid] = (os.path.basename(path).lower(), fps, frame_us / 1000.0)
    finally:
        m.close()
    return out


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wt.DWORD),
                ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", ctypes.c_wchar * 260)]


kernel32.CreateToolhelp32Snapshot.restype = wt.HANDLE
kernel32.GetSystemTimes.argtypes = [ctypes.POINTER(wt.FILETIME)] * 3


def processes():
    """Returns {pid: exe name (lowercase)}."""
    snap = kernel32.CreateToolhelp32Snapshot(0x2, 0)
    if not snap or snap == wt.HANDLE(-1).value:
        return {}
    out = {}
    try:
        e = PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(e)
        ok = kernel32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            out[e.th32ProcessID] = e.szExeFile.lower()
            ok = kernel32.Process32NextW(snap, ctypes.byref(e))
    finally:
        kernel32.CloseHandle(snap)
    return out


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


user32.GetForegroundWindow.restype = wt.HWND
user32.MonitorFromWindow.restype = wt.HANDLE
_SHELL_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Windows.UI.Core.CoreWindow"}


def foreground():
    """Returns (pid, is_fullscreen) of the foreground window."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return 0, False
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    cls = ctypes.create_unicode_buffer(64)
    user32.GetClassNameW(hwnd, cls, 64)
    if cls.value in _SHELL_CLASSES:
        return pid.value, False
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(mi)
    mon = user32.MonitorFromWindow(hwnd, 2)
    if not mon or not user32.GetMonitorInfoW(mon, ctypes.byref(mi)):
        return pid.value, False
    m = mi.rcMonitor
    full = r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom
    return pid.value, full


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]


def idle_seconds():
    """Seconds since the last keyboard / mouse input."""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(info)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    return ((kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0


user32.OpenInputDesktop.restype = wt.HANDLE


def session_locked():
    """True on the lock screen (Win+L): the input desktop can't be opened by a normal app then."""
    desk = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_SWITCHDESKTOP
    if not desk:
        return True
    user32.CloseDesktop(desk)
    return False


class CpuLoad:
    """Total CPU load from GetSystemTimes – no extra software needed."""

    def __init__(self):
        self.prev = None

    def read(self):
        idle, kernel, user = wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
        if not kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        cur = [t.dwHighDateTime << 32 | t.dwLowDateTime for t in (idle, kernel, user)]
        prev, self.prev = self.prev, cur
        if not prev:
            return None
        d_idle, d_kernel, d_user = (c - p for c, p in zip(cur, prev, strict=True))
        total = d_kernel + d_user          # kernel time includes idle time
        return max(0.0, min(100.0, 100.0 * (1 - d_idle / total))) if total else None


class _NvUtil(ctypes.Structure):
    _fields_ = [("gpu", ctypes.c_uint), ("memory", ctypes.c_uint)]


NVML_PATHS = (
    os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "System32", "nvml.dll"),
    r"C:\Program Files\NVIDIA Corporation\NVSMI\nvml.dll",
)


class NvidiaGpu:
    """NVIDIA temperature + load through NVML, which ships with every NVIDIA driver."""

    def __init__(self):
        self.dev = None
        self.nvml = None
        for path in NVML_PATHS:
            try:
                self.nvml = ctypes.CDLL(path)
            except OSError:
                continue
            handle = ctypes.c_void_p()
            if self.nvml.nvmlInit_v2() == 0 and self.nvml.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(handle)) == 0:
                self.dev = handle
            break

    def read(self):
        if not self.dev:
            return None, None
        temp, util = ctypes.c_uint(), _NvUtil()
        t = float(temp.value) if self.nvml.nvmlDeviceGetTemperature(self.dev, 0, ctypes.byref(temp)) == 0 else None
        u = float(util.gpu) if self.nvml.nvmlDeviceGetUtilizationRates(self.dev, ctypes.byref(util)) == 0 else None
        return t, u


class _PdhValue(ctypes.Structure):
    _fields_ = [("CStatus", wt.DWORD), ("doubleValue", ctypes.c_double)]


class _PdhItem(ctypes.Structure):
    _fields_ = [("szName", ctypes.c_wchar_p), ("FmtValue", _PdhValue)]


GPU_COUNTER = r"\GPU Engine(*engtype_3D)\Utilization Percentage"


class GpuLoadPdh:
    """Vendor-neutral GPU load from the Windows "GPU Engine" performance counters (NVIDIA, AMD, Intel)."""

    def __init__(self):
        self.query = self.counter = None
        try:
            self.pdh = ctypes.WinDLL("pdh")
            q, c = ctypes.c_void_p(), ctypes.c_void_p()
            if self.pdh.PdhOpenQueryW(None, None, ctypes.byref(q)) == 0 and \
                    self.pdh.PdhAddEnglishCounterW(q, GPU_COUNTER, None, ctypes.byref(c)) == 0:
                self.query, self.counter = q, c
                self.pdh.PdhCollectQueryData(q)
        except (OSError, AttributeError):
            pass

    def read(self):
        if not self.query or self.pdh.PdhCollectQueryData(self.query) != 0:
            return None
        size, count = wt.DWORD(0), wt.DWORD(0)
        self.pdh.PdhGetFormattedCounterArrayW(self.counter, 0x200, ctypes.byref(size), ctypes.byref(count), None)
        if not size.value:
            return None
        buf = (ctypes.c_byte * size.value)()
        if self.pdh.PdhGetFormattedCounterArrayW(self.counter, 0x200, ctypes.byref(size), ctypes.byref(count), buf) != 0:
            return None
        items = ctypes.cast(buf, ctypes.POINTER(_PdhItem))
        total = sum(items[i].FmtValue.doubleValue for i in range(count.value) if items[i].FmtValue.CStatus in (0, 1))
        return max(0.0, min(100.0, total))


class Telemetry:
    """Snapshot of everything the modes need, refreshed by the engine once a second.

    Sources, best first: MSI Afterburner (+ RivaTuner for FPS), then built-in readings:
    CPU load from Windows, GPU load from Windows counters, GPU temperature from the NVIDIA driver.
    Without Afterburner there is no CPU temperature and no FPS; everything else still works.
    """

    def __init__(self):
        self.cpu_temp = self.gpu_temp = None
        self.cpu_load = self.gpu_load = None
        self.cpu_power = self.gpu_power = None
        self.ram_used = None
        self.framerate = None
        self.afterburner = False
        self.rtss_running = False
        self.rtss = {}
        self.updated = 0.0
        self._cpu = CpuLoad()
        self._nv = None
        self._pdh = None

    def _fallback(self):
        cpu = self._cpu.read()                 # always read: keeps the delta fresh
        if self.cpu_load is None:
            self.cpu_load = cpu
        if self.gpu_temp is not None and self.gpu_load is not None:
            return
        if self._nv is None:
            self._nv = NvidiaGpu()
        t, u = self._nv.read()
        if self.gpu_temp is None:
            self.gpu_temp = t
        if self.gpu_load is None:
            if u is None:
                if self._pdh is None:
                    self._pdh = GpuLoadPdh()
                u = self._pdh.read()
            self.gpu_load = u

    def refresh(self):
        ab = read_afterburner()
        self.afterburner = bool(ab)
        self.cpu_temp = ab.get("CPU temperature")
        self.gpu_temp = ab.get("GPU temperature")
        self.cpu_load = ab.get("CPU usage")
        self.gpu_load = ab.get("GPU usage")
        self.cpu_power = ab.get("CPU power")
        self.gpu_power = ab.get("Power")
        self.ram_used = ab.get("RAM usage")
        self.framerate = ab.get("Framerate")
        try:
            self._fallback()
        except Exception:
            pass
        self.rtss_running = rtss_running()
        self.rtss = read_rtss() if self.rtss_running else {}
        self.updated = time.time()
        return self

    def as_dict(self):
        def r(v):
            return None if v is None else round(v, 1)
        return {"cpu_temp": r(self.cpu_temp), "gpu_temp": r(self.gpu_temp),
                "cpu_load": r(self.cpu_load), "gpu_load": r(self.gpu_load),
                "cpu_power": r(self.cpu_power), "gpu_power": r(self.gpu_power),
                "ram_used": r(self.ram_used), "afterburner": self.afterburner, "rtss": self.rtss_running}

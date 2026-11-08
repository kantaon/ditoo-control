# PyInstaller spec – builds dist/DitooControl/DitooControl.exe (one folder: starts fast, which
# matters because Claude Code runs "DitooControl.exe --notify" on every hook).
#   pyinstaller packaging/DitooControl.spec --noconfirm
import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
PKG = os.path.join(ROOT, "src", "ditoo_control")

datas = [(os.path.join(PKG, "ui"), "ditoo_control/ui")]
datas += collect_data_files("webview")
datas += collect_data_files("_sounddevice_data")

hiddenimports = collect_submodules("webview.platforms") + ["pystray._win32", "clr", "PIL.ImageSequence"]

a = Analysis(
    [os.path.join(SPECPATH, "launcher.py")],
    pathex=[os.path.join(ROOT, "src")],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "pytest", "IPython", "webview.platforms.qt", "webview.platforms.gtk",
              "webview.platforms.cocoa", "webview.platforms.android"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="DitooControl",
    console=False,
    icon=os.path.join(PKG, "ui", "icon.ico"),
    version=os.path.join(SPECPATH, "version_info.txt"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="DitooControl")

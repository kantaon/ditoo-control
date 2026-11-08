"""Writes packaging/version_info.txt (Windows file properties of the .exe) from the package version."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = re.search(r'__version__ = "([^"]+)"', (ROOT / "src/ditoo_control/__init__.py").read_text()).group(1)
nums = tuple(int(x) for x in (version.split(".") + ["0", "0", "0"])[:4])

(Path(__file__).parent / "version_info.txt").write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={nums}, prodvers={nums}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Kantaon'),
      StringStruct('FileDescription', 'Ditoo Control'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'DitooControl'),
      StringStruct('LegalCopyright', 'MIT License – Kantaon'),
      StringStruct('OriginalFilename', 'DitooControl.exe'),
      StringStruct('ProductName', 'Ditoo Control'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding="utf-8")
print("version", version)

"""Isolate tests from the real user profile: settings go to a temporary APPDATA."""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="ditoo-tests-")
os.environ["APPDATA"] = _TMP
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import importlib.util
from pathlib import Path

from ditoo_control import i18n


def test_translation_and_formatting():
    i18n.set_lang("cs")
    assert i18n._("Playing {name}", name="X") == "Běží hra X"
    assert i18n._("Text: {text}", text="hi") == "Text: hi"      # 'text' as a placeholder name works
    i18n.set_lang("en")
    assert i18n._("Playing {name}", name="X") == "Playing X"


def test_unknown_language_falls_back_to_detection():
    assert i18n.set_lang("xx") in i18n.SUPPORTED


def test_every_string_has_a_czech_translation():
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_i18n.py"
    spec = importlib.util.spec_from_file_location("check_i18n", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0

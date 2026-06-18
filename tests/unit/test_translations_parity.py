"""Backend translation parity gates (no HA harness required).

``strings.json`` is the source of truth. Every ``translations/<lang>.json`` must:
  * have identical key structure (no missing/extra keys),
  * use the same ``{token}`` placeholder set per key, and
  * not leak untranslated English values (byte-identical to the source), except
    for a tiny reviewed allowlist.

``translations/en.json`` must equal ``strings.json`` exactly (HA convention).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_COMPONENT = (
    Path(__file__).resolve().parents[2] / "custom_components" / "example_integration"
)
_STRINGS = _COMPONENT / "strings.json"
_TRANSLATIONS = _COMPONENT / "translations"

# Keys whose value is intentionally identical to English in some locale (reviewed
# cognates/loanwords). Keyed by locale -> set of dotted key paths.
_COGNATE_IDENTICAL: dict[str, set[str]] = {
    # German: the field label "Name" is the same word in both languages.
    "de": {
        "services.add_item.fields.name.name",
        "services.update_item.fields.name.name",
    },
}
# Globally-allowed identical values (symbols, product name fragments). Empty here.
_INTENTIONALLY_IDENTICAL: set[str] = set()


def _flatten(obj, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            out.update(_flatten(value, f"{prefix}.{key}" if prefix else key))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


def _placeholders(value: str) -> set[str]:
    return set(re.findall(r"\{(\w+)\}", value))


def _load(path: Path) -> dict[str, str]:
    return _flatten(json.loads(path.read_text(encoding="utf-8")))


_SOURCE = _load(_STRINGS)
_LOCALE_FILES = sorted(p for p in _TRANSLATIONS.glob("*.json"))
_NON_EN = [p for p in _LOCALE_FILES if p.stem != "en"]


def test_strings_and_en_are_identical():
    assert json.loads(_STRINGS.read_text(encoding="utf-8")) == json.loads(
        (_TRANSLATIONS / "en.json").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("path", _NON_EN, ids=lambda p: p.stem)
def test_key_parity(path: Path):
    locale = _load(path)
    assert set(locale) == set(_SOURCE), (
        f"{path.stem}: key mismatch "
        f"(missing={set(_SOURCE) - set(locale)}, extra={set(locale) - set(_SOURCE)})"
    )


@pytest.mark.parametrize("path", _NON_EN, ids=lambda p: p.stem)
def test_placeholder_parity(path: Path):
    locale = _load(path)
    for key, src_value in _SOURCE.items():
        assert _placeholders(locale[key]) == _placeholders(src_value), (
            f"{path.stem}: placeholder mismatch for '{key}'"
        )


@pytest.mark.parametrize("path", _NON_EN, ids=lambda p: p.stem)
def test_no_untranslated_leaks(path: Path):
    locale = _load(path)
    allow = _INTENTIONALLY_IDENTICAL | _COGNATE_IDENTICAL.get(path.stem, set())
    leaks = [
        key
        for key, src_value in _SOURCE.items()
        if key not in allow and locale[key] == src_value
    ]
    assert not leaks, f"{path.stem}: untranslated (identical to English): {leaks}"

#!/usr/bin/env python3
"""Report per-locale translation coverage (informational, not a gate).

The hard gates live in the tests (tests/unit/test_translations_parity.py and the
frontend i18n.test.js). A string counts as "translated" when it is present and
not byte-identical to its English source. Exit status is always 0.

    python3 ci/i18n-coverage.py            # human-readable table
    python3 ci/i18n-coverage.py --markdown # GitHub-comment table
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _ROOT / "custom_components" / "example_integration" / "translations"
_FRONTEND = _ROOT / "custom_components" / "example_integration" / "frontend" / "src" / "locales"


def _flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


def _coverage(directory: Path):
    en = _flatten(json.loads((directory / "en.json").read_text(encoding="utf-8")))
    rows = []
    for path in sorted(directory.glob("*.json")):
        if path.stem == "en":
            continue
        loc = _flatten(json.loads(path.read_text(encoding="utf-8")))
        translated = sum(
            1 for k, v in en.items() if k in loc and loc[k] != v
        )
        rows.append((path.stem, translated, len(en)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    for label, directory in (("Backend", _BACKEND), ("Frontend", _FRONTEND)):
        rows = _coverage(directory)
        if args.markdown:
            print(f"### {label} translation coverage\n")
            print("| Locale | Translated | Total | % |")
            print("|---|---|---|---|")
            for stem, n, total in rows:
                print(f"| {stem} | {n} | {total} | {100 * n // total if total else 0}% |")
            print()
        else:
            print(f"{label}:")
            for stem, n, total in rows:
                print(f"  {stem}: {n}/{total} ({100 * n // total if total else 0}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

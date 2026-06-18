#!/usr/bin/env python3
"""One-command rename of this template to your own integration.

Replaces the placeholder identifiers across the whole repo and renames the
component directory + seeded fixtures, so you can go from a fresh clone to your
own integration in one step:

    python scripts/rename.py your_domain "Your Name"
    # optional short CSS/symbol prefix (default: derived from the domain):
    python scripts/rename.py your_domain "Your Name" --prefix yp

What it changes (ordered, boundary-aware so it doesn't corrupt e.g. `flex-`):

    Example Integration  -> "Your Name"   display name
    example_integration  -> your_domain   domain, static path, ws, imports, paths
    example-integration  -> your-domain   panel URL path
    example-             -> your-domain-   web components + e2e dashboard
    Example              -> YourName       PascalCase symbols (ExampleStore, …)
    ex-                  -> <prefix>-       CSS classes / element ids
    ex_                  -> <prefix>_       the input_text event-capture helper

It also renames `custom_components/example_integration/` and the
`example-e2e.yaml` dashboard fixture.

After running: review `git diff`, then run the tests (see README). The script
does not touch the synthetic `ex` test package name in `tests/conftest.py`
(internal plumbing that works regardless of domain).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories never to descend into, and file suffixes treated as binary/derived.
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "test-results",
    "playwright-report",
    ".auth",
}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".zip"}
# The built bundles are gitignored/derived; never rewrite them.
SKIP_NAMES = {"example-panel.js", "example-card.js"}


def _pascal(display: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", display)
    pascal = "".join(p[:1].upper() + p[1:] for p in parts if p)
    if not pascal:
        sys.exit("error: display name must contain alphanumeric characters")
    return pascal


def _default_prefix(domain: str) -> str:
    parts = domain.split("_")
    if len(parts) > 1:
        return "".join(p[0] for p in parts if p)
    return domain[:2]


def build_replacements(domain: str, display: str, prefix: str) -> list[tuple[str, str]]:
    hyphen = domain.replace("_", "-")
    pascal = _pascal(display)
    # Order matters: longest / most-specific first.
    return [
        (r"Example Integration", display),
        (r"example_integration", domain),
        (r"example-integration", hyphen),
        (r"example-", f"{hyphen}-"),
        (r"Example", pascal),
        (r"\bex-", f"{prefix}-"),
        (r"\bex_", f"{prefix}_"),
    ]


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES or path.name in SKIP_NAMES:
            continue
        files.append(path)
    return files


def apply_to_text(text: str, replacements: list[tuple[str, str]]) -> str:
    for pattern, repl in replacements:
        text = re.sub(pattern, repl.replace("\\", r"\\"), text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", help="new snake_case domain, e.g. your_domain")
    parser.add_argument("display", help='new display name, e.g. "Your Name"')
    parser.add_argument(
        "--prefix",
        help="short CSS/id prefix (default: initials of the domain)",
    )
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.domain):
        sys.exit("error: domain must be lower_snake_case (start with a letter)")
    if args.domain == "example_integration":
        sys.exit("error: choose a domain other than the placeholder")

    prefix = args.prefix or _default_prefix(args.domain)
    if not re.fullmatch(r"[a-z][a-z0-9]*", prefix):
        sys.exit("error: --prefix must be lowercase letters/digits")

    replacements = build_replacements(args.domain, args.display, prefix)

    changed = 0
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text = apply_to_text(text, replacements)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1

    # Rename paths that carry the placeholder.
    hyphen = args.domain.replace("_", "-")
    renames = [
        (
            ROOT / "custom_components" / "example_integration",
            ROOT / "custom_components" / args.domain,
        ),
        (
            ROOT / "tests" / "integration" / "ha_config" / "example-e2e.yaml",
            ROOT / "tests" / "integration" / "ha_config" / f"{hyphen}-e2e.yaml",
        ),
    ]
    for src, dst in renames:
        if src.exists():
            src.rename(dst)

    # Replacing identifiers reflows some line lengths; tidy with ruff so the
    # result is immediately lint-clean (best-effort — skipped if ruff is absent).
    formatted = False
    if shutil.which("ruff"):
        subprocess.run(
            ["ruff", "format", "custom_components", "tests", "ci"],
            cwd=ROOT,
            capture_output=True,
        )
        subprocess.run(
            ["ruff", "check", "--fix", "custom_components", "tests", "ci"],
            cwd=ROOT,
            capture_output=True,
        )
        formatted = True

    print(f"Renamed to domain '{args.domain}' ({args.display}); prefix '{prefix}-'.")
    print(f"Rewrote {changed} files.")
    if not formatted:
        print("Install ruff and run `ruff format` to tidy reflowed lines.")
    print("Next: review `git diff`, then run the tests (see README).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""One-command rename of this template to your own integration.

Replaces the placeholder identifiers across the whole repo and renames the
component directory + seeded fixtures, so you can go from a fresh clone to your
own integration in one step:

    python scripts/rename.py your_domain "Your Name"
    # optional short CSS/symbol prefix (default: derived from the domain):
    python scripts/rename.py your_domain "Your Name" --prefix yp
    # optional repo slug — also rewrites README badges, manifest URLs, the docs
    # site URLs, and the maintainer handle to point at your fork:
    python scripts/rename.py your_domain "Your Name" --repo you/your-repo

What it changes (ordered, boundary-aware so it doesn't corrupt e.g. `flex-`):

    Example Integration  -> "Your Name"   display name
    example_integration  -> your_domain   domain, static path, ws, imports, paths
    example-integration  -> your-domain   panel URL path
    example-             -> your-domain-   web components + e2e dashboard
    Example              -> YourName       PascalCase symbols (ExampleStore, …);
                                           the plain word "Examples" is kept
    ex-                  -> <prefix>-       CSS classes / element ids
    ex_                  -> <prefix>_       the input_text event-capture helper

It also renames `custom_components/example_integration/` and the
`example-e2e.yaml` dashboard fixture, then:

* re-stamps the design docs (`python3 ci/docs.py stamp --all`), because each
  doc's `source_hash` covers files whose text the rename just changed;
* runs `ruff format` and `ruff check --fix`, and lists each line that is then
  longer than the line limit. A longer name can push a comment or a string past
  it, and no formatter can wrap those. Fix them by hand;
* lists each problem that `python3 ci/docs.py check` reports, such as a doc line
  that the longer name pushed past the docs cap.

It leaves itself alone: this script keeps the template placeholders, so it still
reads as a record of what it replaced.

It exits 1 when a step is left to do by hand (no ruff, unstamped docs, lines
that are too long, or a docs-check problem), and 0 when the rename is complete.

After running: review `git diff`, then run the tests (see README). The script
does not touch the synthetic `ex` test package name in `tests/unit/conftest.py`
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
    # Vale style packages fetched by `vale sync`. Synced dependency, not source.
    # The house style in styles/STE/ names no placeholder.
    "styles",
    # Local environments, caches and build output.
    ".venv",
    "mutants",
    ".stryker-tmp",
    "reports",
    ".hypothesis",
    ".docusaurus",
    "build",
    ".setup-ci-deps.lock",
}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".zip"}
# The built bundles are gitignored/derived; never rewrite them.
SKIP_NAMES = {"example-panel.js", "example-card.js"}
# This script keeps the placeholders it replaces. The path follows the script, so
# a fork that moves it keeps the skip.
SKIP_PATHS = {Path(__file__).resolve().relative_to(ROOT)}


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
        # Not the plain word "Examples" (a table header, a heading).
        (r"Example(?!s\b)", pascal),
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
        if path.relative_to(ROOT) in SKIP_PATHS:
            continue
        files.append(path)
    return files


def apply_to_text(text: str, replacements: list[tuple[str, str]]) -> str:
    for pattern, repl in replacements:
        text = re.sub(pattern, repl.replace("\\", r"\\"), text)
    return text


def exit_status(
    *, stamped: bool, formatted: bool, too_long: list[str], doc_problems: list[str]
) -> int:
    """0 when the rename is complete, 1 when a step is left to do by hand.

    The rewrite and the directory renames are done either way. A non-zero status
    tells a caller (a script, CI, an agent) that the result does not pass the gates
    yet: the design docs are not stamped, ruff did not run, or lines are too long.
    """
    return 0 if stamped and formatted and not too_long and not doc_problems else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", help="new snake_case domain, e.g. your_domain")
    parser.add_argument("display", help='new display name, e.g. "Your Name"')
    parser.add_argument(
        "--prefix",
        help="short CSS/id prefix (default: initials of the domain)",
    )
    parser.add_argument(
        "--repo",
        help="repo slug OWNER/NAME — rewrites README badges, manifest URLs, and "
        "the maintainer handle to your fork (default: leave the template's)",
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

    if args.repo:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
            sys.exit("error: --repo must be OWNER/NAME")
        owner = args.repo.split("/")[0]
        # The full slug carries the repo identity in badges, manifest URLs, and the
        # card's documentationURL; the @handle / %40handle carry the maintainer.
        name = args.repo.split("/")[1]
        replacements += [
            # The docs site: GitHub Pages serves it at <owner>.github.io/<name>.
            (
                re.escape("prestomation.github.io/ha-integration-template"),
                f"{owner.lower()}.github.io/{name}",
            ),
            (re.escape("prestomation/ha-integration-template"), args.repo),
            (re.escape("%40prestomation"), f"%40{owner}"),
            (r"@prestomation\b", f"@{owner}"),
        ]

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
    # result is lint-clean (best-effort — skipped if ruff is absent).
    formatted = False
    too_long: list[str] = []
    if shutil.which("ruff"):
        paths = ["custom_components", "tests", "ci", "scripts"]
        subprocess.run(["ruff", "format", *paths], cwd=ROOT, capture_output=True)
        subprocess.run(
            ["ruff", "check", "--fix", *paths], cwd=ROOT, capture_output=True
        )
        # A comment or a string that the longer name pushed past the limit cannot
        # be wrapped by a formatter. List each one, so it is fixed by hand.
        report = subprocess.run(
            ["ruff", "check", "--select", "E501", "--output-format", "concise", *paths],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        too_long = [line for line in report.stdout.splitlines() if ": E501 " in line]
        formatted = True

    # Each design doc hashes the files it describes, and the rename and ruff
    # changed them. Stamp last, after every rewrite.
    stamped = (
        subprocess.run(
            [sys.executable, "ci/docs.py", "stamp", "--all"],
            cwd=ROOT,
            capture_output=True,
        ).returncode
        == 0
    )
    # A longer name can also push a doc line past the docs cap. Report each problem.
    docs = subprocess.run(
        [sys.executable, "ci/docs.py", "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    doc_problems = (
        [line for line in docs.stdout.splitlines() if line.startswith("[")]
        if stamped
        else []
    )

    print(f"Renamed to domain '{args.domain}' ({args.display}); prefix '{prefix}-'.")
    print(f"Rewrote {changed} files.")
    if not stamped:
        print("Run `python3 ci/docs.py stamp --all` to re-stamp the design docs.")
    if not formatted:
        print("Install ruff and run `ruff format` to tidy reflowed lines.")
    if doc_problems:
        print("`python3 ci/docs.py check` reports these problems. Fix them by hand:")
        for line in doc_problems:
            print(f"  {line}")
    if too_long:
        print("These lines are now too long. Wrap them by hand:")
        for line in too_long:
            print(f"  {line}")
    status = exit_status(
        stamped=stamped,
        formatted=formatted,
        too_long=too_long,
        doc_problems=doc_problems,
    )
    if status:
        print("The rename is not complete. Do the steps above, then run the tests.")
    else:
        print("Next: review `git diff`, then run the tests (see README).")
    return status


if __name__ == "__main__":
    raise SystemExit(main())

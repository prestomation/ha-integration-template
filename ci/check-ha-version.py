#!/usr/bin/env python3
"""Report the installed Home Assistant version; fail if pip backtracked to an old one.

Any CI job that ``pip install``s Home Assistant can silently end up testing an
*ancient* release, and nothing in the log says so:

``pip install homeassistant`` does not fail when the runner's Python predates Home
Assistant's floor — it backtracks to the last release that still supported that
Python. So a runner pinned to an old minor version resolves an HA from months ago,
and mypy dutifully type-checks against an API no user runs. The job goes green
having checked nothing that matters.

(The companion trap: ``homeassistant.__version__`` does not exist —
``homeassistant/__init__.py`` is a one-line docstring, and the version lives in
``homeassistant.const``. A step that reads the wrong attribute dies with an
``AttributeError`` and takes the suite that follows it down with it, which is why
diagnostic steps like this one belong under ``continue-on-error`` everywhere except
the job whose whole point is the version.)

Usage:
    python3 ci/check-ha-version.py            # newest stable is expected
    python3 ci/check-ha-version.py --pre      # newest pre-release is expected

Exit status is 1 when the installed version is older than the newest one PyPI offers
for the requested channel, 0 otherwise. When PyPI is unreachable the version is still
reported and the check is skipped — this must not turn a network blip into a red CI.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request

from packaging.version import InvalidVersion, Version

_PYPI = "https://pypi.org/pypi/homeassistant/json"


def _installed() -> Version:
    # The whole point of the script: read it from where it actually lives.
    from homeassistant.const import __version__

    return Version(__version__)


def newest(releases: dict[str, list[dict]], allow_prerelease: bool) -> Version | None:
    """Pick the newest installable version from a PyPI ``releases`` mapping.

    Kept pure and separate from the fetch so it is unit-testable — a version check
    that is itself wrong fails exactly as silently as the bug it guards against.
    """
    candidates = []
    for raw, files in releases.items():
        # A fileless or fully-yanked release cannot be what pip installed.
        if not files or all(f.get("yanked") for f in files):
            continue
        try:
            version = Version(raw)
        except InvalidVersion:
            continue
        if version.is_prerelease and not allow_prerelease:
            continue
        candidates.append(version)

    return max(candidates, default=None)


def _newest_on_pypi(allow_prerelease: bool) -> Version | None:
    try:
        with urllib.request.urlopen(_PYPI, timeout=30) as response:
            releases = json.load(response)["releases"]
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as err:
        print(f"Could not reach PyPI to verify the version ({err}) — skipping check.")
        return None

    return newest(releases, allow_prerelease)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pre",
        action="store_true",
        help="expect the newest pre-release (for jobs using `pip install --pre`)",
    )
    args = parser.parse_args()

    installed = _installed()
    latest = _newest_on_pypi(args.pre)

    channel = "pre-release" if args.pre else "stable"
    if latest is None:
        print(f"HA {installed}")
        return 0

    print(f"HA {installed} (newest {channel} on PyPI: {latest})")
    if installed < latest:
        print(
            f"::error::pip resolved Home Assistant {installed}, but {latest} is "
            f"the newest {channel}. This job is testing a stale Home Assistant. "
            "The usual cause is the runner's Python being older than Home "
            "Assistant's floor, which makes pip backtrack instead of failing."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

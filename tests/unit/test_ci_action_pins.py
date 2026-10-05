"""A third-party action in a job that holds a write token is pinned to a commit.

A job with no ``permissions`` block counts as a write job, because it gets the
repository default token. A tag such as ``@v1`` can move. Whoever controls the
action's repository can point it at new code, and that code then runs with the
job's write token. A commit SHA cannot move. ``actions/*`` (GitHub's own) and
local ``./`` workflows are exempt.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
_PINNED = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def _writes(permissions: object) -> bool:
    # No permissions block means the repository default token, which can write.
    # A reusable workflow with no block takes the caller's token, which can too.
    if permissions is None or permissions == "write-all":
        return True
    return isinstance(permissions, dict) and "write" in permissions.values()


def _unpinned(path: Path) -> list[str]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    top = doc.get("permissions")
    found = []
    for name, job in (doc.get("jobs") or {}).items():
        perms = job.get("permissions", top)
        if not _writes(perms):
            continue
        for step in job.get("steps") or []:
            uses = step.get("uses", "")
            if not uses or uses.startswith(("actions/", "./")):
                continue
            if not _PINNED.match(uses):
                found.append(f"{path.name} {name}: {uses}")
    return found


@pytest.mark.parametrize("path", sorted(_WORKFLOWS.glob("*.yml")), ids=lambda p: p.name)
def test_third_party_actions_with_a_write_token_are_pinned(path: Path) -> None:
    assert _unpinned(path) == []


def test_the_check_sees_an_unpinned_action(tmp_path: Path) -> None:
    workflow = tmp_path / "w.yml"
    workflow.write_text(
        "permissions:\n  contents: read\n"
        "jobs:\n"
        "  publish:\n"
        "    permissions:\n      contents: write\n"
        "    steps:\n"
        "      - uses: someone/action@v1\n"
        "      - uses: someone/action@" + "a" * 40 + "\n"
        "      - uses: actions/checkout@v7\n"
        "  build:\n"
        "    steps:\n      - uses: someone/other@v2\n"
    )
    assert _unpinned(workflow) == ["w.yml publish: someone/action@v1"]


def test_a_job_with_no_permissions_block_counts_as_a_write_job() -> None:
    assert _writes(None)
    assert _writes("write-all")
    assert _writes({"contents": "read", "issues": "write"})
    assert not _writes({"contents": "read"})
    assert not _writes("read-all")

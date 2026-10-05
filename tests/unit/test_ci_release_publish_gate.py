"""The release workflow publishes only from main, and never on a dry run.

Without the gate, a ``notify_dry_run`` dispatch on a branch whose manifest version
has no tag runs the full release job: it tags the branch head, publishes a GitHub
Release and deploys the docs. The publish decision is one step, run here with bash,
and every publishing step and job must read it.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

_WORKFLOW = (
    Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release.yml"
)


def _doc() -> dict:
    return yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))


def _steps() -> list[dict]:
    return _doc()["jobs"]["release"]["steps"]


def _step(step_id: str) -> dict:
    return next(s for s in _steps() if s.get("id") == step_id)


def _publish(tmp_path: Path, event: str, ref: str, dry_run: str) -> str:
    out = tmp_path / "out"
    out.write_text("")
    env = {
        **os.environ,
        "EVENT": event,
        "REF": ref,
        "DRY_RUN": dry_run,
        "GITHUB_OUTPUT": str(out),
    }
    subprocess.run(
        ["bash", "-c", _step("publish")["run"]],
        env=env,
        check=True,
        capture_output=True,
    )
    return out.read_text().strip()


@pytest.mark.parametrize(
    ("event", "ref", "dry_run", "expected"),
    [
        ("push", "refs/heads/main", "", "publish=true"),
        ("workflow_dispatch", "refs/heads/main", "false", "publish=true"),
        ("workflow_dispatch", "refs/heads/main", "true", "publish=false"),
        ("workflow_dispatch", "refs/heads/release-0.27.0", "true", "publish=false"),
        ("workflow_dispatch", "refs/heads/release-0.27.0", "false", "publish=false"),
        ("pull_request", "refs/pull/1/merge", "", "publish=false"),
        ("push", "refs/heads/feature", "", "publish=false"),
    ],
)
def test_publish_decision(tmp_path, event, ref, dry_run, expected) -> None:
    assert _publish(tmp_path, event, ref, dry_run) == expected


def test_tag_and_release_steps_read_the_decision() -> None:
    by_name = {s.get("name"): s for s in _steps()}
    for name in ("Create and push tag", "Create GitHub Release"):
        cond = by_name[name]["if"]
        assert "steps.publish.outputs.publish == 'true'" in cond, name
        assert "github.event_name != 'pull_request'" not in cond, name


def test_jobs_read_the_decision() -> None:
    jobs = _doc()["jobs"]
    assert (
        jobs["release"]["outputs"]["publish"] == "${{ steps.publish.outputs.publish }}"
    )
    assert "needs.release.outputs.publish == 'true'" in jobs["deploy-docs"]["if"]
    assert "needs.release.outputs.publish == 'true'" in jobs["notify-issues"]["if"]


def _target(tmp_path: Path, **env: str) -> tuple[int, str]:
    """Run the notify-issues "Resolve the version" step with bash."""
    job = _doc()["jobs"]["notify-issues"]
    step = next(s for s in job["steps"] if s.get("id") == "target")
    out = tmp_path / "out"
    out.write_text("")
    result = subprocess.run(
        ["bash", "-c", step["run"]],
        env={**os.environ, "GITHUB_OUTPUT": str(out), **env},
        capture_output=True,
        cwd=tmp_path,
    )
    return result.returncode, out.read_text()


def test_a_release_notifies_with_the_release_jobs_own_prerelease(tmp_path) -> None:
    # One source of truth: the release job published the GitHub release with this
    # flag, so the issue notices follow it, even if a second regex would disagree.
    for version, prerelease in (("0.2.0", "true"), ("0.2.0b1", "false")):
        status, out = _target(
            tmp_path,
            DISPATCH_VERSION="",
            RELEASE_VERSION=version,
            RELEASE_PRERELEASE=prerelease,
        )
        assert status == 0
        assert f"prerelease={prerelease}" in out.split()


def test_a_release_without_a_prerelease_flag_notifies_nobody(tmp_path) -> None:
    status, out = _target(
        tmp_path, DISPATCH_VERSION="", RELEASE_VERSION="0.2.0", RELEASE_PRERELEASE=""
    )
    assert status == 1
    assert "prerelease=" not in out


def test_a_dry_run_derives_prerelease_from_its_own_version(tmp_path) -> None:
    status, out = _target(
        tmp_path,
        DISPATCH_VERSION="0.1.0b2",
        RELEASE_VERSION="0.3.0",
        RELEASE_PRERELEASE="false",
    )
    assert status == 0
    assert {"version=0.1.0b2", "prerelease=true"} <= set(out.split())


def test_an_empty_version_notifies_nobody(tmp_path) -> None:
    status, out = _target(
        tmp_path, DISPATCH_VERSION="", RELEASE_VERSION="", RELEASE_PRERELEASE=""
    )
    assert status == 1
    assert out == ""

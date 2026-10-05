"""Unit tests for ``scripts/rename.py``.

The script runs once, on a fresh fork, so a fault in it shows only to the person who
forks the template. These tests load it from a copy in a temporary root, so they never
rewrite the real repository.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "rename.py"
# The display-name placeholder, built from pieces so that a rename of this repository
# does not rewrite it here. The renamed script still replaces the placeholder.
_PLACEHOLDER = "".join(["Exam", "ple Integration"])


def _load(root: Path, folder: str = "scripts"):
    """Copy the script to ``root/<folder>/rename.py`` and import that copy."""
    target = root / folder / "rename.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(_SCRIPT, target)
    spec = importlib.util.spec_from_file_location(f"rename_{folder}", target)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("folder", ["scripts", "tools"])
def test_the_script_never_rewrites_itself(tmp_path: Path, folder: str) -> None:
    # The skip follows the script, so a fork that moves it keeps the skip.
    rename = _load(tmp_path, folder)
    (tmp_path / "README.md").write_text(f"{_PLACEHOLDER}\n")
    files = {p.relative_to(tmp_path).as_posix() for p in rename.iter_files()}
    assert "README.md" in files
    assert f"{folder}/rename.py" not in files


def _main(rename, monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr(sys, "argv", ["rename.py", "demo_thing", "Demo Thing"])
    return rename.main()


def test_a_rename_without_ruff_exits_non_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    rename = _load(tmp_path)
    (tmp_path / "README.md").write_text(f"{_PLACEHOLDER}\n")
    monkeypatch.setattr(rename.shutil, "which", lambda name: None)
    assert _main(rename, monkeypatch) == 1
    out = capsys.readouterr().out
    assert "Install ruff" in out
    assert "The rename is not complete" in out
    # The rewrite itself still happened.
    assert (tmp_path / "README.md").read_text() == "Demo Thing\n"


@pytest.mark.parametrize(
    ("stamped", "formatted", "too_long", "doc_problems", "expected"),
    [
        (True, True, [], [], 0),
        (False, True, [], [], 1),
        (True, False, [], [], 1),
        (True, True, ["a.py:1:89: E501 Line too long"], [], 1),
        (True, True, [], ["[length] README.md:1: line has 101 characters"], 1),
    ],
)
def test_exit_status_is_non_zero_while_work_remains(
    tmp_path: Path, stamped, formatted, too_long, doc_problems, expected
) -> None:
    rename = _load(tmp_path)
    status = rename.exit_status(
        stamped=stamped,
        formatted=formatted,
        too_long=too_long,
        doc_problems=doc_problems,
    )
    assert status == expected

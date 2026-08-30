"""Unit tests for ``ci/check-changelog-release-gap.py``.

The script catches a change folded into a CHANGELOG section whose version has
already been tagged and released, so ``release.yml`` sees nothing new and silently
skips publishing it. ``check()`` is pure — the git/tag lookups are injected — so the
cases it has to tell apart are pinned here without touching a real repository.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "ci" / "check-changelog-release-gap.py"


def _load():
    # The filename has a hyphen, so it is not importable as a module name.
    spec = importlib.util.spec_from_file_location(
        "check_changelog_release_gap", _SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
top_version = _mod.top_version
section = _mod.section
check = _mod.check


class TestTopVersion:
    def test_reads_the_first_heading(self):
        text = "# Changelog\n\n## [0.3.0]\n\nstuff\n\n## [0.2.0]\n\nolder\n"
        assert top_version(text) == "0.3.0"

    def test_ignores_a_version_mentioned_in_prose(self):
        text = "# Changelog\n\nSee 0.1.0 for history.\n\n## [0.2.0]\n\nstuff\n"
        assert top_version(text) == "0.2.0"

    def test_no_heading_at_all(self):
        assert top_version("# Changelog\n\nnothing here\n") is None


class TestSection:
    def test_stops_at_the_next_version_heading(self):
        text = "## [0.3.0]\n\n- new\n\n## [0.2.0]\n\n- old\n"
        assert section(text, "0.3.0") == "## [0.3.0]\n\n- new\n\n"
        assert section(text, "0.2.0") == "## [0.2.0]\n\n- old\n"

    def test_keeps_subsections_inside_the_version(self):
        # `### Added` must not terminate the section -- only `## [` does.
        text = "## [0.3.0]\n\n### Added\n\n- new\n\n## [0.2.0]\n\n- old\n"
        assert "### Added" in section(text, "0.3.0")
        assert "0.2.0" not in section(text, "0.3.0")

    def test_absent_version_yields_empty(self):
        assert section("## [0.3.0]\n\n- new\n", "9.9.9") == ""


class TestCheck:
    def test_version_bumped_is_always_clean(self):
        base = "## [0.2.0]\n\nold entry\n"
        head = "## [0.3.0]\n\nnew entry\n"
        assert check(base, head, tag_exists=lambda v: True) is None

    def test_version_bump_short_circuits_before_checking_any_tag(self):
        # base_version != head_version names two different sections -- there is
        # nothing to compare them for, so tag_exists() must never even be asked.
        def tag_exists(version: str) -> bool:
            raise AssertionError("tag_exists() called despite a version bump")

        base = "## [0.2.0]\n\nold entry\n"
        head = "## [0.3.0]\n\nold entry\n"  # identical body, only the heading moved
        assert check(base, head, tag_exists=tag_exists) is None

    def test_unchanged_section_on_a_released_version_is_clean(self):
        text = "## [0.2.0]\n\nsame entry\n"
        assert check(text, text, tag_exists=lambda v: True) is None

    def test_new_entry_folded_into_an_unreleased_version_is_clean(self):
        # The normal workflow: several PRs land into the same unreleased section
        # before it is ever tagged.
        base = "## [0.3.0]\n\nfirst entry\n"
        head = "## [0.3.0]\n\nfirst entry\nsecond entry\n"
        assert check(base, head, tag_exists=lambda v: False) is None

    def test_new_entry_folded_into_an_already_released_version_fails(self):
        base = "## [0.2.0]\n\nfirst entry\n"
        head = "## [0.2.0]\n\nfirst entry\nsecond entry\n"
        message = check(base, head, tag_exists=lambda v: True)
        assert message is not None
        assert "0.2.0" in message

    def test_removing_a_line_from_a_released_section_also_fails(self):
        # Any edit is unshippable, not just an addition -- a correction to a
        # released section goes nowhere just as quietly.
        base = "## [0.2.0]\n\nfirst entry\nsecond entry\n"
        head = "## [0.2.0]\n\nfirst entry\n"
        assert check(base, head, tag_exists=lambda v: True) is not None

    def test_edit_below_the_top_section_is_ignored(self):
        # Only the section release.yml would publish next is in scope; fixing a
        # typo in an old release's notes must not fail the PR.
        base = "## [0.3.0]\n\ncurrent\n\n## [0.2.0]\n\nold entry\n"
        head = "## [0.3.0]\n\ncurrent\n\n## [0.2.0]\n\nold entry, corrected\n"
        assert check(base, head, tag_exists=lambda v: True) is None

    def test_checks_the_version_that_was_actually_edited(self):
        calls: list[str] = []

        def tag_exists(version: str) -> bool:
            calls.append(version)
            return True

        base = "## [0.2.0]\n\nfirst entry\n"
        head = "## [0.2.0]\n\nfirst entry\nsecond entry\n"
        check(base, head, tag_exists=tag_exists)
        assert calls == ["0.2.0"]

    def test_missing_top_heading_on_either_side_is_clean(self):
        head = "## [0.2.0]\n\nx\n"
        assert check("no heading", head, lambda v: True) is None
        assert check(head, "no heading", lambda v: True) is None

    def test_a_prerelease_is_covered_too(self):
        # The guard is not stable-only: a published beta hits the same bug.
        base = "## [0.3.0b1]\n\nfirst entry\n"
        head = "## [0.3.0b1]\n\nfirst entry\nsneaked-in entry\n"
        assert check(base, head, tag_exists=lambda v: True) is not None

<!--
Link the issue this fixes with `Fixes #N` below.

Turn closing-on-merge off for the repository, so the keyword links the PR to the
issue without closing it. The issue stays open until the fix ships, and release.yml's
notify-issues job closes it on the release that carries it. The reporter's "closed"
notification then names a version that they can install.

For that to happen the issue also needs a `(Fixes #N)` line in the CHANGELOG entry:
that section is what the release reads to decide who gets told.

The plan for the change lives in this body. Start it with the CHANGELOG bullet that
the change ships. See .amazonq/rules/pr-workflow.md.
-->

Fixes #

## What changed

## One-way doors

<!-- Each external contract this change commits to. See .amazonq/rules/pr-workflow.md. -->

## Security

<!-- 1 row for each surface this change adds or changes: admin-only or open, and why. -->
<!-- See .amazonq/rules/pr-workflow.md. Write "No surface changed" if there is none. -->

| Surface | Before | After | Rule | What a user who is not an admin can now do |
| --- | --- | --- | --- | --- |

## Screenshots

<!-- For a panel or card change: a desktop and a phone shot of each changed surface,
     as HTML <img> tags with SHA-pinned raw.githubusercontent.com URLs. Delete this
     section if the change has no UI. -->

## Checklist

- [ ] Tests run locally (`pytest tests/unit`, `bash ci/test-python-component.sh`,
      `bash ci/test-frontend.sh`), and `ruff check` and `ruff format --check` pass
- [ ] `CHANGELOG.md` updated: user-facing changes only, with `(Fixes #N)` for each
      issue this fixes, in a section whose version is not already tagged
- [ ] Panel or card UI changed: desktop and phone screenshots committed under
      `docs/images/`, read, embedded above, and asserted on in `tests/e2e/tests/`
- [ ] New user-facing UI surface: `tests/e2e/walkthrough.capture.ts` extended to step
      through it
- [ ] New user-facing feature: version bumped to the next beta (`manifest.json` +
      `const.py`), `preview-release` label applied, and a page in `docs/guide/`
- [ ] New integrator-facing surface: declared in `api_surface.py`, with `services.yaml`
      and `strings.json` text at translation parity, and `docs/EVENTS.md` for an event
- [ ] `python3 ci/docs.py check` is clean. For each design doc re-stamped, say if
      its text changed, or why the code change needs no doc change
- [ ] A design doc's Goals or Non-goals changed: a **Goal changes** section below
      that says what changed and that the maintainer agreed
- [ ] The **Security** section lists each changed surface as admin-only or open, and
      `api_surface.py` and `docs/SECURITY.md` agree with it
- [ ] New prose follows `.amazonq/rules/writing-style.md` and reads clean under vale
- [ ] `/q review` requested after the last push

# Releasing

`manifest.json` `version` is the **single source of truth**. The release workflow
(`.github/workflows/release.yml`) runs on every push to `main` and tags + publishes a
GitHub Release when the version is new.

## Cutting a release

1. Open a release PR that:
   - bumps `version` in `custom_components/example_integration/manifest.json`,
   - bumps `PANEL_VERSION` in `custom_components/example_integration/const.py` to the
     **same** string (the release workflow asserts they match), and
   - adds a `## [X.Y.Z]` section to `CHANGELOG.md`.
2. Merge (squash). On the push to `main`, `release.yml`:
   - validates `version` format, `version == PANEL_VERSION`, and the changelog
     section exists,
   - builds the frontend bundles and the distributable zip,
   - creates tag `vX.Y.Z` and a GitHub Release with the changelog section as notes.

## Pre-releases (HACS beta channel)

A PEP 440 pre-release suffix ships as a GitHub **pre-release**, which HACS only
offers to users who enabled "Show beta versions":

- `0.2.0b1` (beta), `0.2.0rc1` (release candidate), `0.2.0a1` (alpha).

Stable `X.Y.Z` ships as a normal release.

## Notes

- The built `example-panel.js` / `example-card.js` are gitignored; CI builds them
  for the release zip.
- A stable release's notes describe what changed since the previous **stable**
  release — roll any intervening beta work into Added/Changed/Fixed as users perceive
  it.

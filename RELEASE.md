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

## Preview releases (test a PR build without merging)

Sometimes you want to **install and try a PR's build via HACS** before merging it —
without bumping the version or cutting a real release. Add the **`preview-release`**
label to the PR and `preview-release.yml` builds the frontend bundles +
`example_integration.zip` from the PR head, stamps a synthetic version
(`X.Y.Z.dev<pr>`) into the zip's manifest, and publishes an **ephemeral GitHub
pre-release** with the zip attached. Install it from HACS: open *Example Integration*
→ ⋮ → **Redownload**, enable **Show beta versions**, and pick `X.Y.Z.dev<pr>` (or
download `example_integration.zip` from the release and unzip into
`config/custom_components/example_integration/`).

- **Opt-in only** — nothing happens without the label (and only users with write
  access can label).
- **Same-repo PRs only** — fork PRs get no token and are not built this way.
- **Owner approval** — the publish job runs in the `preview-release` GitHub
  Environment; add **Required reviewers** to it (Settings → Environments) to make each
  build wait for an explicit approval.
- **Ephemeral & low-noise** — it's a **pre-release** (`prerelease: true`), so it's
  offered only to users who enabled *Show beta versions*; the `.dev<pr>` version sorts
  *below* the real `X.Y.Z` release so it never nags anyone as an update; it's
  re-published on each push and **deleted automatically when the PR closes**.

> When you rename the template (`scripts/rename.py`), update `preview-release.yml`
> to replace `example_integration` / `Example Integration` with your domain / display
> name.

## Notes

- The built `example-panel.js` / `example-card.js` are gitignored; CI builds them
  for the release zip.
- A stable release's notes describe what changed since the previous **stable**
  release — roll any intervening beta work into Added/Changed/Fixed as users perceive
  it.

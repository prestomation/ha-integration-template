# Testing & workflow conventions

## Git & PR workflow
- Never push directly to `main`. Work on a feature branch and open a PR; squash
  merge.
- Update `CHANGELOG.md` for every user-facing change before a release. **Never add an
  entry to a section whose version is already tagged** — `release.yml` keys off an
  unchanged `manifest.json` version and skips, so the entry never ships. Bump the
  version and open a new section instead. `lint.yml`'s `changelog-release-gap` job
  (`ci/check-changelog-release-gap.py`) enforces it; folding into a section that is
  not yet tagged stays the normal workflow.
- **User-facing prose is vale-linted for AI-writing tells**, diff-scoped to the lines
  a PR touches: `README.md`, `CHANGELOG.md`, `docs/*.md`, `strings.json`,
  `services.yaml`, and the English frontend locale. Config and the pinned style
  package are in `.vale.ini`. Run `vale sync && vale <paths>` locally, but do not
  treat a clean local run as proof CI is clean — the action pins its own binary.
- Post screenshots to the PR for any change that adds/changes/fixes UI (capture via
  `tests/e2e/screenshots.capture.ts`, commit under `docs/images/`, embed via a
  `raw.githubusercontent.com/.../<commit-sha>/docs/images/<file>.png` URL in an
  HTML `<img>` tag — not markdown). Look at every PNG before committing it, and
  remember that **a screenshot is documentation, not verification**: a capture
  renders a bug as faithfully as it renders correct output. When a capture adds a
  surface, add an assertion on that surface under `tests/e2e/tests/` in the same PR.
- **Video walkthrough (per-PR, CI-generated, never committed).** `walkthrough-preview.yml`
  runs the capture harness (`tests/e2e/videos.capture.ts`) on every PR, transcodes
  to gif+mp4 via `ci/capture-video.sh` (needs `ffmpeg`), publishes them to an orphan
  **`gh-pages`** branch (`pr-preview-media/pr-<n>/`, via `rossjrw/pr-preview-action`),
  and posts/updates a **sticky comment that embeds the gif inline** via a
  `raw.githubusercontent.com` URL (the same mechanism the screenshot gate uses — so
  **no GitHub Pages setup is required**; a `?v=<sha>` query busts the raw/camo cache).
  `docs/videos/` is gitignored and media never touches `main` — nothing lands in git
  history. The gate for a feature that adds a new UI surface is *editing the tour* in
  `videos.capture.ts` (with `BEAT` pauses) in the same PR; it's a **soft gate**
  (`continue-on-error`) so a flaky run doesn't block. Debug locally with
  `KEEP_UP=1 bash ci/e2e-up.sh` then `bash ci/capture-video.sh`. The mp4 is linked
  rather than inline (only a drag-drop `user-attachments` upload inline-plays an mp4,
  which CI can't produce); the gif carries the motion.
- **Document new major features in `README.md` in the same change** — use cases +
  how it's used + screenshot(s) embedded with a relative `docs/images/…` path. (The
  moving walkthrough stays the per-PR CI comment, not the README.)

## The four test tiers (run locally before pushing — never use CI as the runner)
Cheapest first. **Tiers 2 and 3 must run in separate environments** (socket rule).

1. **Pure unit** (`tests/unit`, `pip install pytest`): the pure core
   (`models.py`, `events.py`) and translation parity. Loaded in isolation via the
   synthetic `ex` package in `tests/unit/conftest.py` — these never import HA.
   That conftest *executes* the modules under their real dotted name
   (`custom_components.example_integration.<mod>`, with stub parent packages so
   the HA-importing `__init__.py` never runs) and registers `ex.<mod>` as an
   alias. **Keep it that way**: mutmut matches a mutant's path-derived key
   against the function's `__module__`, so executing them as `ex.<mod>` would
   make every mutant look untested and abort the mutation run. **And keep it in
   `tests/unit/`** — as a root conftest the stub packages would shadow the real
   integration for tier 2, where HA imports the package itself.
2. **Component / in-process HA** (`tests/component`,
   `pytest-homeassistant-custom-component` + `home-assistant-frontend`): real
   `hass`, registries, config entries, I/O mocked. Covers `config_flow`,
   setup/unload, store, coordinator, sensor entities, services, **bus events**
   (`async_capture_events`), websocket commands. Run with `asyncio_mode=auto`
   (`ci/test-python-component.sh`).
3. **Docker integration** (`tests/integration`): a real running HA container over
   REST/WS. Covers end-to-end loading, served bundles, event observability via an
   automation. Bring up with `bash ci/e2e-up.sh`; run with
   `ci/test-python-integration.sh`.
4. **Frontend (vitest)** + **Browser e2e (Playwright)**: `utils`/i18n parity, and
   the panel + card smoke tests / screenshot capture.

### Choosing the tier for "real HA"
HA-coupled logic belongs in the **component** tier — it *is* real HA and ~100×
faster than Docker, and can assert internal state (entity attributes, registry
entries, that an event fired) that REST can't. Reserve the **Docker** tier for what
the in-process harness can't do: serving the JS bundles, registering the panel/card
resources, full-stack REST behavior. Don't write "Docker unit tests".

### Socket isolation (hard constraint)
`pytest-homeassistant-custom-component` pulls in `pytest-socket`, which blocks the
real network. The component tier and the Docker integration tier therefore **cannot
share a pytest invocation**:
- The component step installs the HA harness.
- The integration step does **not** install it and passes `-p no:pytest_socket`.
Keep them in separate dirs and separate CI steps.

### Local-run hygiene
- The Docker/e2e tiers seed a config entry at
  `tests/integration/ha_config/.storage/core.config_entries` so the integration
  loads at HA startup (required for the dashboard card resource to be injected).
  That's the only tracked `.storage` file; HA mutates it at runtime, so restore the
  committed fixture with `git checkout` after a local run and don't commit the
  runtime version. Everything else under `.storage/` is gitignored.
  `tests/unit/test_integration_fixture_clean.py` fails when a runtime-written key
  reaches git — the dirty fixture keeps passing locally against the container that
  dirtied it, and only breaks on a pristine checkout.
- **A unit test that reads a repo file off disk needs that file's directory in
  `[tool.mutmut] also_copy`.** mutmut runs the suite in a `mutants/` copy holding
  only the source paths and the tests, so a test loading `ci/check-ha-version.py` by
  path dies at collection there. It only breaks a PR that *also* changes mutable
  Python, so the failure hides for months. List the directory, not the file: mutmut
  `copy2`s a bare file without creating its parent.
- `asyncio_mode` is set per-invocation by the component/integration runners (it
  needs `pytest-asyncio`, which only the HA harness installs) — not in the root
  `pyproject.toml`, so the pure unit tier stays dependency-light.

## Mutation testing (the fifth tier — a PR gate)
Coverage proves a line *ran*; mutation testing proves a test would have *failed*
had that line been wrong. `mutation.yml` runs on every PR and scores only the code
the branch touched.

- **Runners:** `ci/test-mutation-python.sh` (mutmut, against `tests/unit`) and
  `ci/test-mutation-frontend.sh` (Stryker, against vitest). Both take `--changed`
  (default) or `--all`.
- **The surface is an allowlist, in one place per language:** `only_mutate` in
  `[tool.mutmut]` (pyproject.toml) and `mutate` in `stryker.conf.json`. It holds
  only what the *fast* tiers cover — the pure Python core, and `utils.ts` /
  `i18n.ts`. HA-coupled modules and the DOM-heavy `panel.ts`/`card.ts` are out:
  mutating them means re-running the component or Docker tier thousands of times
  for a score that mostly reports "no test covers this".
- **Diff scoping:** `ci/mutation_scope.py` turns the diff into mutmut mutant-name
  filters (changed line → enclosing function, via `ast`) and Stryker `--mutate`
  line ranges. Scoping to whole files would fail a PR for pre-existing debt.
- **The gate is 80%**, defined in `[tool.mutation-gate] break` and mirrored in
  `thresholds.break` (stryker.conf.json) — **keep the two equal**. `--all` may sit
  below it while the surface is still being brought up; the PR gate is what must
  stay green.
- **Surviving mutants are a test gap, not a formality.** Kill them with a real
  assertion. When a mutant is genuinely *equivalent* (the mutation cannot change
  observable behaviour), annotate it at the source — `# pragma: no mutate`,
  `// Stryker disable next-line <mutator>` — **with a one-line reason**. Never
  blanket-disable a file, and never lower the threshold to get green.
- **Tests that read source off disk must be `*-parity.test.js`.** Under Stryker
  they would read *mutated* text and go red for mutants they never exercised,
  inflating the score; `vitest.stryker.config.js` excludes that suffix. Keep
  static-analysis gates in those files and behavioural tests out of them.
- Label a PR `skip-mutation` to bypass both jobs (for revert/infra PRs).

## Linting (ruff)
Python is linted + formatted with **ruff** (config in `pyproject.toml`, enforced by
`lint.yml`). Keep `ruff check custom_components tests ci scripts` and `ruff format
--check …` clean before pushing. When identifiers reflow lines (e.g. after using
`scripts/rename.py`), run `ruff format`.

## Translations (quality gates)
`strings.json` (backend) and `frontend/src/locales/en.json` are the sources of
truth, guarded by `tests/unit/test_translations_parity.py` and
`frontend/test/i18n.test.js`. For every locale they enforce:
- **Key parity** — identical key structure to English (no missing/extra).
- **Placeholder parity** — same `{token}` set per key.
- **No untranslated leaks** — a value byte-identical to English is a hard failure;
  the only escape hatch is a small reviewed `INTENTIONALLY_IDENTICAL` /
  `COGNATE_IDENTICAL` allowlist (e.g. "Name" in German).
- **Key usage** (frontend) — every `t()`/`tn()` key exists in `en.json`; `tn()`
  bases have an `.other` form; no unused keys.
Adding a string to a locale means translating it or justifying the cognate —
never leaving it in English. `python3 ci/i18n-coverage.py` reports coverage
(informational, not a gate).

## Release
- `manifest.json` `version` is the single source of truth. A release PR bumps it,
  bumps `const.py` `PANEL_VERSION` to match, and adds a `## [X.Y.Z]` `CHANGELOG.md`
  section. PEP 440 pre-release suffixes (`bN`/`aN`/`rcN`) ship as GitHub
  pre-releases → HACS beta channel.
- The built `example-panel.js` / `example-card.js` are gitignored; CI builds them.

## Home Assistant versions
- **PRs test `stable`**; a nightly (`ha-beta.yml`) tests `beta` and gates nothing.
  Beta week is public roughly four weeks ahead of a release, which is the warning
  window for a breaking change. The container version is `HA_TAG` in
  `tests/integration/docker-compose.yml`.
- **Any job that `pip install`s Home Assistant must run on a Python at or above HA's
  own floor, and must verify what pip resolved** with `ci/check-ha-version.py` (add
  `--pre` for `pip install --pre`). Below the floor pip does not fail; it backtracks
  to the last HA that supported that Python, and the job goes green having checked a
  months-old API.
- `[tool.mypy] python_version` tracks **HA's** floor, not the integration's: HA's
  source uses syntax from its own minimum Python, and mypy targeting anything older
  exits on a syntax error inside HA having checked nothing.
- **A diagnostic step must never be able to fail the suite it precedes** — the
  version-report steps in `ha-beta.yml` carry `continue-on-error: true`.
- Anything resting on a Home Assistant framework contract (device registry, entity
  registry, storage migration) needs an assertion in the Docker tier; a test that
  fakes the framework cannot see the framework change underneath it.

## API surface (`api_surface.py`)
- Every integrator-facing surface is declared there: services, events and payload
  spines, entity platforms and attributes, plus the internal websocket commands and
  HTTP routes. Adding a surface anywhere without adding it there is drift.
- The runtime **consumes** the model — `async_unload_entry` iterates `SERVICE_NAMES`
  — so it cannot rot into documentation. `tests/unit/test_api_surface.py` parses the
  component's own source with `ast` and fails when source and model disagree.
- It holds **names and structure only**. Labels and descriptions are resolved from
  `services.yaml` / `strings.json`, so the UI and any reference read from one string.
  The exception is `EventSpec.summary`: a bus event has no HA string source.
- `SURFACE_KINDS` is the ledger of the whole surface space. The rows marked
  `not_applicable` are the point — listing only what you offer cannot tell you what
  you forgot. Keep it light: it imports `const` and nothing else from the
  integration, and nothing at all from Home Assistant.

## Typing (strict-typing — Platinum practice)
- The integration is **fully typed** and ships
  `custom_components/example_integration/py.typed`. `lint.yml` runs `mypy
  custom_components/example_integration` with Home Assistant installed (so HA's types
  resolve); config is `[tool.mypy]` in `pyproject.toml`. Run locally before pushing:
  `pip install mypy homeassistant && mypy custom_components/example_integration`.
- The template implements Platinum-tier practices (strict typing, async core,
  localized exceptions, a single service `DeviceInfo`) but **intentionally does not
  stamp a `quality_scale` tier in `manifest.json`** — the real tier depends on the
  domain you build after forking. Add the manifest key + a `quality_scale.yaml`
  ledger once your scope is settled. `scripts/rename.py` rewrites the mypy target
  path along with the rest of the placeholders.

## Reviews
- After every push and when opening a PR, request a critical review and name the
  topics to scrutinize (correctness edge cases, maintainability, performance,
  security, HA best practices), most-serious-first. Triage: fix valid findings;
  push back, with reasoning, on false positives.

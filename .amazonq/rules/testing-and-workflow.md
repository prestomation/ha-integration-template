# Testing & workflow conventions

## Git & PR workflow
- Never push directly to `main`. Work on a feature branch and open a PR; squash
  merge.
- Update `CHANGELOG.md` for every user-facing change before a release.
- Post screenshots to the PR for any change that adds/changes/fixes UI (capture via
  `tests/e2e/screenshots.capture.ts`, commit under `docs/images/`, embed via a
  `raw.githubusercontent.com/.../<commit-sha>/docs/images/<file>.png` URL in an
  HTML `<img>` tag — not markdown).
- **Document new major features in `README.md` in the same change** — use cases +
  how it's used + screenshot(s) embedded with a relative `docs/images/…` path.

## The four test tiers (run locally before pushing — never use CI as the runner)
Cheapest first. **Tiers 2 and 3 must run in separate environments** (socket rule).

1. **Pure unit** (`tests/unit`, `pip install pytest`): the pure core
   (`models.py`, `events.py`) and translation parity. Loaded in isolation via the
   synthetic `ex` package in `tests/conftest.py` — these never import HA.
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
- After running the Docker HA container, don't commit runtime-mutated state
  (`tests/integration/ha_config/.storage/` is gitignored). The config entry is
  created via the config flow on first run, then persists in the container volume.
- `asyncio_mode` is set per-invocation by the component/integration runners (it
  needs `pytest-asyncio`, which only the HA harness installs) — not in the root
  `pyproject.toml`, so the pure unit tier stays dependency-light.

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

## Reviews
- After every push and when opening a PR, request a critical review and name the
  topics to scrutinize (correctness edge cases, maintainability, performance,
  security, HA best practices), most-serious-first. Triage: fix valid findings;
  push back, with reasoning, on false positives.

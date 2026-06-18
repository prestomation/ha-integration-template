# AGENTS.md — HA Integration Template

This repository is a **template** for building a Home Assistant custom
integration with a backend, a sidebar panel, a Lovelace card, translations,
bus events, and a full four-tier test suite. The example feature is a tiny
**items list** (`example_integration`); replace it with your own domain, but
keep the conventions and gates below — they are what make the result reviewable,
testable, and HACS-shippable.

> **Renaming the template:** find-and-replace `example_integration` →
> `your_domain`, `Example Integration` → `Your Name`, the `example-` web-component
> / static-path prefixes, and the `ex`/`Example` symbol prefixes. Then swap the
> items model (`models.py`, `store.py`, `sensor.py`, the panel/card UI) for yours.

## Workflow

- **Never push directly to `main`.** Always use a feature branch and open a PR.
- Wait for CI (tests, HACS validation, hassfest) and review before merging.
- **Always squash merge PRs.**
- **CHANGELOG.md** — update for every user-facing change before tagging a release.
  Developer-only changes (CI config, AGENTS.md) don't need entries.
- **Always run tests locally before pushing.** Never use CI as the test runner.
  See "Tests" for the four tiers and exactly how to run each.
- **Every PR that touches the panel or card UI MUST include screenshots — no
  exceptions.** This is a hard gate: a UI change is not reviewable (or mergeable)
  until the PR body embeds current screenshots of the changed surface. Capture
  them with the Playwright harness (`tests/e2e/screenshots.capture.ts`; bring HA
  up with `KEEP_UP=1 bash ci/e2e-up.sh`, then run the capture config), commit the
  PNG(s) under `docs/images/`, and embed them in the PR via a
  `raw.githubusercontent.com/<owner>/<repo>/<commit-sha>/docs/images/<file>.png`
  URL pinned to the commit that added them. When a change adds a new UI surface,
  add a capture step for it to the capture script in the same PR.
  - **Embed PR-body screenshots with an HTML `<img src="…" alt="…" width="820">`
    tag, not markdown `![](…)`.** The PR-update API can silently wrap a markdown
    image URL in backticks (a code span), breaking it. HTML `<img>` avoids markdown
    link parsing. Keep the SHA-pinned `src` (branch names have slashes and are
    ambiguous for `raw.githubusercontent.com`). After editing the body, re-read it
    and verify each image URL returns HTTP 200. (In-repo README markdown with
    relative `docs/images/…` paths is fine — this only bites PR/issue bodies.)
- **Always document new major features in `README.md` in the same change.** Add a
  brief section with the **use cases** (what problem it solves) and a little about
  **how it's used**, with **screenshot(s)** (committed under `docs/images/`,
  embedded with a relative `docs/images/…` path). A headline feature isn't done
  until the README shows it.
- **Request a code review after every push and when opening a PR**, and ask
  explicitly for *critical, skeptical* feedback — name the topics to scrutinize
  (correctness edge cases, maintainability, performance, security, HA best
  practices), most-serious-first. Triage findings: fix the valid ones; push back,
  with reasoning, on false positives.

## Conventions live in `.amazonq/rules/` — keep them current

Project conventions and opinionated decisions are recorded as project rules under
[`.amazonq/rules/`](.amazonq/rules/) (Markdown files agentic tools auto-load as
context). They cover architecture/code conventions and testing/workflow.

**Whenever you establish or change a convention** — in a conversation, a review
thread, or a decision captured in a PR — **update `.amazonq/rules/` in the same
change** (and this `AGENTS.md` if it's a workflow/process rule) so the rules and
`AGENTS.md` stay consistent and every agent picks them up automatically. A new
convention isn't real until it's written into the rules.

## Project structure

- **Domain:** `example_integration`. **Display name:** Example Integration.
- **Backend:** `custom_components/example_integration/`. The data model
  (`models.py`) and event builders (`events.py`) are **pure Python (no HA
  imports)** so they unit-test in isolation — keep them that way.
- **Storage:** local single JSON document `.storage/example_integration`, mutated
  only through `ExampleStore` (the chokepoint).
- **Frontend:** TypeScript + Rollup at `custom_components/example_integration/frontend/`.
  Source in `src/*.ts`, builds to `example-panel.js` + `example-card.js`
  (gitignored, built by CI; see `ci/build-panel.sh`).
- **Admin vs usage:** management lives in the **sidebar panel** (a custom HA
  panel); usage/display is exposed via the **native `sensor` entities** and the
  **dashboard card**. Don't blur these — administration stays in the panel.

## Conventions (summary — full text in `.amazonq/rules/architecture-and-code.md`)

- **Pure, HA-free core.** `models.py` and `events.py` import nothing from
  `homeassistant`. Inject HA specifics (the clock via `dt_util`) from callers.
- **One mutation chokepoint.** All writes go through `ExampleStore`; entities and
  the panel read via the `ExampleCoordinator` and never mutate storage directly.
- **Expose every data action as a service.** Any operation that mutates or exports
  data ships as an `example_integration.*` service (handler in `__init__.py`,
  `services.yaml` entry, `strings.json` localization at translation parity). A
  panel **websocket command** is only a UI-latency optimization and delegates to
  the same store method — never a substitute for the service.
- **Fire an event for every state change.** Built by a pure builder in `events.py`,
  fired at the `store.py` chokepoint, with a shared payload spine. A new event
  isn't done until it's in `docs/EVENTS.md`.
- Entity `unique_id`s are anchored to the item `id` (survive renames).
- Escape all user content before `innerHTML` injection in the panel (`escapeHTML`).
- Panel navigation is deep-linked: every destination maps to a URL under
  `/example-integration`, the `route` prop is the single source of truth, and
  Back/Forward move within the panel. Route parse/build are pure functions in
  `utils.ts`. Never mutate view/detail state directly to navigate.

## Tests — the four tiers (run locally before pushing)

Run order is cheapest-first. **The component tier and the Docker integration tier
must run in separate environments/invocations** (see the socket note).

1. **Pure unit** (`tests/unit`) — `pip install pytest` is enough. Tests the pure
   core (`models.py`, `events.py`) and translation parity. No HA.
   `bash ci/test-python-unit.sh`
2. **Component / in-process HA** (`tests/component`) — real Home Assistant via
   `pytest-homeassistant-custom-component` (real `hass`, registries, config
   entries; I/O mocked). Tests `config_flow`, setup/unload, the store, coordinator,
   sensor entities, services, **events on the bus**, and websocket commands. Fast.
   `bash ci/test-python-component.sh`
3. **Docker integration** (`tests/integration`) — a real running HA container over
   REST/WS. Tests end-to-end loading: the integration sets up, services are
   registered, panel + card bundles are served, events are observable via an
   automation. `bash ci/e2e-up.sh` (or start the container, then
   `bash ci/test-python-integration.sh`).
4. **Frontend (vitest)** + **e2e (Playwright)** — `npx vitest run` for `utils`/i18n
   parity; `bash ci/e2e-up.sh` for the browser smoke + screenshot capture.

- **Pick the right tier for "test against real HA".** HA-coupled logic
  (store/coordinator/entities/services/events/config_flow) belongs in the
  **component** tier — it is real HA and ~100× faster than Docker. Reserve the
  **Docker** tier for what the in-process harness can't do: serving the JS bundles,
  registering the panel/card resources, full-stack REST behavior.
- **Socket isolation (important).** `pytest-homeassistant-custom-component` pulls
  in `pytest-socket`, which blocks real network. So the component tier and the
  Docker integration tier **cannot share a pytest invocation**: the component CI
  step installs the harness; the integration CI step deliberately does **not**
  (and passes `-p no:pytest_socket`). Keep them in separate dirs and steps.
- The component tier needs HA + a built frontend package: `pip install
  pytest-homeassistant-custom-component home-assistant-frontend` (the latter
  provides `hass_frontend`, which the `frontend` dependency requires at setup).
- The Docker tier seeds a config entry at
  `tests/integration/ha_config/.storage/core.config_entries` so the integration
  loads **at HA startup** — which is what injects the dashboard card resource into
  served pages (creating the entry at runtime is too late for the card). HA mutates
  that file at runtime; restore the committed fixture (`git checkout`) and don't
  commit the runtime version. Everything else under `.storage/` is gitignored.

## Translations (quality gates)

`strings.json` (backend) and `frontend/src/locales/en.json` are the sources of
truth. Both layers are guarded by tests — `tests/unit/test_translations_parity.py`
and `frontend/test/i18n.test.js` — that enforce, for every locale: **key parity**,
**placeholder parity** (same `{token}` set per key), **no untranslated leaks** (a
value byte-identical to English is a failure, except a tiny reviewed allowlist),
and (frontend) **key usage** + **plural completeness**. Adding a string to a locale
means translating it or justifying it in the allowlist — never leaving it English.
`python3 ci/i18n-coverage.py` prints per-locale coverage (informational).

## Release

`manifest.json` `version` is the single source of truth. A release PR bumps it,
bumps `const.py` `PANEL_VERSION` to match, and adds a `## [X.Y.Z]` `CHANGELOG.md`
section. PEP 440 pre-release suffixes (`bN`/`aN`/`rcN`) ship as GitHub
pre-releases → HACS beta channel. The built bundles are gitignored; CI builds them.
See `RELEASE.md`.

## Linting

- Python is linted and formatted with **ruff** (config in `pyproject.toml`,
  enforced by `lint.yml`). Run `ruff check custom_components tests ci scripts` and
  `ruff format --check …` before pushing; `ruff format` / `ruff check --fix` apply
  fixes.

## Renaming

- `python scripts/rename.py your_domain "Your Name"` rewrites every placeholder
  (domain, display name, web-component / CSS / symbol prefixes), renames the
  component directory + seeded fixtures, and tidies with ruff. Use it instead of a
  manual find-and-replace.

## CI

- `lint.yml` — ruff lint + format check.
- `test.yml` — vitest, pure pytest unit, **component (in-process HA)**, i18n
  coverage, HACS validation, hassfest.
- `integration.yml` — Docker-based integration tests (no HA harness installed).
- `e2e.yml` — Docker + Playwright; uploads the Playwright report on failure.
- `hacs.yml` — HACS validation.
- `release.yml` — PR-merge-driven release (version ↔ PANEL_VERSION ↔ CHANGELOG
  checks; builds the zip).

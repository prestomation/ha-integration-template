# HA Integration Template

[![Integration Usage][usage-shield]][usage]
[![GitHub Downloads][downloads-shield]][releases]
[![GitHub Release][release-shield]][releases]
[![GitHub Release Date][release-date-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacs-shield]][hacs]
![Project Maintenance][maintenance-shield]
[![HACS Validation][hacs-validation-shield]][hacs-validation]
[![HA Version][ha-version-shield]][ha-version]

A **template for a Home Assistant custom integration**: a backend, a sidebar panel, a
dashboard card, translations, bus events, services and a full test suite, wired to CI
and HACS. Clone it, rename it, and replace the example feature with your own.

The example feature is a small **items list** (`example_integration`). Each item has a
name and an integer value. The feature is small on purpose. The subject of the template
is the structure and the conventions around it.

## Contents

| Area | Contents |
|---|---|
| **Backend** | A pure core with no Home Assistant import (`models.py`, `events.py`), 1 write path (`ExampleStore`), a `DataUpdateCoordinator`, a `sensor` platform, a `config_flow` and `diagnostics`. |
| **Services** | `add_item`, `update_item` and `delete_item`, with `services.yaml` and localized text. |
| **Events** | `example_integration_item_{created,updated,deleted}`, fired by the store and described in [`docs/EVENTS.md`](docs/EVENTS.md). |
| **Frontend** | A deep-linked sidebar **panel** for administration and a dashboard **card** for display, in TypeScript and Rollup, with a small i18n module and no runtime dependency. |
| **Translations** | Backend `strings.json` and `translations/`, and frontend `src/locales/` (`en`, `de`), with parity tests. |
| **Tests** | Pure unit, in-process Home Assistant component, Docker integration, Playwright browser, and mutation testing. |
| **Docs** | A Docusaurus site in `website/` built from `docs/guide/` and `docs/*.md`, with a generated API reference, and design docs in `docs/design/` that CI keeps in step with the code. |
| **CI and release** | Lint, test, mutation, integration, e2e, HACS, a version-checked release that tells each fixed issue, PR preview builds, and a nightly run against the Home Assistant beta. |
| **Guardrails** | Automated gates for types, prose, tests, mutation score, translations, fixtures, API-surface drift, docs drift and release consistency. See [Guardrails](#guardrails). |
| **Agent rules** | `AGENTS.md`, `CLAUDE.md`, `.amazonq/rules/`, Claude Code skills and hooks: the conventions and hard gates that coding agents load. |
| **Rename script** | `scripts/rename.py your_domain "Your Name"` rewrites every placeholder and renames the component directory in 1 step. |

## The example feature

**Sidebar panel**: create, edit and delete items. Each page has its own URL, so Back
and Forward work.

![Panel with a list of items](docs/images/panel-list.png)

![Panel with the detail of an item](docs/images/panel-detail.png)

**Dashboard card**: shows the items. The integration adds it to the card picker.

![Dashboard card](docs/images/card.png)

The [user guide](docs/guide/start/panel.md) has the detail.

## Use the template

1. **Rename.** 1 command rewrites every placeholder (domain, display name, web
   component, CSS and symbol prefixes) and renames the component directory:

   ```bash
   python scripts/rename.py your_domain "Your Name"
   # optional explicit short prefix (default: derived from the domain):
   # python scripts/rename.py your_domain "Your Name" --prefix yd
   # optional repository slug for the badges, the docs site and the manifest URLs:
   # python scripts/rename.py your_domain "Your Name" --repo you/your-repo
   ```

   Read `git diff` after the rename. The script runs `ruff format` and reports each line
   that is then too long.
2. **Replace the model.** Change the items model (`models.py`, `store.py`, `sensor.py`,
   the panel and card UI, `strings.json` and the locales) to your own domain, and keep
   each convention. Rewrite the design docs in `docs/design/` to match, then run
   `python3 ci/docs.py stamp --all`.
3. **Run the tests** (see below) and keep them green.

## Run the tests

The tiers, cheapest first (see [`.amazonq/rules/testing.md`](.amazonq/rules/testing.md)):

```bash
# All CI dependencies into .venv (idempotent). Then: source .venv/bin/activate
bash ci/setup-ci-deps.sh

# 1. Pure unit (no HA harness)
bash ci/test-python-unit.sh

# 2. Component: a real in-process Home Assistant
bash ci/test-python-component.sh

# 3. Frontend (vitest)
npm ci && bash ci/build-panel.sh && bash ci/test-frontend.sh

# 4. Docker integration and Playwright e2e (starts HA, runs, stops it)
bash ci/e2e-up.sh

# Lint, format, types and docs (also in CI)
ruff check custom_components tests ci scripts && ruff format --check custom_components tests ci scripts
mypy custom_components/example_integration
python3 ci/docs.py check
```

> **Warning:** run the component tier and the Docker integration tier in separate pytest
> runs. `pytest-homeassistant-custom-component` pulls in `pytest-socket`, which blocks
> the real network that the Docker tier needs.

## Quality scale

The template uses the practices of the Home Assistant
[**Platinum** integration quality scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/):

- **Strict typing**, with `py.typed`. CI runs `mypy` with Home Assistant installed
  (`lint.yml`, config in `pyproject.toml`).
- **An async core with 1 coordinator** and 1 write path (`ExampleStore`).
- **Localized exceptions.** Services raise `ServiceValidationError` with a
  `translation_key` from `strings.json` `exceptions` (en and de). A unit test
  (`tests/unit/test_exception_translations.py`) keeps each raise localized.
- **1 service device** groups the entities of the integration (`DeviceInfo` with
  `entry_type=SERVICE`).

The manifest has **no `quality_scale` tier**. The tier depends on the domain that you
build: a device to talk to, discovery and auth all change it. Add
the manifest key and a `quality_scale.yaml` ledger when the scope is settled.

## Guardrails

Most of the value of the template is in the checks that come with it. Each one catches a
failure that leaves no trace on its own. One such failure is a job that is green after
it tested an old Home Assistant. Another is a changelog entry for work that is in no
release.

The workflow and the conventions behind them are in [`AGENTS.md`](AGENTS.md) and
[`.amazonq/rules/`](.amazonq/rules/).

**On every pull request:**

| Guardrail | Where | What it catches |
|---|---|---|
| **ruff** lint + format | `lint.yml` | Style and formatting drift across `custom_components`, `tests`, `ci`, `scripts`. |
| **mypy**, strict, with Home Assistant installed | `lint.yml` | Type errors against the real HA API, from the 1 list in `requirements-typing.txt`. |
| **Stale Home Assistant resolve** | `ci/check-ha-version.py` | pip quietly backtracking to a months-old HA when the runner's Python sits below HA's floor. The job stays green while checking an API nobody runs. |
| **Prose linting** | `lint.yml` (vale) | AI-writing tells and breaks of the house STE rules (`styles/STE/`) in the README, CHANGELOG, `docs/`, and the strings Home Assistant renders. Scoped to the lines a PR touches. |
| **Docs audit** | `lint.yml` (`docs-audit`, `ci/docs.py check`) | A design doc that no longer matches its code (source hash drift), a source file that no design doc covers, a doc over its length cap, history in a doc, a broken link, and a reference to a file or function that does not exist. |
| **CHANGELOG release gap** | `ci/check-changelog-release-gap.py` | An entry folded into a section whose version is already tagged, `manifest.json` and `PANEL_VERSION` that differ, and a top section that no version bump will release. |
| **The test tiers** | `test.yml`, `integration.yml`, `e2e.yml` | Pure unit, in-process HA component, Docker integration over REST/WS, and Playwright in a real browser at desktop and phone width. |
| **Mutation testing at 80%** | `mutation.yml` | A test that runs a line without asserting anything that would catch it being wrong. Scoped to the code the branch changed. It also fails a run in which Stryker ran no test. |
| **Coverage comment** | `pytest_coverage.yml` | Untested new code, shown in review rather than in a report nobody opens. |
| **Translation parity** | `tests/unit/test_translations_parity.py`, `frontend/test/i18n-parity.test.js` | Missing keys, mismatched `{placeholders}`, and English left in a non-English locale. |
| **Localized exceptions** | `tests/unit/test_exception_translations.py` | A `raise` a user could see that has no `translation_key` behind it. |
| **API-surface drift** | `tests/unit/test_api_surface.py` | A service, event, payload field, websocket command, or entity platform added to one registry and forgotten in the others. Parses the component's own source and compares it to `api_surface.py`. |
| **Generated API reference** | `tests/unit/test_generate_api_docs.py` | A surface in `api_surface.py` that the generated reference page leaves out. |
| **Seeded fixture cleanliness** | `tests/unit/test_integration_fixture_clean.py` | A local Docker run committed back into the seeded config entry, which then fails on a pristine checkout while passing locally. |
| **Docs site build** | `docs-preview.yml` | A guide page with no sidebar entry, a broken link or anchor, and a missing image. Posts a preview link and the changed pages. |
| **Walkthrough capture** | `walkthrough-preview.yml` | A tour that no longer runs. The capture job holds no write token, and a failed capture fails the check. |
| **HACS validation + hassfest** | `test.yml`, `hacs.yml` | Manifest, brand, and repository-structure problems that block installation. |
| **Release consistency** | `release.yml` | `manifest.json` version, `const.py` `PANEL_VERSION`, and the `## [X.Y.Z]` CHANGELOG section disagreeing with each other. |
| **Release publish gate** | `release.yml`, `tests/unit/test_ci_release_publish_gate.py` | A tag, a release or a docs deploy from a branch other than `main`, or from a dry run. |
| **Dependabot auto-merge** | `dependabot-auto-merge.yml`, `ci/wait_for_checks.py` | A bump merging on a partial check list. It waits for every check on the head commit, not the hand-maintained required-checks list. |

**After a release:**

| Guardrail | Where | What it catches |
|---|---|---|
| **Issue notices** | `release.yml` (`notify-issues`), `ci/release-issues.py` | A fixed issue that nobody tells. A beta comments on each `(Fixes #N)` issue, a stable comments and closes it, and a CI warning names an issue that a commit fixed and the CHANGELOG forgot. |

**Nightly, gating nothing:**

| Guardrail | Where | What it catches |
|---|---|---|
| **Home Assistant beta run** | `ha-beta.yml` | A breaking change in the next HA release, roughly four weeks before users get it. Runs the Docker and browser tiers against `beta` and type-checks against a pre-release HA, then files one reusable issue, also when a job times out. |

**Enforced in review, not by a job:**

- **Screenshots.** A PR that touches the panel or card UI needs current desktop and
  phone screenshots of each changed surface in its body. Capture them with the
  Playwright harness and commit them under `docs/images/`.
- **The video walkthrough.** A PR that adds a user-facing UI surface extends the tour in
  `tests/e2e/walkthrough.capture.ts`. CI captures it and posts a sticky comment with the
  gif. Nothing is committed.
- **One-way doors and Security.** A PR body lists each external contract that it commits
  to, and says for each changed surface if it is admin-only or open
  (`.github/pull_request_template.md`).
- **Every data action is a service, and every state change fires a documented event.**

## License

MIT. See [LICENSE](LICENSE).

<!--
Badge reference links. `scripts/rename.py --repo owner/name` rewrites the
`prestomation/ha-integration-template` slug and the maintainer handle here; the
domain in the "integration usage" badge (analytics query `$.example_integration.total`)
is rewritten by the normal domain replacement. The "integration usage" badge only
shows real numbers once the integration is published to HACS and appears in the
Home Assistant analytics data.
-->

[usage-shield]: https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.example_integration.total&style=for-the-badge
[usage]: https://analytics.home-assistant.io/
[downloads-shield]: https://img.shields.io/github/downloads/prestomation/ha-integration-template/total.svg?style=for-the-badge
[releases]: https://github.com/prestomation/ha-integration-template/releases
[release-shield]: https://img.shields.io/github/release/prestomation/ha-integration-template.svg?style=for-the-badge
[release-date-shield]: https://img.shields.io/github/release-date/prestomation/ha-integration-template?style=for-the-badge
[commits-shield]: https://img.shields.io/github/last-commit/prestomation/ha-integration-template?style=for-the-badge
[commits]: https://github.com/prestomation/ha-integration-template/commits/main
[license-shield]: https://img.shields.io/github/license/prestomation/ha-integration-template.svg?style=for-the-badge
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40prestomation-blue.svg?style=for-the-badge
[hacs-validation-shield]: https://github.com/prestomation/ha-integration-template/actions/workflows/hacs.yml/badge.svg
[hacs-validation]: https://github.com/prestomation/ha-integration-template/actions/workflows/hacs.yml
[ha-version-shield]: https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg?style=for-the-badge
[ha-version]: https://www.home-assistant.io/

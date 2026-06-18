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

A batteries-included **template for building a Home Assistant custom integration** —
backend, a sidebar panel, a Lovelace card, translations, bus events, services, and a
full four-tier test suite, all wired to CI and HACS. Clone it, rename it, and replace
the example feature with your own.

The example feature is a tiny **items list** (`example_integration`): a set of named
items, each with a numeric value. It's deliberately trivial — the point is the
*scaffolding and conventions* around it.

## What's included

| Area | What you get |
|---|---|
| **Backend** | Pure HA-free core (`models.py`, `events.py`), a single-chokepoint `ExampleStore`, a `DataUpdateCoordinator`, a `sensor` platform, a `config_flow`, and `diagnostics`. |
| **Services** | `add_item` / `update_item` / `delete_item` — the automation-facing contract, with `services.yaml` + localization. |
| **Events** | `example_integration_item_{created,updated,deleted}` fired at the store chokepoint, documented in [`docs/EVENTS.md`](docs/EVENTS.md). |
| **Frontend** | A deep-linked sidebar **panel** (admin) and a dashboard **Lovelace card** (display), TypeScript + Rollup, with a tiny dependency-free i18n. |
| **Translations** | Backend `strings.json` + `translations/` and frontend `src/locales/` (`en`, `de`), guarded by parity tests. |
| **Tests** | Four tiers: pure unit, **in-process HA** component, Docker integration, and Playwright e2e + screenshot capture. |
| **CI / release** | `lint` (ruff), `test`, `integration`, `e2e`, `hacs`, and a version-checked `release` workflow; plus dependabot and issue/PR templates. |
| **Agentic rules** | `AGENTS.md`, `CLAUDE.md`, `.amazonq/rules/`, and a SessionStart hook — conventions and hard gates that coding agents auto-load. |
| **Rename script** | `scripts/rename.py your_domain "Your Name"` rewrites every placeholder + renames the component dir in one step. |

## The example feature

**Sidebar panel** — administration (create / edit / delete items), deep-linked so
Back/Forward work and any view is shareable by URL:

![Panel — items list](docs/images/panel-list.png)

![Panel — item detail](docs/images/panel-detail.png)

**Dashboard card** — read-only display, auto-registered in the "Add card" picker:

![Dashboard card](docs/images/card.png)

## Using the template

1. **Rename** — one command rewrites every placeholder (domain, display name,
   web-component / CSS / symbol prefixes) and renames the component directory:

   ```bash
   python scripts/rename.py your_domain "Your Name"
   # optional explicit short prefix (default: derived from the domain):
   # python scripts/rename.py your_domain "Your Name" --prefix yd
   ```

   Review `git diff` afterwards. (The script auto-runs `ruff format` so the result
   is lint-clean.)
2. **Replace the model.** Swap the items model (`models.py`, `store.py`, `sensor.py`,
   the panel/card UI, `strings.json`/locales) for your domain. Keep the conventions.
3. **Run the tests** (see below) and keep them green as you build.

## Running the tests

The four tiers, cheapest first (see [`AGENTS.md`](AGENTS.md) for details):

```bash
# 1. Pure unit (no HA harness; `pip install pytest`)
bash ci/test-python-unit.sh

# 2. Component — real in-process HA
pip install -r requirements-test.txt home-assistant-frontend
bash ci/test-python-component.sh

# 3. Frontend (vitest)
npm ci && bash ci/build-panel.sh && bash ci/test-frontend.sh

# 4. Docker integration + Playwright e2e (brings HA up, runs, tears down)
bash ci/e2e-up.sh

# Lint / format (also enforced in CI)
ruff check custom_components tests ci scripts && ruff format --check custom_components tests ci scripts
```

> **Important:** the component tier and the Docker integration tier **cannot share a
> pytest invocation** — `pytest-homeassistant-custom-component` pulls in
> `pytest-socket`, which blocks the real network the Docker tier needs. They run as
> separate steps.

## Conventions & hard gates

The workflow, conventions, and gates live in [`AGENTS.md`](AGENTS.md) and
[`.amazonq/rules/`](.amazonq/rules/). Two that are easy to miss:

1. **Any PR touching the panel or card UI must include current screenshots** captured
   with the Playwright harness.
2. **Every data action is a service; every state change fires a documented event.**

## License

MIT — see [LICENSE](LICENSE).

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

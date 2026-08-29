# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). `manifest.json` `version`
is the single source of truth (see `RELEASE.md`).

## [Unreleased]

### Added
- **A full set of guardrails, ported from a production integration built on this
  template.** New PR checks cover prose linting, a stale-Home-Assistant resolve, an
  already-released CHANGELOG section, coverage reporting, seeded-fixture hygiene, and
  API-surface drift; a nightly run against the Home Assistant beta gives about four
  weeks of warning before a breaking release. The README's Guardrails section lists
  each one and what it catches.
- **`api_surface.py`, the single index of every integrator-facing surface.** Services,
  events and payload spines, entity platforms and attributes, websocket commands and
  HTTP routes are declared once, the runtime consumes the model, and a drift test
  parses the component source to fail when the two disagree.
- **Platinum-tier practices baked into the template.** Strict typing (`py.typed` +
  `mypy` in `lint.yml`), localized service exceptions (`strings.json` → `exceptions`,
  en + de) with an AST drift-guard test, a single service `DeviceInfo` grouping the
  integration's entities, and `integration_type: service`. The template demonstrates
  these patterns without stamping a `quality_scale` tier in the manifest (that's
  left to the integration you build on top of it).

## [0.1.0]

### Added
- Initial template: the **Example Integration** (`example_integration`) — a managed
  **items list** demonstrating the full stack:
  - Pure, HA-free core (`models.py`, `events.py`) unit-tested in isolation.
  - `ExampleStore` single mutation chokepoint persisting to
    `.storage/example_integration` and firing `item_created/updated/deleted` events.
  - `ExampleCoordinator` + a `sensor` platform (a total sensor and per-item sensors).
  - Automation-facing services `add_item` / `update_item` / `delete_item`, with panel
    websocket commands delegating to the same store methods.
  - A sidebar **panel** (deep-linked admin UI) and a dashboard **Lovelace card**
    (read-only display), built with TypeScript + Rollup.
  - Backend + frontend translations (`en`, `de`) guarded by parity tests.
- Four-tier test suite: pure unit, in-process HA component
  (`pytest-homeassistant-custom-component`), Docker integration, and Playwright e2e
  with screenshot capture.
- CI workflows (`test`, `integration`, `e2e`, `hacs`, `release`) and the agentic
  rules/workflow docs (`AGENTS.md`, `CLAUDE.md`, `.amazonq/rules/`).

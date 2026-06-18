# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). `manifest.json` `version`
is the single source of truth (see `RELEASE.md`).

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

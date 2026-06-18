# Design notes

This template demonstrates a complete Home Assistant custom integration in
miniature. The feature — an **items list** (named items, each with a numeric
`value`) — is intentionally trivial so the *structure* is the lesson.

## Layers

```
                  ┌───────────────────────────────────────────────┐
  Pure core       │ models.py   events.py        (no HA imports)   │
  (unit-tested)   └───────────────────────────────────────────────┘
                            ▲                ▲
                            │ build/validate │ build payloads
                  ┌─────────┴────────────────┴────────────────────┐
  HA boundary     │ store.py  ── the single mutation chokepoint    │
                  │   • validates via models                       │
                  │   • persists to .storage/example_integration   │
                  │   • fires bus events (events.py)               │
                  └───────────────┬───────────────────────────────┘
                                  │ read via
                  ┌───────────────┴───────────────────────────────┐
  Surfaces        │ coordinator → sensor entities (usage/display)  │
                  │ services (__init__.py) — automation contract   │
                  │ websocket_api — panel/card UI optimization     │
                  │ panel.py + card.py — register the frontend     │
                  └───────────────────────────────────────────────┘
```

## Key decisions

- **Pure, HA-free core.** `models.py`/`events.py` are pure so the highest-value
  logic unit-tests without the HA harness (tier 1).
- **One mutation chokepoint.** Every write goes through `ExampleStore`; events fire
  there, so all surfaces are observed uniformly.
- **Services are the contract; the websocket is an optimization.** The panel/card
  use websocket commands for latency, but they delegate to the same store methods
  the services call. Automations get a real `example_integration.*` service.
- **Immediate refresh.** Mutations call `coordinator.async_refresh()` (not the
  debounced `async_request_refresh()`) so the local store stays instantly
  consistent and tests are deterministic.
- **Admin vs. usage split.** Management lives in the sidebar panel; display lives in
  native sensor entities and the dashboard card.
- **Deep-linked panel.** The URL is the single source of truth (`parseRoute`/
  `buildPath` are pure); Back/Forward move within the panel.

## Why four test tiers
See `.amazonq/rules/testing-and-workflow.md`. In short: pure unit (ms), in-process
HA component (≈100ms, real `hass`), Docker integration (real running HA over REST/WS),
and Playwright e2e (browser). The component tier is the workhorse for HA-coupled
logic; Docker is reserved for what the in-process harness can't do (serving bundles,
registering panel/card resources, full-stack REST).

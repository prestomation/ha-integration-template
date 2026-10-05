---
title: Testing rules
summary: Which test tier covers what, how to run each one, how to write a test that can fail, and the translation gates.
---

# Testing rules

Run the tests locally before you push. CI is not the test runner.

## Tiers and how to run them

Run the cheapest tier first.

| Tier | Where | Run |
|---|---|---|
| Unit (pure core) | `tests/unit` | `bash ci/test-python-unit.sh` |
| Component (in-process HA) | `tests/component` | `bash ci/test-python-component.sh` |
| Frontend | `tests/frontend`, `frontend/test` | `bash ci/test-frontend.sh` |
| Integration | `tests/integration` (Docker HA) | `bash ci/test-python-integration.sh` |
| Browser | `tests/e2e` (Playwright) | `bash ci/e2e-up.sh` |
| Mutation | the changed code | see [ci-and-ha-versions.md](ci-and-ha-versions.md#mutation-testing) |

- The unit tier needs only `pip install pytest PyYAML`. It tests the pure core, the CI
  scripts, the docs tool and translation parity.
- The component tier runs a real Home Assistant through
  `pytest-homeassistant-custom-component`, with real registries and config entries and
  mocked I/O. It covers `config_flow`, setup and unload, the store, the coordinator,
  the entities, the services, the events on the bus and the websocket commands. It also
  needs `home-assistant-frontend`, because the `frontend` dependency imports
  `hass_frontend` at setup. Its runner sets `asyncio_mode=auto`, because only the harness
  installs `pytest-asyncio`.
- `ci/setup-ci-deps.sh` installs everything into `.venv`. Run `source .venv/bin/activate`
  first.

### Pick the tier for "test against real HA"

- Home Assistant logic (store, coordinator, entities, services, events, config flow)
  goes in the **component** tier. It is real Home Assistant and about 100 times faster
  than Docker, and it can assert on internal state that REST cannot see.
- Keep the **Docker** tier for what the harness cannot do: serve the JS bundles, register
  the panel and card resources, and full-stack REST behavior.

### Tiers that must not share a pytest run

- **Component and Docker.** `pytest-homeassistant-custom-component` pulls in
  `pytest-socket`, which blocks the real network that the Docker tier needs. The
  component step installs the harness. The integration step does not, and its runner
  turns the socket plugins off.
- **Unit and component.** `tests/unit/conftest.py` installs stub parent packages for
  `custom_components.example_integration`. In one pytest process, Home Assistant finds
  the stub and every component test fails with "No setup or config entry setup function
  defined". A job that wants both tiers (coverage) runs 2 invocations with
  `--cov-append`.
- `tests/unit/conftest.py` runs each pure module under its real dotted name
  (`custom_components.example_integration.<mod>`) and registers `ex.<mod>` as an alias.
  Keep the real name: mutmut matches a mutant key to `__module__`. Keep the file in
  `tests/unit/`: as a root conftest its stubs would hide the real integration from the
  component tier.

## Dependencies

- **A missing test dependency fails the run. It never skips.** Import every package in
  `requirements-test.txt` plainly, so a broken environment does not look like a choice.
- **A unit test that reads a repo file needs that file in `also_copy`** under
  `[tool.mutmut]`. mutmut runs the suite in a `mutants/` copy that holds only the source
  and the tests. The fault shows only on a PR that also changes mutable Python. List the
  directory: mutmut copies a bare file without its parent directory.

## Writing a test that can fail

- **Test the shipped function, never a copy.**
- **Check that a new test can fail.** Mutate the line and watch it go red. A fake that can
  only produce the passing case reports coverage that the code does not have.
- **Pin a whole error message** with `raises_exactly` from `tests/unit/asserts.py`. A test
  that asserts only "something was raised" lets the wrong message ship.
- A known-broken contract gets `xfail(strict=True)`, never a weaker assertion.
- **A framework contract needs a Docker-tier assertion.** Device registry, entity
  registry, device automation and storage migration behavior is invisible to a test that
  fakes the framework. HA 2026.8 split devices per config entry and broke device
  attachment across custom integrations with no advance signal.
- **Cross-version behavior needs an upgrade test.** Boot a frozen older Home Assistant on
  a seeded config dir, then boot the current one on the same dir, so Home Assistant runs
  its own migration between. The fixtures depend on what the integration stores, so the
  template has no upgrade tier. Add one, and a job in `ha-beta.yml`, when the integration
  stores data that Home Assistant migrates.
- **Assert disappearance too.** Test a transition from both ends: present before, gone
  after.
- Never commit a real `.storage` dump. Build fixtures from synthetic data, and use each
  fixture in a test.

## The seeded fixture

- The Docker and browser tiers seed a config entry in
  `tests/integration/ha_config/.storage/core.config_entries`, so the integration loads at
  Home Assistant startup. That is what puts the card resource into the served pages. An
  entry made at run time is too late for the card.
- Home Assistant writes to that file at run time. After a local run, restore it with
  `git checkout`. Git ignores the rest of `.storage/`.
  `tests/unit/test_integration_fixture_clean.py` fails when a key that a run wrote
  reaches git, because a dirty fixture passes locally and fails on a clean checkout.

## Browser tests

- Auth and onboarding are in `tests/e2e/global-setup.ts`. Specs share its saved state.
- **A spec owns what it creates.** Delete created items after the test, and give
  fixtures stable names, never a `Date.now()` suffix.
- The card can load after the dashboard renders, so `openCard` in
  `tests/e2e/tests/helpers.ts` retries with a reload. Keep the retry
  ([frontend.md](frontend.md#bundles-and-the-card)).
- `tests/e2e/viewports.ts` is the only place that writes a width (`DESKTOP`, `PHONE`).
- Measure layout by relations (A is above B), never by coordinates. Assert that a list is
  not empty before you loop over it.
- A capture is documentation. Each surface that a capture shows needs an assertion in
  `tests/e2e/tests/` ([pr-workflow.md](pr-workflow.md#screenshots-desktop-and-phone)).

## Translations

`strings.json` and `frontend/src/locales/en.json` are the sources.
`tests/unit/test_translations_parity.py` and `frontend/test/i18n-parity.test.js` enforce for
each locale:

- the same keys as English, and the same `{token}` placeholders per key;
- no value identical to English, except the global `INTENTIONALLY_IDENTICAL` list and a
  per-locale `COGNATE_IDENTICAL` list of reviewed cognates;
- for the frontend, that every `t()` and `tn()` key exists, that each `tn()` base has an
  `.other` form, and that no key is unused.

Add a string to a locale only as a translation or as a reviewed cognate.
`python3 ci/i18n-coverage.py` prints coverage for information only. Add a locale by
adding `<lang>.json` next to the English source and listing it in `locales/index.ts`.

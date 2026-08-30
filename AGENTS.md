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
  - **Never add an entry to a section whose version is already released.**
    `release.yml` cuts a release by reading `manifest.json`'s version and tagging it,
    and skips silently when that tag already exists. An entry folded into the current
    top `## [X.Y.Z]` section without a version bump therefore merges clean and then
    goes nowhere: nothing told `release.yml` there was anything new to publish. Bump
    `manifest.json` + `const.py` (`PANEL_VERSION`) and open a new section instead.
    `lint.yml`'s `changelog-release-gap` job (`ci/check-changelog-release-gap.py`)
    fails the PR when it happens; folding into a section that is *not* yet tagged is
    the normal workflow and stays allowed.
- **User-facing prose is linted for AI-tell phrasing.** `lint.yml`'s `vale` job runs
  the [vale-ai-tells](https://github.com/tbhb/vale-ai-tells) Vale style (pinned in
  `.vale.ini`) over `README.md`, `CHANGELOG.md`, the `docs/*.md` pages, `strings.json`,
  `services.yaml`, and the English frontend locale, catching things like "delve",
  "it's important to note", em-dash overuse, and other AI-writing tells. **It's
  diff-scoped** (`filter_mode: added`): only the lines a PR touches are checked, so
  it's a real gate on new prose without failing on the existing backlog. Run it
  locally with `vale sync && vale <paths>` (Vale CLI from
  [github.com/errata-ai/vale releases](https://github.com/errata-ai/vale/releases)).
  For an accepted false positive, either disable the rule for that file in `.vale.ini`
  (`ai-tells.RuleName = NO`) or wrap the exception inline with
  `<!-- vale ai-tells.RuleName = NO -->` / `<!-- vale ai-tells.RuleName = YES -->`.
  **A clean local run is not proof CI is clean:** the action pins its own binary and
  can report hits a locally-installed Vale misses. When a run matters, check the
  rule's own regexes against the text (`styles/ai-tells/<Rule>.yml` is plain YAML
  `tokens`), and match Vale's scope while you do — rules apply per **block**, so a
  list item plus its continuation lines is one string and a pattern like `[^,]+`
  happily spans sentence boundaries. In practice keep at most one comma in a bullet
  after a modal (`can`, `could`, `will`) or a pronoun (`you`, `we`, `they`). A
  wholesale rewrite of a file's prose can also surface pre-existing hits on lines that
  merely moved, so run `vale <file>` over the whole file before that kind of PR.
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
  - **Always visually inspect every captured screenshot before committing it.** Read
    the PNG with the Read tool and look at the rendered image. Confirm the changed
    surface is visible and correct: dialogs show their heading and buttons, lists are
    populated, nothing is blank or clipped. If a screenshot looks wrong, diagnose the
    root cause and fix it rather than committing it.
  - **A screenshot is documentation, not verification — capturing a surface is not
    covering it.** A capture renders whatever the UI does, including a bug, and
    nothing fails because no test asserted on it. When a capture adds a surface, make
    sure something in `tests/e2e/tests/` asserts on that surface in the same PR.
- **Every PR that adds a _new user-facing UI feature_ SHOULD keep the video
  walkthrough current — but you don't capture or commit it; CI does.** Screenshots
  prove a surface *renders*; a short video proves the *interaction* works (the flow,
  the transitions, the motion). On every PR, `walkthrough-preview.yml` stands up the
  seeded HA container, runs the capture harness (`tests/e2e/videos.capture.ts`),
  transcodes to gif+mp4, publishes them to an orphan **`gh-pages`** branch (under
  `pr-preview-media/pr-<n>/`, via `rossjrw/pr-preview-action`), and posts/updates a
  **sticky PR comment** that **embeds the gif inline** (via a `raw.githubusercontent.com`
  URL — the same trick the screenshot gate uses, so no GitHub Pages setup is needed).
  Nothing lands in `docs/videos/` or `main` — `docs/videos/` is gitignored and the
  media lives only on `gh-pages` — so there's zero `main` bloat, and the comment
  always reflects the PR's HEAD (a `?v=<sha>` cache-buster keeps it fresh).
  - **The gate for a feature PR is: extend the tour.** Since the walkthrough is
    generated, "keeping it current" means **editing the tour** (`videos.capture.ts`),
    not committing a file: when a feature adds a brand-new UI surface, add a step
    through it (deliberate `BEAT` pauses so the motion reads well) **in the same PR**.
    Pure bug-fix / styling / copy PRs don't need to touch the tour.
  - **Capture is a _soft_ gate** (`continue-on-error`): a flaky Playwright run posts a
    "capture failed" note (with a logs link) instead of blocking the PR; pushing again
    re-runs it. Don't hand-commit a video to work around it.
  - **Run it locally to debug the tour** (with ffmpeg on PATH). From the repo root:
    ```bash
    KEEP_UP=1 bash ci/e2e-up.sh        # build panel + start HA
    # In the Claude Code remote env, point Playwright at the pre-installed Chromium:
    CHROMIUM_EXEC=$(ls /opt/pw-browsers/chromium-*/chrome-linux/chrome 2>/dev/null | head -1) \
      bash ci/capture-video.sh         # writes gif/mp4 to docs/videos/ (gitignored)
    ```
    Open `docs/videos/walkthrough.gif` with the Read tool and confirm the tour shows
    the intended surfaces (populated list, add flow, detail, card) before relying on
    CI. **Why gh-pages + an inline gif and not a committed file:** GitHub's issue/PR-body
    sanitizer *strips* a committed-file `<video>` tag, and committing gifs bloats git
    history with multi-MB binaries. Publishing to an orphan `gh-pages` branch and
    embedding the gif via `raw.githubusercontent.com` keeps the motion *inline* and
    reviewable while leaving `main` clean — and, unlike serving via GitHub Pages, needs
    no repo setting enabled. (The mp4 is linked, not inline: only a drag-and-drop
    `user-attachments` upload inline-*plays* an mp4, which CI can't produce.)
- **Always document new major features in `README.md` in the same change.** Add a
  brief section with the **use cases** (what problem it solves) and a little about
  **how it's used**, with **screenshot(s)** (committed under `docs/images/`,
  embedded with a relative `docs/images/…` path). A headline feature isn't done
  until the README shows it. (The moving walkthrough is **not** in the README — it's
  the per-PR CI comment described above; the README stays on committed screenshots.)
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
- **Every integrator-facing surface is declared in `api_surface.py`.** Services,
  events and their payloads, entity platforms and attributes, plus the internal
  websocket commands and HTTP routes. It exists because those registries have no
  reason to know about each other, so a surface can be added in one and forgotten in
  the rest — registered but missing from the teardown list, renamed on one side of a
  pair. The runtime *consumes* it (`async_unload_entry` iterates `SERVICE_NAMES`), and
  `tests/unit/test_api_surface.py` parses the component's own source and fails on
  drift. The model holds names and structure only: every label and description is
  resolved from `services.yaml` / `strings.json`, so the Home Assistant UI and any
  generated reference read from one string. `SURFACE_KINDS` is the ledger of the whole
  surface space, and the rows that say `not_applicable` are the point — listing only
  what you offer cannot tell you what you forgot.
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

Plus a fifth, **mutation testing** — see below. It is a PR gate, not part of the
run-before-you-push loop (it is too slow); run it when you change the mutable
surface.

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
- **The unit tier and the component tier cannot share one either**, for a second
  reason that bites even in a single environment: `tests/unit/conftest.py` installs
  stub `custom_components.example_integration` parent packages so the pure core loads
  without Home Assistant. Collect both tiers in one pytest process and that stub is
  in `sys.modules` when HA imports the integration for real, so every component test
  dies with *"No setup or config entry setup function defined"* — HA found the stub.
  Anything wanting both (the coverage job, say) runs two invocations and combines
  with `--cov-append`.
- The component tier needs HA + a built frontend package: `pip install
  pytest-homeassistant-custom-component home-assistant-frontend` (the latter
  provides `hass_frontend`, which the `frontend` dependency requires at setup).
- The Docker tier seeds a config entry at
  `tests/integration/ha_config/.storage/core.config_entries` so the integration
  loads **at HA startup** — which is what injects the dashboard card resource into
  served pages (creating the entry at runtime is too late for the card). HA mutates
  that file at runtime; restore the committed fixture (`git checkout`) and don't
  commit the runtime version. Everything else under `.storage/` is gitignored.
  `tests/unit/test_integration_fixture_clean.py` fails when a runtime-written key
  reaches git, because that only breaks on a *pristine* checkout: the dirty fixture
  keeps passing locally against the container that dirtied it.
- **Anything resting on a Home Assistant framework contract** — device registry,
  entity registry, device automation, storage migration — **needs an assertion in the
  Docker tier.** The component tier mocks less than it used to, but a unit test that
  fakes the framework cannot see the framework's contract change underneath it. HA
  2026.8 split devices per config entry and broke device attachment across the
  custom-integration ecosystem with no advance signal.
- **Cross-version behaviour needs an upgrade test**, not just a fresh-boot test: boot
  a frozen older HA against a seeded config dir, then boot the current one against
  the same dir so HA runs its own migration in between. The fixtures are specific to
  what your integration stores, so the template doesn't ship this tier. Add it (and a
  job in `ha-beta.yml`) once your integration persists anything HA migrates.

## Mutation testing (a PR gate)

The four tiers above measure *coverage* — that a line ran. Mutation testing
measures whether a test would have **failed** if that line were wrong. It is the
difference between a suite that executes the code and a suite that actually
asserts on it.

`mutation.yml` runs on every PR, in two jobs:

```bash
bash ci/test-mutation-python.sh            # mutmut, changed functions only
bash ci/test-mutation-python.sh --all      # the whole configured surface
bash ci/test-mutation-frontend.sh          # Stryker, changed line ranges only
bash ci/test-mutation-frontend.sh --all
```

- **It only scores what your branch touched.** `ci/mutation_scope.py` maps the
  diff to mutmut mutant-name filters (changed line → enclosing function, via
  `ast`) and Stryker `--mutate` line ranges. Scoping to whole files would fail a
  PR for debt it didn't create.
- **The mutable surface is an allowlist**, in exactly one place per language:
  `only_mutate` in `[tool.mutmut]` (pyproject.toml) and `mutate` in
  `stryker.conf.json`. It covers the pure Python core and `utils.ts` / `i18n.ts`
  — the code the *fast* tiers exercise. HA-coupled modules and the DOM-heavy
  `panel.ts`/`card.ts` are excluded on purpose: mutating them would mean running
  the component or Docker tier once per mutant for a score that mostly reports
  "nothing covers this". Widen the allowlist when you add unit tests that would
  make the score mean something.
- **The gate is a mutation score of 80%**, set in `[tool.mutation-gate] break`
  and mirrored in `thresholds.break` (stryker.conf.json). Keep the two equal.
- **Kill surviving mutants with real assertions.** If a mutant is genuinely
  *equivalent* — it cannot change observable behaviour — annotate it at the
  source (`# pragma: no mutate`, `// Stryker disable next-line <mutator>`) with a
  one-line reason. Never blanket-disable a file, and never lower the threshold to
  get to green.
- **Tests that read `src/*.ts` off disk belong in a `*-parity.test.js` file.**
  Inside Stryker's sandbox they read *mutated* source, so any mutant that changes
  a string literal turns them red and is scored as "killed" by a test that never
  ran the behaviour. `vitest.stryker.config.js` excludes that suffix; the normal
  `ci/test-frontend.sh` run still includes it.
- Label a PR `skip-mutation` to bypass both jobs.

- **A unit test that reads a repo file off disk needs that file in `also_copy`.**
  mutmut runs the suite inside a `mutants/` copy holding only the source paths and
  the tests, so a test that loads `ci/check-ha-version.py` by path, or reads the
  seeded Docker fixture, dies at collection there. The trap is that it only breaks a
  PR that *also* touches mutable Python — every other PR skips mutmut and never finds
  out. List the file's **directory**: mutmut `copy2`s a bare file without creating
  its parent, and only `copytree`s a directory into place.

`tests/unit/conftest.py` executes the pure modules under their **real** dotted
name (`custom_components.example_integration.<mod>`, with stub parent packages so
the HA-importing `__init__.py` never runs) and aliases them to `ex.<mod>`. Keep
it that way: mutmut matches a mutant's path-derived key against the function's
`__module__`, and a mismatch makes every mutant look untested. It also has to
stay in `tests/unit/` rather than `tests/` — as a root conftest its stub parent
packages would shadow the real integration for the component tier, where Home
Assistant imports `custom_components.example_integration` itself.

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

## Linting & typing

- Python is linted and formatted with **ruff** (config in `pyproject.toml`,
  enforced by `lint.yml`). Run `ruff check custom_components tests ci scripts` and
  `ruff format --check …` before pushing; `ruff format` / `ruff check --fix` apply
  fixes.
- The integration is **fully typed** (ships `py.typed`); `lint.yml` runs `mypy
  custom_components/example_integration` with Home Assistant installed. Run it
  locally first: `pip install mypy homeassistant && mypy
  custom_components/example_integration`. User-facing exceptions are localized
  (translation keys under `strings.json` → `exceptions`). `[tool.mypy]
  python_version` and the job's `python-version` both track Home Assistant's Python
  floor rather than the integration's — see "Home Assistant versions" under CI.
- The template demonstrates Platinum-tier practices but **does not stamp a
  `quality_scale` tier** in the manifest — the real tier depends on your domain
  after forking. See `.amazonq/rules/testing-and-workflow.md`.

## Renaming

- `python scripts/rename.py your_domain "Your Name"` rewrites every placeholder
  (domain, display name, web-component / CSS / symbol prefixes), renames the
  component directory + seeded fixtures, and tidies with ruff. Use it instead of a
  manual find-and-replace.

## CI

- `lint.yml` — ruff lint + format check; **mypy** strict typing with Home Assistant
  installed (preceded by `ci/check-ha-version.py`, which fails the job if pip
  resolved a stale HA); **vale** prose linting, diff-scoped; and
  `changelog-release-gap`, which fails a PR editing an already-released CHANGELOG
  section (`ci/check-changelog-release-gap.py`).
- `test.yml` — vitest, pure pytest unit, **component (in-process HA)**, i18n
  coverage, HACS validation, hassfest.
- `mutation.yml` — mutation testing (mutmut + Stryker) on the code a PR changed;
  fails below an 80% mutation score. `skip-mutation` label bypasses it.
- `integration.yml` — Docker-based integration tests (no HA harness installed).
- `e2e.yml` — Docker + Playwright; uploads the Playwright report on failure.
- `pytest_coverage.yml` + `post_coverage_to_pr.yml` — coverage comment on PRs. Split
  in two because the PR-triggered half runs the PR's own code and must not hold a
  write token; the `workflow_run` half posts the comment from the base branch and
  never checks the PR out.
- `ha-beta.yml` — **nightly early warning**, gates nothing. Runs the Docker and
  browser tiers against `HA_TAG=beta` plus mypy against a pre-release HA, and
  files or updates a single `ha-beta-regression` issue on failure.
- `walkthrough-preview.yml` — per-PR video walkthrough: captures the tour, publishes
  the gif/mp4 to `gh-pages`, posts a sticky comment embedding the gif inline (soft gate).
- `hacs.yml` — HACS validation.
- `release.yml` — PR-merge-driven release (version ↔ PANEL_VERSION ↔ CHANGELOG
  checks; builds the zip).
- `dependabot-auto-merge.yml` — squash-merges a Dependabot PR once **every** check on
  the head commit is green. Not `gh pr merge --auto`, which waits only on branch
  protection's hand-maintained required-checks list: that list drifts out of sync with
  the workflows' actual jobs, and a bump can merge while a job it doesn't name is
  failing. Keep required status checks configured anyway, as defense in depth for
  human merges.

### Home Assistant versions

- **PRs test `stable`** — what users actually run. The container version is `HA_TAG`
  in `tests/integration/docker-compose.yml`, defaulting to `stable`; override it
  locally with `HA_TAG=beta bash ci/e2e-up.sh`.
- **A nightly tests `beta`.** HA beta week is public roughly four weeks ahead of a
  release, so that is the warning window. HA 2026.8 split devices per config entry and
  broke device attachment across the custom-integration ecosystem with no advance
  signal, which is the kind of thing this exists to catch.
- **Any job that `pip install`s Home Assistant must run on a Python at or above HA's
  own floor, and must verify what pip actually resolved.** When the runner's Python is
  too old, pip does not fail — it quietly backtracks to the last HA release that
  supported that Python, and the job goes green having checked an API nobody runs. Run
  `python ci/check-ha-version.py` (add `--pre` when installing with `pip install
  --pre`) in every such job.
- **`[tool.mypy] python_version` tracks HA's floor, not ours.** HA's source uses
  syntax from its own minimum Python; target anything older and mypy cannot parse HA
  at all — it exits on a syntax error having checked nothing.
- **A diagnostic step must never be able to fail the suite it precedes.** The
  version-report steps in `ha-beta.yml` carry `continue-on-error: true` for exactly
  that reason.

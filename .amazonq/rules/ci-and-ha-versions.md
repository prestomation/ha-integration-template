---
title: CI, mutation testing and Home Assistant versions
summary: What each CI workflow gates, the mutation and typing gates, vale, and how to test the right Home Assistant.
---

# CI, mutation testing and Home Assistant versions

## Workflows

| Workflow | What it does |
|---|---|
| `lint.yml` | ruff, mypy (HA installed), vale, `docs-audit`, `changelog-release-gap` |
| `test.yml` | vitest, pytest unit and component, i18n coverage, HACS validation, hassfest |
| `mutation.yml` | mutmut and Stryker on the changed code, 80% gate |
| `integration.yml` | Docker integration tests, with no HA harness installed |
| `e2e.yml` | Docker and Playwright; uploads the report on a failure |
| `walkthrough-preview.yml` | the walkthrough gif comment ([pr-workflow.md](pr-workflow.md#walkthrough-video)) |
| `docs-preview.yml` | builds the docs site for a PR and links the changed pages |
| `ha-beta.yml` | nightly against HA `beta`; gates nothing, files `ha-beta-regression` |
| `pytest_coverage.yml` | runs the coverage; `post_coverage_to_pr.yml` posts the comment |
| `release.yml` | tags and publishes on merge ([changelog-and-release.md](changelog-and-release.md)) |
| `preview-release.yml` | an installable `X.Y.Z.dev<pr>` build for a labelled PR |
| `docs-deploy.yml` | publishes the docs site after a stable release |
| `dependabot-auto-merge.yml` | merges a Dependabot PR when every check on its head is green |
| `hacs.yml` | HACS validation |

- **A pipe hides a failure.** `pytest … | tee log` takes the exit status of `tee`. Put
  `set -o pipefail` at the top of each `run:` block that pipes a test runner, and write an
  output guard that names what must not appear, not only what must.
- **A diagnostic step must never fail the suite after it.** Version reports in
  `ha-beta.yml` carry `continue-on-error: true`.
- **A check that no PR runs shares its inputs with one that does.** `ha-beta.yml` runs
  only on a schedule, so its inputs come from files that a PR lane also reads.
- **A job that runs PR code holds a read-only token.** A workflow that must write splits
  into a build job and a publish job that runs no PR code (`walkthrough-preview.yml`,
  `docs-preview.yml`). A Dependabot PR is a same-repo PR and gets the write token.
- **Each workflow sets `permissions: contents: read` at the top.** A job that needs more
  asks for it in its own block. A job with no block gets the repository default token,
  so `test_ci_action_pins.py` counts it as a write job and requires pinned actions.
- `pytest_coverage.yml` runs the PR's code with no write token. `post_coverage_to_pr.yml`
  runs from the base branch on `workflow_run` and never checks the PR out.
- `dependabot-auto-merge.yml` waits through `ci/wait_for_checks.py` for every check on
  the head commit. It does not trust the required-checks list of branch protection,
  which is kept by hand and drifts. Keep required checks on anyway, for human merges.
- `ci/setup-ci-deps.sh` installs every CI dependency (Python into `.venv`, npm, vale,
  ffmpeg, Docker, Chromium). It is idempotent and safe to run again; `FORCE=1` reinstalls
  and `SKIP_*` leaves a part alone. A SessionStart hook runs it; the log is
  `/tmp/setup-ci-deps.log`.

## Mutation testing

`mutation.yml` gates every PR at an 80% mutation score on the code that the PR changed.
Coverage says that a line ran. Mutation testing says that a test fails if the line is
wrong.

```bash
bash ci/test-mutation-python.sh            # mutmut, changed functions only
bash ci/test-mutation-frontend.sh          # Stryker, changed line ranges only
# add --all to score the whole configured surface
```

- `ci/mutation_scope.py` maps the diff to mutmut name filters (changed line to enclosing
  function) and Stryker `--mutate` ranges. Scoring whole files would fail a PR for old debt.
- **The mutable surface is an allowlist** in 1 place per language: `only_mutate` in
  `[tool.mutmut]` (`pyproject.toml`) and `mutate` in `stryker.conf.json`. It holds the
  pure Python core and `utils.ts` and `i18n.ts`. Widen it when you add unit tests that
  make the score mean something.
- It excludes modules that import HA at run time, the data modules (`const.py`,
  `api_surface.py`), and `panel.ts` and `card.ts`, which only the browser tier covers.
- The threshold is `[tool.mutation-gate] break`, mirrored in `thresholds.break`. Both
  runners fail on a mismatch. **Never lower it to get green.**
- **Kill a surviving mutant with a real assertion.** For a genuinely equivalent mutant,
  annotate the source (`# pragma: no mutate`, `// Stryker disable next-line <mutator>`)
  with a 1-line reason. Never disable a whole file.
- A test that reads `src/*.ts` off disk goes in a `*-parity.test.js` file.
  `vitest.stryker.config.js` excludes that suffix, because under Stryker it reads mutated
  source and kills mutants it never ran.
- **Keep the root `vitest` on version 4.** The Stryker vitest runner 10.0.0 runs no test
  per mutant under vitest 5, so every mutant survives. Dependabot holds the major back.
  Before a move, `bash ci/test-mutation-frontend.sh --all` must print
  `Ran N tests per mutant on average.` with N above 0.
- A PR that changes the npm manifests, the Stryker or vitest config, or the mutation
  scripts, and no TypeScript, is scored on `utils.ts`. `ci/mutation_report.py` fails a
  run in which no test ran against a scored mutant.
- Label a PR `skip-mutation` to bypass both jobs.

## Typing and quality scale

- The integration is fully typed and ships `py.typed`. The template uses the practices
  of the **Platinum** quality scale, but it stamps no `quality_scale` tier in
  `manifest.json`. The tier depends on the domain that you build. Add the key and a
  `quality_scale.yaml` ledger when the scope is settled.
- Run mypy before you push:
  `pip install -r requirements-typing.txt && mypy custom_components/example_integration`.
- **`requirements-typing.txt` is the only place that names a mypy dependency.** `lint.yml`,
  `ha-beta.yml` and `ci/setup-ci-deps.sh` install from it. Add a new stub package there.
- `typings/voluptuous/*.pyi` makes mypy read `voluptuous` as probatio, the way HA 2026.9
  and later alias it. Without the stubs, mypy fails against HA 2026.10. Delete them when
  the code imports probatio directly.
- User-facing exceptions are localized ([architecture.md](architecture.md#localized-text)).
- Python is linted and formatted with ruff. Run
  `ruff check custom_components tests ci scripts` and `ruff format --check` on the same
  paths. After `scripts/rename.py`, a longer name can make a line too long: fix it by hand.

## Home Assistant versions

- **PRs test `stable`.** `HA_TAG` in `tests/integration/docker-compose.yml` defaults to
  it. Override locally with `HA_TAG=beta bash ci/e2e-up.sh`. The nightly tests `beta`, about
  4 weeks before a release.
- **A job that installs HA runs on a Python at or above HA's floor, and checks what pip
  resolved.** On an older Python, pip goes back to an old HA and the job checks an API
  that nobody runs. Run `python ci/check-ha-version.py` (`--pre` for a pre-release).
- `[tool.mypy] python_version` follows HA's floor. HA's own source uses syntax from its
  minimum Python, and an older target cannot parse it.
- Read the version from `homeassistant.const.__version__`. `homeassistant.__version__`
  does not exist.

## Vale

- The `vale` job runs the pinned `ai-tells` style and the `STE` style over the files
  that `.vale.ini` names: `README.md`, `CHANGELOG.md`, `docs/guide/**/*.md`, the
  canonical `docs/*.md`, `docs/design/architecture.md`, `website/docs/intro.md`,
  `strings.json`, `services.yaml` and `locales/en.json`.
- The job is diff-scoped (`filter_mode: added`), but a rule applies to a whole block. An
  edit to 1 line of a paragraph puts the whole paragraph in scope. Compare the set of hits
  in each edited file with `origin/main`, not only the lines you touched.
- **A clean local run is weak evidence.** The action pins its own binary. Match the
  `tokens` regexes in `styles/ai-tells/<Rule>.yml` against the block by hand. Keep at most
  1 comma in a bullet after a modal or a pronoun, or `VerbTricolon` can fire.
- Run `vale sync && vale <paths>` locally. Disable an accepted false positive in
  `.vale.ini` (`ai-tells.RuleName = NO`) or inline with `<!-- vale ai-tells.RuleName = NO -->`.
- No bot bumps the pinned `ai-tells.zip` in `.vale.ini`. Bump it by hand now and then.

## Skills

- The `open-work` skill only reports open work, sorted by who must act next.
- The `preview-comment` skill drafts the note that tells a reporter a preview build is
  ready. It posts the note only after the maintainer approves the exact text.
- The `ux-review` skill reviews a surface of the running panel against a brief.

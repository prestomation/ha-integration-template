# HA Integration Template — Claude Code memory

@AGENTS.md

The project's workflow, conventions, and **hard gates** live in `AGENTS.md`
(imported above) and `.amazonq/rules/`. Read them before pushing.

Four gates worth repeating because they are easy to miss:

1. **Every PR that touches the panel or card UI
   (`custom_components/example_integration/frontend/src/`) MUST include current
   screenshots** of the changed surface — captured with the Playwright harness,
   committed under `docs/images/`, and embedded in the PR body (SHA-pinned
   `raw.githubusercontent.com` URL, HTML `<img>` tag). See AGENTS.md "Workflow".

2. **Every PR that adds a _new user-facing UI feature_ should keep the video
   walkthrough current — but CI captures it; you never commit a video.**
   `walkthrough-preview.yml` runs `tests/e2e/videos.capture.ts` on every PR, publishes
   the gif/mp4 to an orphan `gh-pages` branch, and posts a **sticky PR comment that
   embeds the gif inline** (via a `raw.githubusercontent.com` URL — no GitHub Pages
   setup needed). The gate is *editing the tour*: when a feature adds a new surface,
   extend `videos.capture.ts` to step through it in the same PR. `docs/videos/` is
   gitignored and media never touches `main` (zero repo bloat); capture is a soft gate.
   Pure bug-fix / styling PRs stay on the screenshots gate only. See AGENTS.md "Workflow".

3. **The component test tier and the Docker integration tier cannot share a pytest
   invocation** — `pytest-homeassistant-custom-component` pulls in `pytest-socket`,
   which blocks the real network the Docker tier needs. Run them separately
   (`ci/test-python-component.sh` vs `ci/test-python-integration.sh`). See
   AGENTS.md "Tests".

4. **`mutation.yml` gates every PR at an 80% mutation score on the code it
   changed** (mutmut for Python, Stryker for TypeScript). Surviving mutants mean a
   test asserts nothing useful — kill them, or annotate a genuinely equivalent
   mutant with a reason. Never lower the threshold to get green. The mutable
   surface is an allowlist: `only_mutate` in `[tool.mutmut]` and `mutate` in
   `stryker.conf.json`. See AGENTS.md "Mutation testing".

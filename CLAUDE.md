# HA Integration Template — Claude Code memory

@AGENTS.md

The project's workflow, conventions, and **hard gates** live in `AGENTS.md`
(imported above) and `.amazonq/rules/`. Read them before pushing.

Two gates worth repeating because they are easy to miss:

1. **Every PR that touches the panel or card UI
   (`custom_components/example_integration/frontend/src/`) MUST include current
   screenshots** of the changed surface — captured with the Playwright harness,
   committed under `docs/images/`, and embedded in the PR body (SHA-pinned
   `raw.githubusercontent.com` URL, HTML `<img>` tag). See AGENTS.md "Workflow".

2. **The component test tier and the Docker integration tier cannot share a pytest
   invocation** — `pytest-homeassistant-custom-component` pulls in `pytest-socket`,
   which blocks the real network the Docker tier needs. Run them separately
   (`ci/test-python-component.sh` vs `ci/test-python-integration.sh`). See
   AGENTS.md "Tests".

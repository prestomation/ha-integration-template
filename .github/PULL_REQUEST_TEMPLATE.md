<!--
Thanks for contributing! Please confirm the gates below before requesting review.
See AGENTS.md for the full conventions, and the README's "Guardrails" section for
what each automated check catches.
-->

## Summary

<!-- What does this change do, and why? -->

## Checklist

- [ ] Ran the relevant test tiers locally (unit / component / integration / e2e) — see AGENTS.md "Tests"
- [ ] `ruff check` and `ruff format --check` pass
- [ ] **UI change?** Screenshots of the changed surface are embedded below (captured with `tests/e2e/screenshots.capture.ts`, committed under `docs/images/`, HTML `<img>` with a SHA-pinned `raw.githubusercontent.com` URL) — this is a hard gate. Each one visually inspected, and the new surface asserted on under `tests/e2e/tests/`
- [ ] **New integrator-facing surface?** Declared in `api_surface.py` (service, event + payload spine, entity platform/attribute, websocket command, HTTP route), with a `SURFACE_KINDS` row if it's a new kind
- [ ] New service / event / convention is documented (`services.yaml` + `strings.json` at translation parity / `docs/EVENTS.md` / `.amazonq/rules/`)
- [ ] User-facing change is in `CHANGELOG.md` and (if a headline feature) `README.md` — in a section whose version is **not** already released, or with a version bump opening a new one
- [ ] New prose reads clean under vale (`vale sync && vale <changed files>`); CI lints only the lines this PR touches

## Screenshots

<!-- For any panel/card UI change. Delete this section if not applicable. -->

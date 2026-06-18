<!--
Thanks for contributing! Please confirm the gates below before requesting review.
See AGENTS.md for the full conventions.
-->

## Summary

<!-- What does this change do, and why? -->

## Checklist

- [ ] Ran the relevant test tiers locally (unit / component / integration / e2e) — see AGENTS.md "Tests"
- [ ] `ruff check` and `ruff format --check` pass
- [ ] **UI change?** Screenshots of the changed surface are embedded below (captured with `tests/e2e/screenshots.capture.ts`, committed under `docs/images/`, HTML `<img>` with a SHA-pinned `raw.githubusercontent.com` URL) — this is a hard gate
- [ ] New service / event / convention is documented (`services.yaml` + `strings.json` at translation parity / `docs/EVENTS.md` / `.amazonq/rules/`)
- [ ] User-facing change is in `CHANGELOG.md` and (if a headline feature) `README.md`

## Screenshots

<!-- For any panel/card UI change. Delete this section if not applicable. -->

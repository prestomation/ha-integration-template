#!/usr/bin/env bash
# Run the Playwright e2e tests. Assumes HA is running on $HA_URL, the panel JS is
# built (ci/build-panel.sh), and Chromium is installed (ci/setup-browser-env.sh).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../tests/e2e"
if [ ! -d node_modules ]; then
  npm ci 2>/dev/null || npm install --no-audit --no-fund
fi
exec npx playwright test "$@"

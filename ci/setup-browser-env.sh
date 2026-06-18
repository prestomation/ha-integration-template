#!/usr/bin/env bash
# Prepare the environment for the Docker integration + Playwright e2e tiers.
#
# Idempotent: safe to run repeatedly (e.g. from a Claude Code SessionStart hook).
# Starts the Docker daemon (needed for the HA container) and installs the
# Chromium browser Playwright drives. Non-fatal if Docker can't start so it never
# blocks unrelated sessions — the e2e scripts surface a clear error instead.
set -uo pipefail

log() { echo "[setup-browser-env] $*"; }

if docker info >/dev/null 2>&1; then
  log "Docker daemon already running."
else
  log "Starting Docker daemon..."
  if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
    sudo -n dockerd >/tmp/dockerd.log 2>&1 &
  else
    dockerd >/tmp/dockerd.log 2>&1 &
  fi
  for _ in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then break; fi
    sleep 1
  done
  docker info >/dev/null 2>&1 && log "Docker daemon is up." \
    || log "WARNING: Docker daemon did not start; HA-dependent tests will not run here."
fi

# Install Playwright Chromium for the e2e suite (best-effort).
if [ -d tests/e2e ]; then
  log "Ensuring Playwright Chromium is installed..."
  (cd tests/e2e && (npm ci >/dev/null 2>&1 || npm install --no-audit --no-fund >/dev/null 2>&1) \
    && npx playwright install --with-deps chromium >/dev/null 2>&1) \
    && log "Playwright Chromium ready." || log "WARNING: Playwright install skipped/failed."
fi

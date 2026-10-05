#!/usr/bin/env bash
set -euo pipefail
# Docker integration tier. Assumes Home Assistant is already running.
#
# These tests drive a real container over HTTP, so the pytest-socket plugin has to
# be off. pytest-homeassistant-custom-component pulls it in. CI leaves the harness
# out of this lane, so there the flags are inert, but a local environment that has
# it (the .venv that ci/setup-ci-deps.sh builds installs everything) needs them:
#
# - Both spellings of the plugin, because its *registered* name is `socket` (its
#   pytest11 entry point), not `pytest_socket`. `-p no:` for a plugin that is not
#   installed is a no-op, so naming both is free.
# - `-p no:homeassistant` too: the harness applies the block in its own autouse
#   fixture, which calls `pytest_socket.disable_socket` itself. This lane wants none
#   of the harness, because it drives a real container rather than an in-process
#   Home Assistant.
#
# Arguments pass through, so a targeted run is possible. With none, pytest takes
# the `.` below and runs everything, which is what CI does.
cd "$(dirname "$0")/../tests/integration"
python -m pytest . -v --tb=short -p no:socket -p no:pytest_socket -p no:homeassistant "$@"

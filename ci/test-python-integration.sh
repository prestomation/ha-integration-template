#!/usr/bin/env bash
# Docker integration tier. Assumes Home Assistant is already running.
# -p no:pytest_socket disables pytest-socket (pulled in by the HA harness if it's
# present in the same env) so real HTTP to the container is allowed.
set -euo pipefail
cd tests/integration
python -m pytest . -v --tb=short -p no:pytest_socket

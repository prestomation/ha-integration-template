#!/usr/bin/env bash
# Component tier — real in-process Home Assistant via
# pytest-homeassistant-custom-component. Pulls in pytest-socket (blocks network);
# run separately from the Docker integration tier. asyncio_mode is set here
# because the pure unit tier deliberately has no pytest-asyncio.
set -euo pipefail
python -m pytest tests/component -v -o asyncio_mode=auto

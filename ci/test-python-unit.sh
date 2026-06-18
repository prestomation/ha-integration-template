#!/usr/bin/env bash
# Pure unit tier — needs only `pip install pytest` (no HA harness).
set -euo pipefail
find custom_components -name "*.py" -exec python -m py_compile {} +
python -m pytest tests/unit -v

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../custom_components/example_integration"
zip -r ../../example_integration.zip . \
  -x "*/__pycache__/*" -x "__pycache__/*" -x "*.pyc" \
  -x "*/node_modules/*" -x "*/src/*" -x "*/test/*" \
  -x "rollup.config.mjs" -x "tsconfig.json" \
  -x "package.json" -x "package-lock.json"

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec "${PYTHON_BIN:-python}" scripts/agent_config.py build "$@"

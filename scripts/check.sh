#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
"${PYTHON_BIN:-python}" scripts/agent_config.py check "$@"
"${PYTHON_BIN:-python}" scripts/agent_config.py compile "$@"
"${PYTHON_BIN:-python}" -m unittest discover -s tests -v

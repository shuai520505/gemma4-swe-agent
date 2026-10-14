#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
V0_VENV="${V0_VENV:-/workspace/venvs/gemma4}"
V0_WHEELS="${V0_WHEELS:-/workspace/official-wheels}"
if [ ! -x "$V0_VENV/bin/python" ]; then
  python -m venv "$V0_VENV"
fi
"$V0_VENV/bin/python" scripts/download_official_wheels.py "$V0_WHEELS"
"$V0_VENV/bin/python" -m pip install --no-cache-dir torch==2.14.1+cpu torchvision==0.29.1+cpu --index-url https://download.pytorch.org/whl/cpu
"$V0_VENV/bin/python" -m pip install --no-cache-dir -r requirements-dev.txt \
  "$V0_WHEELS/google_adk-1.36.1-py3-none-any.whl" \
  "$V0_WHEELS/google_genai-2.11.0-py3-none-any.whl" \
  "$V0_WHEELS/adk_submission-0.2.13-py3-none-any.whl" \
  "$V0_WHEELS/adk_eval_core-0.1.0-py3-none-any.whl" \
  "$V0_WHEELS/swegemma-0.2.11-py3-none-any.whl"
"$V0_VENV/bin/python" -m pip check
PYTHON_BIN="$V0_VENV/bin/python" scripts/check.sh

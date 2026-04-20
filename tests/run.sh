#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

rm -rf .venv
rm -f report.html

UV_PROJECT_ENVIRONMENT=.venv.linux uv run pytest "$@"

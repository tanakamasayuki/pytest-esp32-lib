#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

find . -type d \( -name build -o -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +

rm -rf .venv .venv.linux .venv.win
rm -f report.html
find . -type f -name "*.log" -delete

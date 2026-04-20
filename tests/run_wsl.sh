#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/run_build.sh" "$@"

WIN_RUN_TEST_BAT="$(wslpath -w "${SCRIPT_DIR}/run_test.bat")"
cmd.exe /C "${WIN_RUN_TEST_BAT}" "$@"

#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/run_build.sh" "$@"

WIN_TEST_DIR="$(wslpath -w "${SCRIPT_DIR}")"
CMD_COMMAND="cd /d ${WIN_TEST_DIR} && call run_test.bat"

for arg in "$@"; do
  ESCAPED_ARG="${arg//\"/\"\"}"
  CMD_COMMAND+=" \"${ESCAPED_ARG}\""
done

cmd.exe /C "${CMD_COMMAND}"

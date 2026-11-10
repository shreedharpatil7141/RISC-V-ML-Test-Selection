#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <prepared-stage8-directory>" >&2
  exit 2
fi
python3 "$(dirname -- "${BASH_SOURCE[0]}")/run_stage8_enabled.py" --sim verilator --prepared "$1"

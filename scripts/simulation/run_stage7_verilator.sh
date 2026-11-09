#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <prepared-stage7-directory>" >&2
  exit 2
fi
grep -Fq 'STAGE7_PREPARATION READY stage6_compat=259 stage7_cases=13 images=13 references=13 errors=0' "$1/stage7_preparation.txt"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/run_stage4_4.py" --sim verilator --enable-a
python3 "$SCRIPT_DIR/run_stage6_enabled.py" --sim verilator --prepared "$1/stage6_compat"
python3 "$SCRIPT_DIR/run_stage7_enabled.py" --sim verilator --prepared "$1"

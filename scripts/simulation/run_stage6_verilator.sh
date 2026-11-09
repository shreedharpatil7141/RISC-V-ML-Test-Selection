#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <prepared-stage6-directory>" >&2
  exit 2
fi
if ! grep -Fq 'STAGE6_PREPARATION PASS stage5=248 stage6=11 total=259 images=259 references=259 errors=0' "$1/stage6_preparation.txt"; then
  echo "Prepared Stage 6 artifacts are missing or invalid: $1" >&2
  exit 2
fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/run_stage4_4.py" --sim verilator --enable-a
python3 "$SCRIPT_DIR/run_stage6_enabled.py" --sim verilator --prepared "$1"

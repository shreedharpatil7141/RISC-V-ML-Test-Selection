#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then echo "Usage: $0 <prepared-stage9.json>" >&2; exit 2; fi
python3 "$(dirname -- "${BASH_SOURCE[0]}")/test_stage9_coverage.py"
python3 "$(dirname -- "${BASH_SOURCE[0]}")/stage9_coverage.py" --sim verilator --prepared "$1"

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
for tool in python3 verilator make; do command -v "$tool" >/dev/null || { echo "ERROR: missing $tool" >&2; exit 1; }; done
command -v g++ >/dev/null || command -v clang++ >/dev/null || command -v c++ >/dev/null || { echo 'ERROR: missing C++ compiler' >&2; exit 1; }
python3 scripts/simulation/run_stage4_3.py --sim verilator

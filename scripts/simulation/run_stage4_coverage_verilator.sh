#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/simulation/run_stage4_coverage.py --sim verilator

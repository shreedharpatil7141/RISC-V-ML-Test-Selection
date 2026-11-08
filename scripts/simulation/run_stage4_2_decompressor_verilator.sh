#!/usr/bin/env bash
# Standalone Stage 4.2 RV32C decompressor exhaustive unit sweep.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || exit 1
cd "$ROOT" || exit 1

for tool in python3 verilator make g++; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: required tool '$tool' not found on PATH" >&2
    exit 1
  fi
done
python3 --version || exit 1
verilator --version || exit 1

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="sim_out_stage4_2_verilator_${RUN_ID}"
REPORT="reports/stage4_2_decompressor_verilator_${RUN_ID}.txt"
if [[ -e "$OUT" || -e "$REPORT" ]]; then
  echo "ERROR: fresh output/report path already exists: $OUT / $REPORT" >&2
  exit 1
fi
mkdir -p "$OUT" reports || exit 1

echo "[Stage 4.2 Verilator] Generating independent vectors..."
if ! python3 scripts/simulation/generate_stage4_2_vectors.py "$OUT/vectors.txt" >"$OUT/vectors.log" 2>&1; then
  cat "$OUT/vectors.log"
  echo "ERROR: vector generation failed" >&2
  exit 1
fi
cat "$OUT/vectors.log"
grep -Fq 'RV32C_VECTOR_GENERATION PASS halfwords=65536 oracle_mismatches=0' "$OUT/vectors.log" || {
  echo "ERROR: vector generation marker missing" >&2; exit 1;
}
[[ -s "$OUT/vectors.txt" ]] || { echo "ERROR: missing/empty vectors" >&2; exit 1; }

echo "[Stage 4.2 Verilator] Building standalone testbench..."
if ! verilator --binary --timing --top-module tb_rv32c_decompressor \
  --Mdir "$OUT/obj_dir" -Wall -Wno-fatal \
  rtl/decoder/rv32c_decompressor.sv \
  verification/environment/tb_rv32c_decompressor.sv \
  >"$OUT/build.log" 2>&1; then
  cat "$OUT/build.log"
  echo "ERROR: Verilator build failed" >&2
  exit 1
fi
cat "$OUT/build.log"

echo "[Stage 4.2 Verilator] Running 65,536 halfword patterns and hand anchors..."
if ! "$OUT/obj_dir/Vtb_rv32c_decompressor" "+VECTORS=$OUT/vectors.txt" >"$OUT/run.log" 2>&1; then
  cat "$OUT/run.log"
  echo "ERROR: Verilator simulation failed" >&2
  exit 1
fi
cat "$OUT/run.log"
if ! python3 scripts/simulation/check_stage4_2_sim_log.py "$OUT/run.log" >"$OUT/logcheck.log" 2>&1; then
  cat "$OUT/logcheck.log"
  echo "ERROR: Verilator log validation failed" >&2
  exit 1
fi
cat "$OUT/logcheck.log"
grep -Fxq 'RV32C_SIM_LOG_CHECK PASS terminal_markers=1 pass_markers=1 halfwords=65536 mismatches=0 anchors=16' "$OUT/logcheck.log" || {
  echo "ERROR: strict log-checker marker missing" >&2; exit 1;
}
{
  echo "Simulator: Verilator"
  echo "Run: $RUN_ID"
  cat "$OUT/vectors.log"
  cat "$OUT/logcheck.log"
  grep -F 'RV32C_DECOMPRESS_UNIT PASS' "$OUT/run.log"
  echo 'STAGE4_2_DECOMPRESSOR_VERILATOR PASS halfwords=65536 anchors=16'
} > "$REPORT"
cat "$REPORT"
echo "Output: $OUT"
echo "Report: $REPORT"

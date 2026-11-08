# Verification architecture and implemented Stage 3/4 flows

The project began with a planned modular SystemVerilog environment. The
current Stage 3 evidence is produced by the directed self-checking testbenches
and Python orchestration described here; it does not imply that the planned
generator/driver/monitor/scoreboard component tree exists. UVM is not used.

## Current Stage 3 evidence path

1. `prepare_stage5.py` reads the checked-in per-suite `manifest.csv` files,
   assembles each `.s` source, runs the independent Python ISS, and creates
   temporary hex files, golden ISS retirement traces, M operand/result
   sidecars, and cycle-model expectations in a fresh simulator output folder.
2. Each simulator compiles and runs arithmetic, M decoder, pipeline,
   divider, and wrapper testbenches. It then runs all 209 system cases on the
   single-cycle golden core and the iterative-M pipeline.
3. `check_stage5_results.py`, `stage4_lib.py`, and `stage5_coverage.py` check
   unit result markers, system PASS markers, exact pipeline/golden/ISS trace
   equality, cycle timing, divider start/done/busy/abort protocol, the 108-bin
   M dictionary, and the 16-element pipeline event vector. Missing or
   malformed inputs fail the check and return a nonzero exit status.
4. The canonical Stage 3.7 commands write separate simulator reports and
   timestamped output directories. Exact commands and owner reports are in
   `stage3_artifact_manifest.md` and
   `../architecture/stage3_rv32m_status.md`.

The ISS (`rv32i_iss.py`) is a Python architectural model and does not import
or call RTL. `m_model.py` uses shift/add multiplication and restoring
division for model-side arithmetic checks. Testbenches also contain
self-checking reference calculations. Pipeline-event counters are RTL
microarchitectural observations; the ISS is used only for architectural
cross-checks.

## Regression inventory

| Suite | Cases | Purpose |
|---|---:|---|
| `rv32i` | 106 | Base arithmetic, control flow, memory, and synchronous fault behavior |
| `pipeline` | 63 | Existing pipeline data/control hazards and retirement checks |
| `pipeline_m` | 8 | M forwarding, holds, wrong-path and fault interactions |
| `m_extension` | 22 | Golden-core M operation and corner cases |
| `pipeline_div` | 8 | Iterative divider protocol and pipeline interactions |
| `pipeline_div_coverage` | 2 | Targeted RS1 load-use and divider forwarding-source coverage |
| **Total** | **209** | Directed regression only |

Stage 3.7 reports show all 209 pass on both simulators. Per-test cycle and
protocol values are retained in each report. Divider unit testing records
262,144 W=8 checks and 1,600 W=32 checks; the exact simulator-specific unit
results and event hits are tabulated in the architecture status document.

## Future verification work

The longer-term plan mentions generated constrained-random tests, class-based
drivers, monitors, scoreboards, generic coverage crosses, A/CSR verification,
interrupt injection, and architectural compliance testing. Those components
or results must not be inferred from the Stage 3 regression. The RISC-V
architectural test suite has not been run, and no compliance claim is made.
The MATLAB machine-learning pipeline has no reported Stage 3 results.

## Stage 4 RV32IMC evidence path

`prepare_stage4_4.py` assembles the fixed legacy and mixed-width C sources,
generates independent ISS traces, and checks all expected halt causes before
simulation. The full XSim/Verilator runners preserve the 209-case C-disabled
suite, execute 21 C-enabled cases on golden and pipeline RTL, compare full
architectural traces against the ISS and each other, and validate the timing
model and divider protocol. Seven units include the independent 65,536-pattern
decompressor check. The coverage checker derives architectural bins from ISS
retirement/STOP records and microarchitectural events from DUT sidecars and
RTL COV counters; these evidence classes are reported separately.

The current separate simulator reports each show 230 cases, 460 ISS
comparisons, 230 pipeline-to-golden traces, seven units, all 16 pipeline
events, and zero coverage errors. Verilator-only mutation evidence combines
eight detections from the original ten-mutant campaign with a focused run of
C07/C09 after parser correction. The original two INVALID records and their
trace reanalysis are retained; this is not one fresh ten-mutant run. No XSim
mutation campaign is claimed. Exact commands and expected markers are in
[`README.md`](README.md) and the
[`stage4_coverage_manifest.md`](stage4_coverage_manifest.md).

The reference model is software-only and independent of decompressor/pipeline
RTL. C-disabled mode keeps released Stage 3 behavior. This is finite directed
verification, not full architectural compliance; no synthesis/timing or ML
result is claimed.

# Verification architecture and implemented Stage 3 flow

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
drivers, monitors, scoreboards, generic coverage crosses, CSR/A/C verification,
interrupt injection, and architectural compliance testing. Those components
or results must not be inferred from the Stage 3 regression. The RISC-V
architectural test suite has not been run, and no compliance claim is made.
The MATLAB machine-learning pipeline has no reported Stage 3 results.

# Machine Learning-Based Test Selection for Accelerated Functional Coverage Closure in RISC-V Processor Verification

**Status:** Stages 3, 4, and 5 are complete and released on `main`; Stage 5 is marked by annotated tag `stage5-complete`. Separate Stage 5 XSim and Verilator runs each passed 248 cases, 496 ISS comparisons, 248 pipeline-to-golden traces, eight unit suites, and atomic checks. Verilator-only mutation evidence spans the original run, focused A01/A02 run, and A02 saved-evidence reanalysis; original INVALID records remain preserved, and the updated A02 classifier implementation check remains unexecuted. Results are finite directed verification, not full architectural compliance. No multi-hart/RVWMO, synthesis/timing, unsupported extension, or ML result is claimed. Stage 4 release is recorded by the annotated `stage4-complete` tag on `main`.

## Overview
A simulation-based verification project with independently modeled RV32IMC
golden and pipeline cores plus a validated RV32A word-integer subset: LR.W,
SC.W, and nine AMOs. RV32C uses mixed 16/32-bit fetch and preserves original
PC, raw instruction bits, and length through retirement and precise fault
reporting. C- and A-disabled modes preserve prior-stage behavior. The RV32IM
multiplier is combinational; DIV/REM use a fixed 34-cycle iterative protocol
with pipeline holds. A verification is single-hart, no-wait-state, and has no
concurrent writer. Floating-point/Zc, CSR, privileged trap/interrupt machinery,
and Zifencei are not implemented. Results do not claim full compliance,
multi-hart/RVWMO validation, synthesis/timing evidence, or ML results.

## Toolchain
Stage 3 simulation uses Vivado 2026.1 XSim on Windows or Verilator 5.x,
Python 3, GNU make, and a C++ compiler under WSL. MATLAB work is planned and
has no results in this Stage 3 package. **UVM is not used.** No FPGA hardware
is required for the simulation evidence.

## Layout
| Folder | Contents |
|---|---|
| `rtl/` | Implemented RV32I/RV32M packages, core, pipeline, ALU, decoder, regfile, control, memory |
| `verification/environment/` | Self-checking RTL unit and pipeline testbenches used by the Stage 3 regressions |
| `tests/` | Directed (per extension), random, corner-case, integration tests |
| `dataset/` | `raw/`, `processed/`, `training/`, `reports/` (features, coverage, runs, bin_dictionary CSVs) |
| `matlab/` | Preprocessing, models, selection, evaluation, active learning, visualization |
| `scripts/` | Simulation, dataset and automation scripts |
| `documentation/` | Architecture, verification, ML and research docs |
| `reports/` | Generated regression/coverage/experiment reports |

## Key documents
- `PROJECT_PLAN.md` - stages, deliverables, exit criteria
- `IMPLEMENTATION_LOG.md` - running progress log
- `documentation/architecture/` - ISA scope, module definitions, microarchitecture
- `documentation/verification/` - component responsibilities, compile order
- `documentation/machine_learning/` - dataset schemas, MATLAB ML architecture
- `documentation/vivado_setup.md` - creating the `.xpr` project
- `documentation/machine_learning/stage15_final_integration.md` - integrated
  saved-evidence validation and reproduction limits

## Integrity rules
No fabricated simulation or ML results. No post-execution data as model input.
Offline replay is never presented as real simulation savings. No claim of full
RISC-V compliance without architectural-test validation.

## Quick start
```
# Stage 1 (single-cycle golden core)
scripts\simulation\run_stage1_xsim.bat                 # Vivado XSim (validated)
python scripts/simulation/run_stage1.py                 # Verilator (Linux)

# Stage 2 (5-stage pipeline vs golden core vs ISS)
scripts\simulation\run_stage2_xsim.bat                 # Vivado XSim
python scripts/simulation/run_stage2.py                 # Verilator (Linux)

# Consolidated Stage 3 RV32M regression (209 tests; XSim or Verilator)
scripts\simulation\run_stage3_regression_xsim.bat      # Windows CMD after Vivado setup
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage3_regression.py

# Separate, explicit Stage 3.6 mutation campaign (long running; Verilator in WSL)
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage6_mutation.py

# Full Stage 4 coverage + regression (230 cases; separate output/report per simulator)
scripts\simulation\run_stage4_coverage_xsim.bat
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage4_coverage_verilator.sh

# Explicit Verilator-only mutation campaign
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_mutation.py

# Stage 5 RV32A full XSim regression (Vivado CMD)
scripts\simulation\run_stage5_a_xsim.bat

# Stage 5 RV32A full Verilator regression (Windows CMD -> Ubuntu WSL)
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage5_a_verilator.sh

# Stage 5 Verilator mutation campaign (separate explicit command)
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage5_a_mutation.py

# Stage 15 integrated saved-evidence validation (Windows CMD; no simulator rerun)
scripts\machine_learning\validate_stage15.cmd
```

The Stage 4 coverage batch preserves all 209 C-disabled legacy cases and runs
21 RV32IMC cases. Each case is checked against the independent software ISS;
pipeline traces also match the golden RTL. It runs seven arithmetic, decoder,
pipeline, divider, wrapper, and decompressor unit suites. Mutation evidence
combines eight detections from the original run with focused C07/C09
detections; this was not one fresh ten-mutant run. XSim mutation results are
not claimed. See
[`documentation/architecture/stage4_4_pipeline.md`](documentation/architecture/stage4_4_pipeline.md)
and [`documentation/architecture/stage4_c_coverage_mutation.md`](documentation/architecture/stage4_c_coverage_mutation.md)
for the fetch/retirement contract, coverage and mutation scope, dependencies,
commands, reports, and expected markers. The Stage 4 file manifest is in
[`documentation/verification/stage4_coverage_manifest.md`](documentation/verification/stage4_coverage_manifest.md).

The Stage 5 A-extension specification, software, MEM transaction contract,
commands, evidence, and limitations are described in
[`documentation/architecture/stage5_0_rv32a_review.md`](documentation/architecture/stage5_0_rv32a_review.md).
The software gate compared all 230 preserved Stage 4 images and traces in
A-disabled mode. Stage 5 adds LR.W, SC.W, and nine word AMOs in the golden and
pipeline cores while preserving C/M and A-disabled modes. See the architecture
review for canonical Windows XSim and Windows CMD-to-WSL Verilator commands,
report paths, mutation provenance, and limitations. No Stage 5 completion tag
has been created.

The consolidated Stage 3 regression runs all 209 current system tests on the
single-cycle golden core and the M-enabled pipeline, compares architectural
traces against the independent ISS, checks the cycle model and divider
protocol counters, runs arithmetic/decoder/pipeline/divider/wrapper unit
suites, and requires all 108 defined M dictionary bins and 16 pipeline events.
The XSim command writes `reports/stage3_7_regression_xsim.txt` and a fresh
`sim_out_stage3_7_xsim_<UTC>/` directory. Verilator writes
`reports/stage3_7_regression_verilator.txt` and a fresh
`sim_out_stage3_7_verilator_<UTC>/` directory. The mutation campaign is a
separate command.

The existing script filenames `run_stage4.py`, `run_stage5.py`, and their
XSim counterparts are historical implementation-step names within the RV32M
extension. They do not select RISC-V ISA stages or change the Stage 1/2
scripts. The `run_stage3_regression` entry points reuse the final `run_stage5`
suite while keeping Stage 3.5 reports and mutation-harness behavior separate.
See [`documentation/architecture/stage3_rv32m_status.md`](documentation/architecture/stage3_rv32m_status.md)
for implementation scope and separate simulator evidence, and
[`documentation/verification/stage3_artifact_manifest.md`](documentation/verification/stage3_artifact_manifest.md)
for the Stage 3 artifact manifest and reproducibility map.

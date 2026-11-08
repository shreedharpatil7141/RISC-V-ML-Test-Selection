# Machine Learning-Based Test Selection for Accelerated Functional Coverage Closure in RISC-V Processor Verification

**Status:** Stage 3 RV32IM is complete and approved through Stage 3.9. Stage 4.2's standalone decompressor was owner-verified in XSim and Verilator (65,536 patterns, zero mismatches, 16 anchors each). Stage 4.3 mixed-width golden-core integration is implemented and awaits separate simulator validation; no Stage 4 completion is claimed. Stage 3.7 XSim and Verilator evidence remains separate (209/209 tests, all units, 108/108 finite M bins, 16/16 pipeline events). These are finite directed results, not architectural compliance.

## Overview
A simulation-based verification project whose currently implemented and
Stage 3-verified processor scope is a single-hart, in-order **RV32IM** core
with a five-stage pipeline and synchronous fault halting. C, A, CSR,
privileged trap/interrupt machinery, and Zifencei are not implemented. The
repository also contains planned machine-learning coverage-selection work;
no ML results are claimed.

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
```

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

# Machine Learning-Based Test Selection for Accelerated Functional Coverage Closure in RISC-V Processor Verification

**Status:** Stage 1 complete pending approval - single-cycle RV32I core verified under Verilator (XSim not yet run). See `IMPLEMENTATION_LOG.md`.

## Overview
A simulation-based verification framework for a single-hart, in-order
**RV32IMAC + Zicsr + Zifencei + M-mode** processor, verified with a
modular (non-UVM) SystemVerilog environment, plus a MATLAB machine-learning
pipeline that ranks candidate tests by expected *new* coverage per unit cost
and drives actual test-selection decisions.

## Toolchain
Windows - AMD Vivado 2026.1 (XSim) - SystemVerilog - MATLAB - CSV - Git.
**UVM is not used.** No FPGA hardware required.

## Layout
| Folder | Contents |
|---|---|
| `rtl/` | Processor RTL (packages, core, pipeline, ALU, decoder, regfile, control, memory, CSR, atomic, interfaces) |
| `verification/` | Generator, driver, monitor, reference model, scoreboard, coverage, assertions, environment |
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

## Quick start (Stage 1)
```
python scripts/simulation/run_stage1.py      # Verilator + Python; needs verilator, python3
scripts\simulation\run_stage1_xsim.bat       # Vivado XSim (UNTESTED)
```

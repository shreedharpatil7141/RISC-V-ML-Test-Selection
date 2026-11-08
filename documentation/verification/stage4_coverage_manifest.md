# Stage 4 coverage and mutation package manifest

This manifest describes the Stage 4 coverage/mutation checkpoint relative to
the committed Stage 4.4 pipeline checkpoint `82ccb33371c7629c92a860dfeb180a4d4466ffa2`.
It lists only Stage 4 additions/changes and concise evidence; it is not a full
project copy. Generated build trees, object files, `.hex` images, vector files,
caches, simulator work directories, and temporary mutation workspaces are
excluded.

## Implemented source and verification files

| File | Purpose | Dependencies / reproducibility | Expected evidence |
|---|---|---|---|
| `scripts/simulation/run_stage4_4.py` (modified) | C-disabled + C-enabled golden/pipeline regression, strict fresh-output checks, trace/timing/protocol checks, sidecar collection | Python 3; XSim 2026.1 or Verilator 5.x, GNU make, C++ compiler | `STAGE4_4_PIPELINE_<SIM> PASS legacy=209 rv32imc=21 full_trace_comparisons=460 units=7` |
| `verification/environment/tb_rv_pipe_stage4.sv` (modified) | DUT-derived attempted/retired/fault/squash/divider metadata observations; preserves the architectural trace | SystemVerilog simulator; shared Stage 4.4 RTL file list | One `COV` record and C-sidecar events per pipeline run |
| `tests/directed/rv32imc_pipeline/manifest.csv` (modified) | Adds the boundary-coverage program to the C pipeline suite | `coverage_boundaries.s`, independent C assembler/ISS | 21 C cases in preflight |
| `tests/directed/rv32imc_pipeline/coverage_boundaries.s` (new) | Exercises x15, signed immediate endpoints, shift 31, and stack offset 252 | RV32IMC test assembler | Included in the 21 C cases; expected ECALL |
| `scripts/simulation/run_stage4_coverage.py` (new) | Runs full regression then the independent coverage checker | Python 3; stage4_4 runner | `STAGE4_C_COVERAGE_<SIM> PASS cases=230 c_cases=21 patterns=65536 pipeline_events=16` |
| `scripts/simulation/run_stage4_coverage_xsim.bat` (new) | Windows XSim coverage entry point | Vivado 2026.1, Python 3, initialized CMD | Separate timestamped XSim report and `sim_out_stage4_4_xsim_<UTC>` |
| `scripts/simulation/run_stage4_coverage_verilator.sh` (new) | Ubuntu/WSL Verilator coverage entry point | Python 3, Verilator 5.x, GNU make, C++ compiler | Separate timestamped Verilator report and `sim_out_stage4_4_verilator_<UTC>` |
| `scripts/simulation/stage4_c_coverage.py` (new/updated) | Tallies exhaustive, ISS architectural, and RTL event evidence independently; prints each error with expected/actual | Saved full simulation output, manifests, traces, sidecars, units, and companion report | Zero `coverage_errors`; simulator-specific coverage PASS marker |
| `scripts/simulation/run_stage4_mutation.py` (new/updated) | Runs isolated Verilator mutants, checks complete DUT traces against independent ISS, supports `--mutants C07,C09`, retains reviewable evidence | Python 3, Verilator 5.x, GNU make, C++ compiler; fresh full baseline | `STAGE4_C_MUTATION_VERILATOR PASS caught=... missed=0 invalid=0 equivalent=0` |
| `.gitattributes` (modified) | Allows verbatim simulator-generated whitespace in retained Stage 4 raw mutation artifacts; follows the existing Stage 3 mutation evidence rule | Git attributes | Keeps raw log bytes intact while other staged files remain covered by `git diff --cached --check` |

## Documentation files

| File | Purpose |
|---|---|
| `README.md` (modified) | Current ISA scope, status, commands, results, and limitations |
| `PROJECT_PLAN.md` (modified) | Stage 4 gate state and separate simulator/mutation evidence |
| `documentation/architecture/stage4_4_pipeline.md` (modified) | Fetch, length, retirement, fault, timing, and regression contract |
| `documentation/architecture/stage4_c_coverage_mutation.md` (new/updated) | Fixed dictionary, evidence provenance, mutation rules/results, limitations |
| `documentation/architecture/microarchitecture.md` (modified) | Implemented RV32IMC pipeline status and excluded target features |
| `documentation/verification/README.md` (modified) | Canonical regression/coverage/mutation entry points |
| `documentation/verification/verification_architecture.md` (modified) | Independent ISS, RTL coverage sources, and validation flow |
| `documentation/verification/stage4_coverage_manifest.md` (new) | This file-level purpose/dependency/command/marker manifest |
| `IMPLEMENTATION_LOG.md`, `STAGE_CHANGELOG.md` (modified) | Chronological approvals, findings, actual reports, and limitations |

## Reports retained

| Evidence | Files | Recorded result |
|---|---|---|
| Stage 4.2 decompressor history | `reports/stage4_2_decompressor_xsim_owner.txt`, `reports/stage4_2_decompressor_verilator_owner.txt`, detailed accepted XSim/Verilator reports, and `reports/stage4_2_decompressor_xsim_false_pass_20261108.txt` | Accepted reports remain separate; contradictory early transcript is preserved as invalid history |
| Stage 4.3 golden-core history | `reports/stage4_3_golden_xsim_resume_20261108T102530Z.txt`, `reports/stage4_3_golden_verilator_20261108T102658Z.txt` | 209 C-disabled compatibility cases and 12 C-enabled golden-core cases; separate simulator records |
| Historical Stage 4.4, 229 configurations | `reports/stage4_4_pipeline_xsim_20261108T140852Z.txt`, `reports/stage4_4_pipeline_verilator_20261108T143119Z.txt` | Separate prior XSim/Verilator evidence; not replaced by 230-case reports |
| Expanded full regression | `reports/stage4_4_pipeline_xsim_20261108T154108Z.txt`, `reports/stage4_4_pipeline_verilator_20261108T161512Z.txt` | Each: 230 configurations, 460 golden/pipeline-to-ISS comparisons, 230 pipeline-to-golden traces, 7 units; divider 2,027 starts/dones, 66,891 busy cycles, 0 aborts |
| Coverage | `reports/stage4_c_coverage_xsim_20261108T161413Z.txt`, `reports/stage4_c_coverage_verilator_20261108T161707Z.txt` | Each: 65,536 decompressor patterns, all 16 pipeline event bins, zero errors |
| Checker defect history | `reports/stage4_c_coverage_xsim_20261108T160146Z.txt`, `reports/stage4_c_coverage_xsim_reanalysis_20261108T161158Z.txt` | Original one-error report retained; diagnosis explains EBREAK STOP accounting. Corrected execution evidence is the XSim PASS report above. |
| Original mutation campaign | `reports/stage4_c_mutation_verilator_20261108T161754Z.txt` and selected raw records under `reports/stage4_c_mutation_runs/run_20261108T161754Z/` | 8 CAUGHT, 0 MISSED, 2 INVALID. Raw INVALID records remain unchanged. |
| Mutation reanalysis | `reports/stage4_c_mutation_verilator_20261108T161754Z_reanalysis.txt` | Independent saved-trace diagnosis of C07/C09 parser gap |
| Focused mutation rerun | `reports/stage4_c_mutation_verilator_20261108T163835Z.txt` and raw selected records under `reports/stage4_c_mutation_runs/run_20261108T163835Z/` | Fresh full baseline plus C07/C09 only: 2 CAUGHT, 0 MISSED, 0 INVALID. Combined with original eight detections; not one fresh ten-mutant run. |

When preserving raw mutation records, retain source diffs, result JSON,
stdout/stderr, runner/simulator logs, traces, sidecars, ISS references, and
baseline summaries. Exclude generated `.hex` images, vectors, compiler/build
trees, object files, caches, and temporary isolated source workspaces.

## Reproduction commands

Run from Windows CMD at repository root:

```cmd
scripts\simulation\run_stage4_coverage_xsim.bat
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage4_coverage_verilator.sh
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_mutation.py
```

The focused C07/C09 parser-validation run executes a fresh full coverage
baseline, then those two mutants only:

```cmd
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_mutation.py --mutants C07,C09
```

Mutation is Verilator-only; no XSim mutation result is claimed. The evidence
scope is finite and directed. No full architectural compliance, synthesis or
timing-closure, unsupported ISA, or ML result is implied.

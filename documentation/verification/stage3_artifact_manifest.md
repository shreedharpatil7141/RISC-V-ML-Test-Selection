# Stage 3 artifact manifest and reproduction guide

This manifest describes the Stage 3 RV32IM implementation, directed tests,
verification assets, reports, and canonical Stage 3.7 entry points added or
modified relative to the `stage2-complete` baseline. It is a source/evidence
index, not a project archive. Generated binaries, simulator build trees,
`.hex` outputs, caches, and mutation scratch workspaces are excluded.

## Documentation and repository evidence

| Paths | Purpose |
|---|---|
| `README.md`, `PROJECT_PLAN.md` | User-facing implemented scope, exact entry points, current stage status, and future-project separation |
| `IMPLEMENTATION_LOG.md`, `STAGE_CHANGELOG.md` | Append-only work history, separate simulator evidence, gate status, and limits |
| `documentation/architecture/isa_specification.md`, `rtl_modules.md`, `microarchitecture.md`, `README.md` | Distinguish the broader target from implemented RV32I+M, accurately describe existing modules and pipeline behavior, and link Stage 3 evidence |
| `documentation/architecture/stage3_4_divider_schedule.md`, `stage3_5_m_coverage_dictionary.md`, `stage3_6_mutation_plan.md`, `stage3_rv32m_status.md` | Divider cycle/protocol contract; finite bin definitions; mutation plan/M26 scope; Stage 3 implementation, results, and limitations |
| `documentation/verification/verification_architecture.md`, `README.md`, `stage3_artifact_manifest.md` | Implemented regression flow, independent verification sources, exact artifact inventory, tool dependencies, commands, reports, and markers |
| `reports/stage1_regression.txt`, `reports/stage1_mutation_audit/reanalysis_20261107.txt` | Preserved Stage 1 regression/audit evidence; these do not substitute for the Stage 3 reports |
| `reports/stage3_2_xsim.txt`, `reports/stage3_3_regression_{xsim,verilator}.txt`, `reports/stage3_4_regression_{xsim,verilator}.txt`, `reports/stage3_5_coverage_{xsim,verilator}_reanalysis.txt` | Historical Stage 3 milestone evidence, kept separate by simulator and gate |
| `reports/stage3_6_mutation_verilator.txt`, `reports/stage3_6_mutation_m26_adjudication.txt`, `reports/stage3_6_mutation_runs/run_20261107_175902_UTC/` | Raw Verilator mutation results plus separate adjudication; raw M26 `MISSED` record remains unchanged |
| `reports/stage3_7_regression_xsim.txt`, `reports/stage3_7_regression_verilator.txt` | Owner-supplied final consolidated regression reports, kept separate by simulator |
| `.gitattributes` | Preserve whitespace bytes in raw mutation transcripts when reviewing the staged diff; raw captured output is not normalized |

## Implementation and tests

| Paths | Change / purpose | Dependencies and reproduction |
|---|---|---|
| `rtl/alu/rv_md_comb.sv`, `rv_mul.sv`, `rv_div_iter.sv`, `rv_md_exec.sv` | Added golden combinational M model; combinational multiplier; fixed 34-cycle iterative divider; pipeline M wrapper | SystemVerilog; included in `scripts/simulation/stage1_rtl.f` or `stage2_rtl.f` as appropriate |
| `rtl/control_unit/rv_control.sv`, `rtl/core/rv_core_single.sv`, `rtl/core/rv_core_pipe.sv`, `rtl/decoder/rv_decoder.sv` | Add legal M decode/control/writeback and integrate M in both core paths | XSim or Verilator compile lists |
| `rtl/packages/rv_pipe_pkg.sv`, `rtl/pipeline/rv_ex_stage.sv`, `rv_id_stage.sv`, `rv_pipe_regs.sv` | Carry M control, forwarded operands, divider hold/transfer, and fault/redirect handling | Compiled by `stage2_rtl.f` |
| `verification/environment/tb_rv_md.sv`, `tb_rv_decoder_m.sv`, `tb_rv_div_iter.sv`, `tb_rv_md_exec.sv`, `tb_rv_pipe_stage4.sv`; modified `tb_rv_pipe.sv` | Arithmetic, exhaustive M decode, divider, wrapper, and iterative-M pipeline checks | Invoked by the regression runners; result markers listed below |
| `tests/directed/m_extension/manifest.csv` and its 22 named `.s` programs | Golden-core M operations and arithmetic corners (`m_chain`, `m_div*`, `m_mul*`, `m_rem*`, sign matrix, x0, and related cases) | Assembled by preparation scripts. Generated `.hex` images are not source deliverables |
| `tests/directed/pipeline_m/manifest.csv`, `expected_perf.csv`, and eight `.s` programs | Pipeline M dependencies, forwarding, x0, JALR, load-use, wrong-path, and fault cases | Included in the 209-test consolidated suite |
| `tests/directed/pipeline_div/manifest.csv`, `expected_perf.csv`, and eight `.s` programs | Divider sequencing, dependencies, faults, forwarding, wrong-path, and load-use | Included in the consolidated suite |
| `tests/directed/pipeline_div_coverage/manifest.csv`, `expected_perf.csv`, and two `.s` programs | Focused RS1 load-use and divider forwarding-source cases | Included in the consolidated suite |
| `tests/directed/rv32i/manifest.csv` and illegal-encoding `.s` programs | Update RV32I illegal M encoding coverage; one former test was renamed to identify its exact funct7 pattern | Included in the RV32I suite |

The checked-in per-suite manifests are the authoritative test-file lists; the
209-case prepared manifest is generated under each simulator output directory.

## Models and orchestration

| Paths | Purpose | Dependencies |
|---|---|---|
| `scripts/simulation/rv32i_iss.py`, `rv32_asm.py`, `rv32_asm_selftest.py` | Independent Python ISS, assembler, and assembler self-checks; modified for M instructions and source syntax | Python 3 standard library |
| `scripts/simulation/m_model.py`, `m_model_selftest.py`, `gen_m_tests.py`, `iss_validate_stage3.py` | Independent M arithmetic model, self-checks, program generation, and ISS validation | Python 3 standard library |
| `scripts/simulation/prepare_stage3.py`, `prepare_stage4.py`, `prepare_stage5.py`, `stage4_lib.py`, `stage5_coverage.py` | Generate test images, ISS traces/sidecars, expected cycle data; check timing, protocol, pipeline events, and finite M bins | Python 3 standard library |
| `scripts/simulation/check_stage3_results.py`, `check_stage4_results.py`, `check_stage5_results.py` | Stage-specific strict checkers. The Stage 3.7 runner passes `stage3_7` to the shared checker so its report marker identifies the consolidated gate; default `stage3_5` remains for historical calls and mutation harness | Python 3 standard library |
| `scripts/simulation/run_m_stage3.py`, `run_stage3.py`, `run_stage3_xsim.py`, `run_stage3_xsim.bat`, `run_stage4.py`, `run_stage4_xsim.bat`, `run_stage5.py`, `run_stage5_xsim.bat` | Historical Stage 3 implementation-step runners; Stage 3.5 direct defaults and marker remain available to the mutation harness | Python 3; Verilator 5.x/make/C++ for Verilator; Vivado XSim for XSim |
| `scripts/simulation/run_stage3_regression.py`, `run_stage3_regression_xsim.bat` | Canonical Stage 3.7 wrappers with isolated outputs, reports, and `STAGE3_7_REGRESSION_* PASS` markers | Verilator path: Python 3, Verilator 5.x, GNU make, C++ compiler. XSim path: Windows CMD, Python 3 launcher, Vivado `xvlog`/`xelab`/`xsim`, PowerShell |
| `scripts/simulation/run_stage6_mutation.py`, `audit_stage1_mutations.py` | Separate finite mutation audits; they operate on scratch copies and preserve raw evidence | Verilator path requires Verilator 5.x, make, C++ compiler, Python 3; no XSim mutation result exists |
| `scripts/simulation/stage1_rtl.f`, `stage2_rtl.f`, `gen_rv32i_tests.py` | Add M source ordering and illegal-M test cases | Referenced by both simulators and test preparation |

Some Stage 3 runners retain `stage4`/`stage5` in their filenames because they
were named for sequential Stage 3 implementation steps. They do not select
the project's ISA stages 4 or 5. Use the `run_stage3_regression` entry points
for the consolidated Stage 3.7 gate.

## Reproduction commands and expected markers

Run from the repository root. XSim requires Vivado's environment initialized
in Windows CMD and Python 3 available through `py -3`:

```cmd
scripts\simulation\run_stage3_regression_xsim.bat
```

Expected report and marker:

```text
reports\stage3_7_regression_xsim.txt
STAGE3_7_REGRESSION_XSIM PASS
```

Verilator runs in Ubuntu WSL from Windows CMD:

```cmd
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage3_regression.py
```

Expected report and marker:

```text
reports/stage3_7_regression_verilator.txt
STAGE3_7_REGRESSION_VERILATOR PASS
```

The separate, long-running Stage 3.6 campaign command is:

```cmd
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage6_mutation.py
```

Its expected summary marker is `STAGE3_6_MUTATION_AUDIT`; do not rerun it
unless a relevant source or verification change requires new mutation
evidence.

## Preserved evidence and exclusions

The separate Stage 3.7 owner reports are
`reports/stage3_7_regression_xsim.txt` and
`reports/stage3_7_regression_verilator.txt`. Earlier Stage 3.2-3.6 evidence,
including the raw M26 `MISSED` record and its separate scoped adjudication,
remains under `reports/`. Raw campaign records in
`reports/stage3_6_mutation_runs/run_20261107_175902_UTC/` are retained; they
are evidence records, not scratch workspaces.

Do not add simulator output directories (`sim_out*`), generated test `.hex`
files, Verilator `obj_*`/binary trees, Vivado `.Xil`/`xsim.dir` outputs,
Python caches, or the untracked `reports/stage1_mutation_audit/run_*`
workspace tree. Historical Stage 1/2 reports and the `stage2-complete` tag
are preserved. No ZIP, full-project copy, or unchanged-file bundle is part of
this package.

## Stage 3.7 owner results

See `../architecture/stage3_rv32m_status.md` for separate simulator tables,
unit counts, trace/timing/protocol observations, pipeline-event counts,
finite-coverage scope, and limitations. Both local Stage 3.7 reports end in
their simulator-specific PASS marker with 209/209 tests, 108/108 defined M
bins, zero coverage data errors, and system/unit PASS.
The report headings retain the shared checker's historical “Stage 3.5” title;
filenames and gate markers identify the Stage 3.7 results.

Stage 3.9 does not need a fresh XSim run if it changes documentation only or
leaves RTL, testbenches, runners, and checking behavior unchanged. Reuse the
Stage 3.7 owner evidence in that case. Any relevant source or checker change
requires choosing the affected validation and recording new simulator
evidence; do not infer a pass from unchanged reports after code changes.

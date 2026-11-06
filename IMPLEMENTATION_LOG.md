# Implementation Log

Append-only. Record only what was actually done and observed.

## Stage 0 - Project initialization
- Created directory hierarchy per specification.
- Created README, PROJECT_PLAN, .gitignore, and documentation under `documentation/`.
- `.gitkeep` placed in otherwise-empty folders so Git tracks the structure.
- **No RTL, testbench, or dataset exists yet.**
- `RISC_V_ML_Verification.xpr` intentionally NOT created (see `documentation/vivado_setup.md`).
- Compilation: N/A. Simulation: N/A.
- Status: awaiting approval to begin Stage 1.

## Stage 1 - RV32I single-cycle core (2026-11-04) - COMPLETE
Implemented: rv32_pkg, rv_decoder, rv_imm_gen, rv_regfile, rv_alu, rv_branch_cmp, rv_control, rv_lsu, rv_core_single.
Behaviour: ECALL/EBREAK/illegal/misaligned halt the core with halt_cause (no trap CSRs until Stage 7). M/A/C/Zicsr/FENCE.I/MRET deliberately illegal.
Verification results are kept separate per simulator (never merged):
- AMD Vivado 2026.1 XSim (reported by user): unit PASS 114,378 checks / 0 errors; system 101/101 PASS; RTL-vs-ISS trace 101/101 PASS; STAGE1_REGRESSION_XSIM PASS. Assistant cross-check of the 101 uploaded XSim RTL traces vs ISS traces: 101/101 byte-identical.
- Verilator 5.020: earlier run (TB with $urandom) unit 114,402 / 0 errors, system 101/101, mutation 14/14 detected; current repo TB (Xorshift32) unit 114,339 / 0 errors, system 101/101.
- Assembler self-test: 21/21 known encodings.
Findings: mutation exposed a gap (no long branch/JAL offsets) -> 37 long_* tests added. One mutant was equivalent (x0 write hidden by read mask) -> redefined.
Reports: reports/stage1_regression.txt, reports/stage1_mutation.txt (Verilator).

## Stage 1 - XSim compatibility fixes and bring-up (2026-11-04/05)
Issues resolved:
1. XSim failed: `$urandom(seed)` unsupported (`ERROR: [XSIM 43-3122] ... urandom system task is not supported`, tb_rv_units.sv line 69).
2. First XSim system-test run failed because of incorrect XSim command-line invocation; corrected to `xsim <snap> --runall --log <file> --testplusarg "NAME=value"`.
3. x0_behavior verified manually with EXPECT_CAUSE=1, CHECK_GP=1 (manifest entry `x0_behavior,1,1`; manifest has 101 tests, not intentionally modified).
4. Windows file lock: Excel held manifest.csv open; closed.
Files changed: verification/environment/tb_rv_units.sv (Xorshift32 PRNG, seed 32'h00005eed; removed `void'($urandom(seed))`; removed unused `byte unsigned lanes [4]`; test cases preserved), scripts/simulation/run_stage1_xsim.bat (py -3, --runall, --testplusarg, failure tracking, trace-file checks, trace compare, non-zero exit code, summary). RTL unchanged.
Status: Stage 1 accepted by user; used as golden reference.

## Stage 2 - 5-stage pipelined RV32I core (2026-11-05) - COMPLETE (XSim PASS)
Implemented (new files only; Stage 1 RTL/TB/ISS/scripts/tests untouched): rv_pipe_pkg, rv_if_stage, rv_id_stage, rv_ex_stage, rv_mem_stage, rv_wb_stage, rv_pipe_regs, rv_forward_unit, rv_hazard_unit, rv_core_pipe; tb_rv_pipe, tb_rv_pipe_units; gen_pipe_tests.py (63 directed tests), stage2_lib.py (stall/redirect/cycle model), prepare_stage2.py, check_stage2_results.py, run_stage2.py, run_stage2_xsim.bat, mutation_check_stage2.py, stage2_rtl.f.
Design: EX/MEM->EX and MEM/WB->EX forwarding (EX/MEM priority, x0 never forwarded), WB->ID bypass, 1-cycle load-use stall (hold PC + IF/ID, bubble into ID/EX), branches/jumps resolved in EX (predict not-taken, 2-bubble flush of IF/ID and ID/EX), faults carried to MEM (precise halt: older retire, faulting one does not, younger squashed), retirement from MEM/WB only.

Results are separate per simulator (never merged):
- AMD Vivado 2026.1 XSim (user run 2026-11-05 19:17:01, run_stage2_xsim.bat; values read from the console summary the user pasted - the report file reports\stage2_regression_xsim.txt itself was not provided to the assistant): Stage 1 unit TB PASS 114,378 checks / 0 errors; Stage 2 pipe unit TB PASS 624,576 checks / 0 errors; pipeline suite 63/63; rv32i suite 101/101; total 164/164; coverage events 16/16; STAGE2_REGRESSION_XSIM PASS.
- Verilator 5.020 (assistant sandbox): same 164 tests on both cores, 164/164; Stage 1 unit 114,339 / 0 errors; pipe unit 624,576 / 0 errors; coverage 16/16; mutation 20/20 injected pipeline bugs detected (Verilator only, one detected only by the unit TB).
- Mutation testing was NOT run under XSim (mutation_check_stage2.py drives Verilator).

XSim compile/elaboration notes: all RTL and both new testbenches compile and elaborate. Warning XSIM 43-3373 ("$value$plusargs is used as system task") is reported for tb_rv_pipe.sv lines 137-139 and, since Stage 1, for tb_rv_core.sv lines 113-115. It does not change results (see STAGE_CHANGELOG audit). Correction proposed, NOT applied (awaiting user authorization).

## Stage 2 - final documentation and repository audit (2026-11-06)
Scope: documentation/repository review only; no RTL or testbench change; Stage 3 not started.
- Verified against the pasted XSim console summary: all seven required figures match. Not verified: the per-test report file (not provided).
- Stage 1 files (RTL, tb_rv_core, tb_rv_units, run_stage1*, ISS, generator, tests) are byte-identical between the assistant's working tree and the user's uploaded repo; the user's current local repo state is not visible and must be checked with the git commands in the audit report.
- Stage 1 Verilator regression re-run during audit: unit 114,339 / 0 errors, system 101/101 PASS.
- Repository hygiene finding: the uploaded repo snapshot contained sim_out_xsim/ (202 files) and scripts/simulation/__pycache__/; .gitignore updated; `git rm --cached` required (commands in audit report).
Status: Stage 2 awaiting user approval. Stage 3 NOT started.

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

## Stage 1 - RV32I single-cycle core (2026-11-04)
Implemented: rv32_pkg, rv_decoder, rv_imm_gen, rv_regfile, rv_alu, rv_branch_cmp, rv_control, rv_lsu, rv_core_single.
Behaviour: ECALL/EBREAK/illegal/misaligned halt core with halt_cause (no trap CSRs until Stage 7). M/A/C/Zicsr/FENCE.I/MRET deliberately illegal.
Verification (simulator: Verilator 5.020; XSim NOT run):
- Assembler self-test: 21/21 known encodings.
- Unit TB: PASS, 114402 checks, 0 errors.
- System tests: 101/101 pass; RTL retirement trace, final regs and memory identical to independent Python ISS.
- Mutation check: 14/14 injected bugs caught.
Findings: mutation exposed gap (no long branch/JAL offsets) -> 37 long_* tests added. One mutant was equivalent (x0 write hidden by read mask) -> redefined.
Reports: reports/stage1_regression.txt, reports/stage1_mutation.txt.
Open items: run run_stage1_xsim.bat in Vivado (untested); confirm ISA spec versions vs docs.riscv.org; retarget *_stage1 illegal tests when M/CSR/MRET/FENCE.I/C land; no Vivado Tcl script or .xpr yet.
Status: awaiting approval for Stage 2.

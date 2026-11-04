# Stage 1 Verification Summary (RV32I single-cycle core)

## DUT scope
`rv_core_single`: single-cycle RV32I. Legal: all 37 RV32I base instructions + FENCE (NOP) + ECALL + EBREAK.
Everything else (M, A, C, Zicsr, FENCE.I, MRET, WFI) is *deliberately illegal* until its stage.
No trap CSRs yet: ECALL, EBREAK, illegal instruction, misaligned load/store, and misaligned jump/branch target
**halt** the core (`halted=1`, `halt_cause`, `halt_pc`); the faulting instruction does not retire and changes no state.
Halt-cause codes are implementation-defined (see `rv32_pkg::halt_cause_e`), not mcause values.
Branch/jump target alignment is 4 bytes (no C extension yet); a *not-taken* branch with a misaligned target does not fault.

## Verification layers
| Layer | What | Independence |
|---|---|---|
| Unit TB `tb_rv_units.sv` | ALU (10 ops x corners + 2000 random each), branch compare (6 conditions), imm-gen (I/S/B/U/J), regfile (shadow model, x0, read-before/after write), LSU (byte lanes, sign-ext, misalign) | Expected values from separate formulations (wide integer arithmetic, explicit bit placement, byte arrays) |
| System TB `tb_rv_core.sv` | Runs a hex image on the core with a 64 KiB memory; checks halt cause, `gp==1` for self-checking tests, no out-of-range access; dumps retirement trace + final regs + memory | - |
| Directed tests (101) | Self-checking programs, one per instruction group (see below) | Expected values from `gen_rv32i_tests.py` Python models |
| ISS trace compare | Every test's full RTL retirement trace (PC, insn, rd write, store size/addr/data), final x1-x31, final memory 0x4000-0x5FFF, halt cause/PC are diffed against `rv32i_iss.py` | Independent Python decode/execute written from the spec |
| Assembler anchor | `rv32_asm_selftest.py`: 21 hand-known encodings | Known-good encodings |
| Mutation check | `mutation_check.py`: 14 injected RTL bugs, each must make the regression fail | - |

Note: the assembler, generator and ISS are all in-house tools; the ISS was *not* validated against Spike or the official riscv-arch-test suite. No toolchain was available. **No RISC-V compliance claim is made.**

## Test inventory
- `rr_*` (10): every R-type ALU op x 10x10 corner operands + rd/rs aliasing.
- `imm_*` (9): I-type ALU ops x corner operands x immediate corners; shifts x shamt {0,1,7,15,16,31}.
- `upper_lui`, `upper_auipc`.
- `branch_{beq,bne,blt,bge,bltu,bgeu}`: 49 operand pairs each, taken + not-taken; `branch_backward` loops; `branch_notaken_misaligned_ok`.
- `long_beq_*` (13), `long_jal_*` (24): long forward/backward offsets covering high immediate bits (added after mutation check exposed the gap).
- `jumps`: JAL/JALR link values, backward JAL, JALR bit-0 clearing, rd==rs1, rd==x0.
- `loadstore_directed`, `loadstore_random` (400 seeded ops vs Python memory model).
- `regfile`, `x0_behavior`, `fence_nop`.
- Negative (halt-cause expected): `halt_ebreak`, `illegal_*` (17), `misalign_*` (11).
  Some `illegal_*_stage1` tests (M-ext, CSR, MRET, FENCE.I, compressed) encode *Stage-1* behaviour and **must be retargeted when those stages land.**

## Not covered in Stage 1
Pipeline hazards, M/A/C/Zicsr/Zifencei/privileged behaviour, interrupts, memory wait states, reset-in-flight, X-propagation checks, coverage collection, formal checking.

## Tools actually used
Verilator 5.020 (simulation, lint), Python 3.12. **XSim has not been run.** `scripts/simulation/run_stage1_xsim.bat` is written but untested.
Portability notes for XSim: all files carry `` `timescale 1ns/1ps``; TB uses `$value$plusargs`, `$fopen/$fdisplay`, hierarchical reads of `dut.u_rf.regs`, `automatic` locals, `longint` casts - all expected to be supported but unverified.

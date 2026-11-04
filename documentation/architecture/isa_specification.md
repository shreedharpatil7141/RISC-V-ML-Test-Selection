# Target ISA: RV32IMAC + Zicsr + Zifencei + M-mode

## Specification baseline
These are the baseline versions to pin. **They were not verified against docs.riscv.org in Stage 0 (no web access used); confirm and record exact versions at the start of Stage 1.**

| Item | Baseline version |
|---|---|
| RV32I | 2.1 |
| M | 2.0 |
| A | 2.1 |
| C | 2.0 |
| Zicsr | 2.0 |
| Zifencei | 2.0 |
| Privileged architecture | 1.12 (M-mode only) |

Source: https://docs.riscv.org/

## Configuration
- XLEN = 32, single hart (mhartid = 0), in-order.
- `misa`: MXL=1 (32), extensions I, M, A, C. misa treated as read-only (writes ignored) - documented WARL choice.
- Reset PC: parameter, default `0x0000_0000`.
- Memory: unified byte-addressable, little-endian; separate instruction/data ports in the memory model.
- Only machine mode. No S/U modes, no MMU, no PMP, no F/D, no debug mode.

## Instruction set scope
- **RV32I (37 user insts + FENCE):** LUI, AUIPC, JAL, JALR, BEQ/BNE/BLT/BGE/BLTU/BGEU, LB/LH/LW/LBU/LHU, SB/SH/SW, ADDI/SLTI/SLTIU/XORI/ORI/ANDI/SLLI/SRLI/SRAI, ADD/SUB/SLL/SLT/SLTU/XOR/SRL/SRA/OR/AND, FENCE, ECALL, EBREAK. Formats R, I, S, B, U, J.
- **M:** MUL, MULH, MULHSU, MULHU, DIV, DIVU, REM, REMU. Division by zero returns all-ones (DIV/DIVU) or the dividend (REM/REMU), no trap; MIN_INT / -1 gives MIN_INT (DIV) and 0 (REM).
- **A (word):** LR.W, SC.W, AMOSWAP/ADD/XOR/AND/OR/MIN/MAX/MINU/MAXU.W. aq/rl bits decoded; single hart makes them ordering no-ops.
- **C (RV32C):** quadrants 0/1/2 incl. C.ADDI4SPN, C.LW/SW, C.LWSP/SWSP, C.J/JAL/JR/JALR, C.BEQZ/BNEZ, C.LI/LUI/ADDI/ADDI16SP/SLLI/SRLI/SRAI/ANDI, C.MV/ADD/AND/OR/XOR/SUB, C.NOP, C.EBREAK. No floating-point compressed forms (no F/D). Illegal and reserved encodings raise illegal-instruction.
- **Zicsr:** CSRRW/RS/RC and immediate forms, with the spec rules for rs1=x0 / uimm=0 (no write) and rd=x0 (no read side effects for CSRRW).
- **Zifencei:** FENCE.I flushes the pipeline and refetches (instruction-fetch synchronization).
- **Privileged (M-mode):** ECALL, EBREAK, MRET, WFI (implemented as NOP, documented permitted behaviour).

## CSRs
mstatus (MIE, MPIE, MPP=11 fixed), misa, mie, mip, mtvec (direct mode, vectored optional - decide in Stage 7), mepc, mcause, mtval, mscratch, mcycle/mcycleh, minstret/minstreth, mhartid, mvendorid/marchid/mimpid (read-only 0). Unimplemented CSR access -> illegal-instruction; write to read-only CSR -> illegal-instruction.

## Exceptions and interrupts
Instruction address misaligned (cause 0; with C, only possible for 2-byte-misaligned targets from JALR clearing bit 0 rules - documented in Stage 4/7), illegal instruction (2), breakpoint (3), load misaligned (4), store/AMO misaligned (6), ECALL from M (11). Interrupts: MSI (3), MTI (7), MEI (11) via input pins (`mtimecmp` timer itself is outside the core; core receives `mtip`). Access faults are not generated unless the memory model signals them (decision deferred to Stage 7).

## Single-hart memory model and limitations
- Sequentially consistent from the software view (in-order, single hart, blocking memory).
- LR/SC: one reservation (address + valid); cleared by SC (success or fail), by any trap/MRET, and by a store to the reserved word from this hart. SC fails without valid matching reservation.
- AMOs are executed atomically in the memory stage (read-modify-write, no bus interleaving).
- **Not supported:** multi-hart coherence, misaligned atomics (trap), PMA/PMP, cache, virtual memory, Ztso, hypervisor, counters beyond mcycle/minstret, mcountinhibit (maybe Stage 7), debug trigger module.
- Compliance claim: none until RISC-V architectural tests have been run and results recorded.

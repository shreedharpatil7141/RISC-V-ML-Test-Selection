# RTL Module Definitions

All RTL is SystemVerilog (synthesizable subset), compiled into one library `work` by XSim. Package first, then leaf modules, then integration.

| Module | Dir | Responsibility | Stage |
|---|---|---|---|
| `rv32_pkg` | rtl/packages | Types, opcodes, funct codes, ALU/ctrl enums, CSR addresses, cause codes | 1 (extended later) |
| `rv_pc` | rtl/core | Program counter, next-PC mux, redirect | 1 |
| `rv_decoder` | rtl/decoder | 32-bit decode to control + register fields | 1 |
| `rv_imm_gen` | rtl/decoder | I/S/B/U/J immediates | 1 |
| `rv_regfile` | rtl/register_file | 32x32, 2R1W, x0=0 | 1 |
| `rv_alu` | rtl/alu | Arithmetic, logic, shifts, compares, branch compare | 1 |
| `rv_branch_cmp` | rtl/alu | Branch condition compare (added in Stage 1) | 1 |
| `rv_control` | rtl/control_unit | Control signals | 1 |
| `rv_lsu` | rtl/memory | Load/store alignment, byte enables, sign extension, misalign detect | 1 |
| memory ports | (flat ports in `rv_core_single`) | Decision: Stage 1 uses flat ports instead of an SV interface; `rtl/interfaces` is populated in Stage 2 if needed | 1 |
| `rv_core_single` | rtl/core | Non-pipelined integration (golden baseline) | 1 |
| `rv_if_stage` / `rv_id_stage` / `rv_ex_stage` / `rv_mem_stage` / `rv_wb_stage` | rtl/pipeline | Pipeline stages | 2 |
| `rv_pipe_regs` | rtl/pipeline | IF/ID, ID/EX, EX/MEM, MEM/WB | 2 |
| `rv_forward_unit` | rtl/pipeline | EX/MEM/WB bypass | 2 |
| `rv_hazard_unit` | rtl/pipeline | Load-use stall, flush, redirect | 2 |
| `rv_muldiv` | rtl/alu | Multi-cycle mul/div with ready/valid | 3 |
| `rv_rvc_decoder` | rtl/decoder | 16->32 expansion + illegal detect | 4 |
| `rv_fetch_buffer` | rtl/pipeline | Halfword-aligned fetch, 32-bit boundary crossing | 4 |
| `rv_amo_unit` | rtl/atomic | AMO ALU + LR/SC reservation register | 5 |
| `rv_csr_unit` | rtl/csr | CSR file, Zicsr ops, permissions | 6/7 |
| `rv_trap_ctrl` | rtl/csr | Exception/interrupt priority, mepc/mcause/mtval, MRET | 7 |
| `rv_retire_if` (interface) | rtl/interfaces | RVVI-inspired retirement port | 2 |
| `rv_core_top` | rtl/core | Pipelined top | 2+ |

## Retirement port (RVVI-inspired)
valid, trap, pc_rdata, pc_wdata, insn, insn_len (2/4), rd, rd_wdata (gated by rd!=x0), mem_valid/mem_we/mem_addr/mem_wdata/mem_rdata/mem_size, csr_valid/csr_addr/csr_old/csr_new, trap_cause, trap_tval, order (retire counter). Based on concepts of riscv-verification/RVVI; not a copy.

## Compilation order (RTL)
1. `rtl/packages/*`
2. `rtl/interfaces/*`
3. `rtl/alu`, `rtl/register_file`, `rtl/decoder`, `rtl/control_unit`, `rtl/atomic`, `rtl/csr`, `rtl/memory`
4. `rtl/pipeline`
5. `rtl/core`

## Stage 1 status
Implemented and verified under Verilator: `rv32_pkg`, `rv_decoder`, `rv_imm_gen`, `rv_regfile`, `rv_alu`, `rv_branch_cmp`, `rv_control`, `rv_lsu`, `rv_core_single`. `rv_pc` is not a separate module: the PC register and next-PC mux live in `rv_core_single` (to be split during the Stage 2 pipeline refactor). Compile list: `scripts/simulation/stage1_rtl.f`.

# RTL Module Definitions

All RTL is SystemVerilog (synthesizable subset), compiled into one library `work` by XSim. Package first, then leaf modules, then integration.

| Module | Dir | Responsibility | Stage |
|---|---|---|---|
| `rv32_pkg` | rtl/packages | Types, opcodes, funct codes, ALU/control enums, implementation halt causes (no CSR addresses) | 1 (extended later) |
| `rv_decoder` | rtl/decoder | 32-bit decode to control + register fields | 1 |
| `rv_imm_gen` | rtl/decoder | I/S/B/U/J immediates | 1 |
| `rv_regfile` | rtl/register_file | 32x32, 2R1W, x0=0 | 1 |
| `rv_alu` | rtl/alu | Arithmetic, logic, shifts, compares, branch compare | 1 |
| `rv_branch_cmp` | rtl/alu | Branch condition compare (added in Stage 1) | 1 |
| `rv_control` | rtl/control_unit | Control signals | 1 |
| `rv_lsu` | rtl/memory | Load/store alignment, byte enables, sign extension, misalign detect | 1 |
| memory ports | (flat ports in `rv_core_single`) | Flat ports are used; no RTL memory interface module is present | 1 |
| `rv_core_single` | rtl/core | Non-pipelined integration (golden baseline; PC logic is internal) | 1 |
| `rv_if_stage` / `rv_id_stage` / `rv_ex_stage` / `rv_mem_stage` / `rv_wb_stage` | rtl/pipeline | Pipeline stages | 2 |
| `rv_pipe_regs` | rtl/pipeline | IF/ID, ID/EX, EX/MEM, MEM/WB | 2 |
| `rv_forward_unit` | rtl/pipeline | EX/MEM/WB bypass | 2 |
| `rv_hazard_unit` | rtl/pipeline | Load-use stall, flush, redirect | 2 |
| `rv_md_comb` | rtl/alu | Behavioral combinational RV32M reference used by the single-cycle core | 3 |
| `rv_mul` | rtl/alu | Combinational 32x32 multiply and high-half selection | 3 |
| `rv_div_iter` | rtl/alu | Fixed-latency restoring DIV/REM unit with start/ready/done/abort | 3 |
| `rv_md_exec` | rtl/alu | Pipeline M wrapper: combinational multiply plus iterative divider | 3 |
| `rv_rvc_decoder` | rtl/decoder | Planned: 16->32 expansion + illegal detect | 4 (not implemented) |
| `rv_fetch_buffer` | rtl/pipeline | Planned: halfword-aligned fetch, 32-bit boundary crossing | 4 (not implemented) |
| `rv_amo_unit` | rtl/atomic | Planned: AMO ALU + LR/SC reservation register | 5 (not implemented) |
| `rv_csr_unit` | rtl/csr | Planned: CSR file, Zicsr ops, permissions | 6/7 (not implemented) |
| `rv_trap_ctrl` | rtl/csr | Planned: trap/interrupt priority, CSRs, MRET | 7 (not implemented) |
| retirement outputs | flat ports in the cores | Retirement observations are exposed as flat ports; no `rv_retire_if` interface module is present | 2 |
| `rv_core_top` | rtl/core | Planned generic top; current pipeline top is `rv_core_pipe` | 2+ (not implemented) |

## Current retirement observations
The cores expose flat retirement outputs for valid, PC, instruction, destination
register/write data, memory operation, and halt/fault information. There is no
CSR retirement port or `rv_retire_if` interface module in the current RTL. The
broader RVVI-inspired signal list from the original plan is not implemented.

## Compilation order (RTL)
1. `rtl/packages/*`
2. `rtl/interfaces/*`
3. `rtl/alu`, `rtl/register_file`, `rtl/decoder`, `rtl/control_unit`, `rtl/atomic`, `rtl/csr`, `rtl/memory`
4. `rtl/pipeline`
5. `rtl/core`

## Stage 1 status
Implemented and verified (Verilator and XSim): `rv32_pkg`, `rv_decoder`, `rv_imm_gen`, `rv_regfile`, `rv_alu`, `rv_branch_cmp`, `rv_control`, `rv_lsu`, `rv_core_single`. `rv_pc` is not a separate module (PC logic lives in `rv_core_single` and, for Stage 2, in `rv_if_stage`). Compile list: `scripts/simulation/stage1_rtl.f`.

## Stage 2 status
Implemented and verified (separate XSim and Verilator records): `rv_pipe_pkg` (rtl/packages), `rv_if_stage`, `rv_id_stage`, `rv_ex_stage`, `rv_mem_stage`, `rv_wb_stage`, `rv_pipe_regs`, `rv_forward_unit`, `rv_hazard_unit` (rtl/pipeline), and `rv_core_pipe` (rtl/core, top). Reuses Stage 1 leaf modules. The retirement port stays a flat port list; `rtl/interfaces` remains empty. Compile list: `scripts/simulation/stage2_rtl.f`.

## Stage 3 status
The Stage 3.7 owner reports independently record XSim PASS and Verilator PASS
for 209/209 tests, 108/108 finite M bins, and all unit gates. `rv_core_single`
uses `rv_md_comb` as the golden M implementation. `rv_core_pipe` uses
`rv_md_exec`, which selects combinational `rv_mul` or fixed-latency
`rv_div_iter`. The divider schedule and scope are in
`documentation/architecture/stage3_rv32m_status.md` and
`stage3_4_divider_schedule.md`. No `rv_muldiv` module exists. C, A, CSR,
Zifencei, and privileged trap/interrupt blocks in the target table are future
scope descriptions, not current RTL.

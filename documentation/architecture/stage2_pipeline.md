# Stage 2: Five-Stage Pipelined RV32I Core (`rv_core_pipe`)

Golden reference: `rv_core_single` (Stage 1) is unchanged and independently testable. Stage 2 reuses its leaf modules
(`rv_decoder`, `rv_imm_gen`, `rv_control`, `rv_regfile`, `rv_alu`, `rv_branch_cmp`, `rv_lsu`) **without modification**.

## Modules (`rtl/pipeline/`, package `rtl/packages/rv_pipe_pkg.sv`, top `rtl/core/rv_core_pipe.sv`)
| Module | Role |
|---|---|
| `rv_if_stage` | PC register, fetch; priority halted > redirect > stall > pc+4 |
| `rv_id_stage` | decode, immediate, control, register read, WB->ID bypass, `uses_rs1/rs2` |
| `rv_ex_stage` | operand forwarding muxes, ALU, branch compare, branch/jump resolve, fetch-misalign fault |
| `rv_mem_stage` | LSU, data memory port, load/store misalign fault, commit gating |
| `rv_wb_stage` | register write request + retirement port |
| `rv_pipe_regs` | IF/ID, ID/EX, EX/MEM, MEM/WB registers with stall / redirect / kill control |
| `rv_forward_unit` | EX/MEM and MEM/WB forwarding selects (x0 never forwarded; loads never forwarded from EX/MEM) |
| `rv_hazard_unit` | load-use detection (1-cycle stall) |

## Hazard handling
- **EX/MEM -> EX** forwarding (ALU result, or pc+4 for JAL/JALR); **MEM/WB -> EX** forwarding (final write-back data incl. load data); EX/MEM has priority.
- **WB -> ID bypass** (instruction in WB writes the register being read in ID), so `rv_regfile` stays unmodified.
- **Load-use**: if the instruction in ID reads (rs1/rs2 as actually used) the destination (!= x0) of a load in EX: hold PC and IF/ID, bubble into ID/EX. Exactly 1 stall; the consumer then takes the load data through MEM/WB forwarding. Store data and branch operands are forwarded like any other operand.
- **Branches/jumps** resolve in EX, predict-not-taken. A taken branch, JAL or JALR redirects PC and squashes IF/ID and ID/EX: 2 bubbles.
- **Faults** (illegal, ECALL, EBREAK from ID; fetch-misalign from EX; load/store misalign from MEM) travel with the instruction and halt at MEM: older instructions retire (they are in WB), the faulting instruction does not retire and writes nothing, all younger instructions are squashed. Wrong-path faults never fire because wrong-path instructions are squashed before MEM.
- **Retirement** comes only from MEM/WB with `valid`; bubbles carry `valid=0`, so stalls and flushes cannot create duplicate or phantom retirements. Port names/format match Stage 1 (no `ret_pc_next`), so traces are directly comparable.

## Timing model used by the checker
`cycles = instret + 5 + stalls + 2*redirects` (5 = 4 pipeline latency to MEM for the halting instruction + 1 testbench sampling edge). `stalls` and `redirects` are predicted from the ISS trace alone (`stage2_lib.perf_model`).

## Debug/coverage outputs (simulation aids)
`dbg_stall`, `dbg_redirect`, `dbg_events[15:0]` (16 hazard-scenario event strobes), `dbg_assert_fail` (sticky; load-use escaped stall, or x0 forwarded).

## Verification status
XSim regression PASS (user run) and Verilator regression PASS (assistant sandbox), recorded separately in `documentation/verification/stage2_verification.md`. Mutation testing (Verilator only): 20/20 injected pipeline bugs detected.

## Known warnings
XSim reports `[XSIM 43-3373] $value$plusargs is used as system task` for the plusarg handling in `tb_rv_pipe.sv` (lines 137-139; same pattern in Stage 1 `tb_rv_core.sv`). No functional impact observed; a minimal fix is proposed but not applied.

## Limitations
No branch prediction (predict-not-taken, 2-cycle taken penalty); no wait-state memory (combinational-read memories assumed); no trap CSRs (halt on fault, as Stage 1); M/A/C/Zicsr/privileged not yet implemented; hazard coverage is counter-based event coverage only.

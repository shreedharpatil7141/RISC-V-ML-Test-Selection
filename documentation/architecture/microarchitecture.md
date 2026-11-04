# Microarchitecture Plan

- Strategy: build a correct non-pipelined RV32I core first (Stage 1) as a functional baseline, then convert to a 5-stage pipeline (Stage 2) and compare retirement traces.
- Pipeline: IF -> ID -> EX -> MEM -> WB, in-order, single issue.
- Hazards: forwarding from EX/MEM and MEM/WB to EX; load-use 1-cycle stall; branches resolved in EX with 2-cycle flush (predict not-taken; no predictor initially).
- Multiply/divide: multi-cycle unit stalls the pipeline until done (Stage 3).
- Compressed: fetch buffer works on 16-bit units; instruction length determined from bits [1:0]; PC increments by 2 or 4; 32-bit instruction may straddle a word boundary (Stage 4).
- Atomics: executed in MEM stage, with reservation register (Stage 5).
- CSR/traps: CSR access and trap decision at a precise point (commit in MEM/WB) so that younger instructions are flushed and state is architecturally precise (Stage 6/7).
- FENCE.I: flush pipeline and refetch from PC+4 (Stage 6).
- Interrupts: taken at instruction boundary; mepc = PC of the next instruction to retire.
- Design principle: retirement information is the contract between DUT and verification; no scoreboard dependence on internal signals.

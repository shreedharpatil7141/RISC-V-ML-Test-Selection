# Implemented microarchitecture and future target

## Implemented at the Stage 3.8 gate

- RV32I single-cycle core (`rv_core_single`) is the architectural RTL baseline.
- RV32I five-stage pipeline (`rv_core_pipe`) is in-order and single issue:
  IF, ID, EX, MEM, WB. It has EX/MEM and MEM/WB forwarding, a load-use
  interlock, EX-stage redirects, and precise synchronous fault halting.
- RV32M multiplication is combinational in EX. The pipeline uses
  `rv_md_exec` with `rv_mul` and `rv_div_iter`; the golden core uses a
  separate behavioral `rv_md_comb` path.
- DIV/REM are accepted once, latch forwarded operands, iterate for 32 RUN
  cycles, and transfer in FIN. C0-C32 hold PC/IF-ID/ID-EX while EX/MEM gets
  bubbles; C33 transfers the result. This is 34 occupied EX cycles and 33
  added hold cycles per completed operation.
- A synchronous faulting instruction is not retired and younger work is
  killed. This is the current halt behavior, not privileged trap entry.

See `stage3_4_divider_schedule.md` for protocol priorities and the exact
cycle model, and `stage3_rv32m_status.md` for current verification evidence.

## Future project target, not implemented claims

Compressed fetch/decode (C), atomics (A), CSR state and Zicsr, Zifencei,
machine-mode trap vectors, MRET, WFI, and interrupts remain planned scope.
They are not present as verified Stage 3 functionality. The same applies to
memory wait states, asynchronous external kills, multicore coherence, MMU,
PMP, and physical synthesis/timing behavior.

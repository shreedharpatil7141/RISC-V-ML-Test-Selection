# Implemented microarchitecture and future target

## Stage 4.4 pipeline C integration (implementation present; validation pending)

`rv_core_pipe` now has a default-off `ENABLE_C` mode. In that mode IF asks
for the aligned current and next instruction words, selects the addressed
halfword, expands RV32C integer instructions, and joins a 32-bit instruction
that begins at word offset two. The IF/ID through MEM/WB records preserve
original PC, raw bits, canonical expansion, and byte length. Retirement and
precise fetch/data faults retain the original instruction identity. Branch
and jump targets accept halfword alignment; JAL/JALR links use PC plus the
original two- or four-byte length. C-disabled mode keeps the released Stage 3
fixed four-byte fetch and trace behavior.

The independent C assembler/ISS supplies images and architectural traces.
Stage 4.4 adds cycle and divider protocol checks in addition to trace
comparisons. Its eight new pipeline programs cover mixed-width dependencies,
offset-two DIV fetch and consecutive divisions, load-use/stack/JALR forwarding,
links, wrong-path faults, and older-fault suppression. Exact scope and
commands are in [`stage4_4_pipeline.md`](stage4_4_pipeline.md). This is not an
architectural compliance claim; simulator validation remains pending.

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

RV32C integer golden-core support is owner-validated; its pipeline integration
is implemented in Stage 4.4 and awaits the XSim/Verilator gate. Compressed
floating-point and Zc extensions are not implemented. Atomics (A), CSR state
and Zicsr, Zifencei, machine-mode trap vectors, MRET, WFI, and interrupts are
also outside the implemented scope. The same applies to memory wait states,
asynchronous external kills, multicore coherence, MMU, PMP, and physical
synthesis/timing behavior.

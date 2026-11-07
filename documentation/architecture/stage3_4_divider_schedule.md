# Stage 3.4 fixed-latency M execution schedule

This schedule is the contract for the fixed-latency iterative DIV/REM path. The existing single-cycle `rv_core_single` and `rv_md_comb` remain the independent architectural reference. The multiplier remains combinational and occupies one EX cycle.

The Stage 3.3 combinational pipeline milestone remains reproducible through `scripts/simulation/run_stage3.py` or `scripts/simulation/run_stage3_xsim.bat`: `tb_rv_pipe` defaults `USE_ITERATIVE_M=0`, selecting the behavioral `rv_md_comb` path. Stage 3.4 uses the separate `tb_rv_pipe_stage4` with `USE_ITERATIVE_M=1`. Existing Stage 3.3 reports are retained.

## Divider cycle and transfer table

Let C0 be the EX cycle in which a valid DIV/DIVU/REM/REMU is first accepted while the divider is IDLE. Edges are the active clock edges ending each cycle.

| EX cycle | Divider state during cycle | Action at ending edge | Front end / ID/EX | EX/MEM | Busy / done |
|---|---|---|---|---|---|
| C0 | IDLE, start accepted | Latch operation and both forwarded operands once; initialize magnitudes, quotient/remainder state and iteration index; enter RUN | Hold PC, IF/ID and ID/EX | Bubble | busy=1, done=0 |
| C1..C32 | RUN, exactly 32 cycles | One restoring quotient/remainder iteration per edge. Edge C32 completes iteration 32 and enters FIN. | Hold PC, IF/ID and ID/EX | Bubble | busy=1, done=0 |
| C33 | FIN | Present final result and one-cycle done; at this edge transfer the held DIV/REM exactly once into EX/MEM, accept the next ID instruction, and return to IDLE | Release hold; advance normally | One valid divide result | busy=0, done=1 |

Therefore the divide occupies 34 EX cycles total (C0 through C33 inclusive), with 33 added hold/busy cycles (C0 through C32). The cycle model is `cycles = instret + 5 + stalls + 2*redirects + 33*n_div`, where `n_div` counts architecturally executed divide/remainder instructions from the independent ISS trace, including rd=x0.

During C0..C32, IF/ID and PC hold, ID/EX retains the divide, EX/MEM receives a bubble every cycle, and MEM/WB continues to load its normal next value so older instructions drain and retire. Existing load-use stalls remain separate; they resolve before a dependent divide enters EX. Normal forwarding supplies both operands at C0, after which `rv_div_iter` uses only its latched operands.

## Abort and priority rules

- Reset initializes the divider to IDLE and clears all iteration/result-valid state.
- A synchronous abort has priority over start, iteration, and FIN completion. At the next edge it returns to IDLE and suppresses done, so no stale result can transfer.
- The pipeline gates start with `!kill`, where kill includes an older MEM-stage fault and an already halted core. Thus an older fault concurrent with a younger divider's initial EX cycle suppresses the start. Kill also suppresses any completion transfer and clears younger pipeline state.
- A redirect/kill overrides divider hold in the pipeline registers. A wrong-path divider that has not been accepted never starts.
- The multiplier never asserts divider start and transfers its result through the ordinary one-cycle EX path.

## Verification event definitions

- `md_starts`: accepted start pulses.
- `md_dones`: one-cycle FIN completions actually transferred to EX/MEM.
- `busy_cycles`: accepted-start cycle plus the 32 RUN cycles; 33 per normally completed divide.
- `md_aborts_started`: accepted operations later aborted. It is zero for normal completed pipeline tests; wrapper abort tests exercise every offset C0..C33.

The single-cycle core's behavioral `rv_md_comb` is not replaced by, or shared with, the iterative divider algorithm.

# Stage 3 RV32M implementation and evidence

This document records the implemented Stage 3 scope and its owner-reviewed
Stage 3.7 XSim and Verilator evidence. It does not claim full RISC-V
architectural compliance.

## Implemented scope

The implemented processor is a 32-bit, single-hart, in-order core with a
single-cycle reference core and a five-stage IF/ID/EX/MEM/WB pipeline. The
Stage 3 extension is RV32M: `MUL`, `MULH`, `MULHSU`, `MULHU`, `DIV`, `DIVU`,
`REM`, and `REMU`. The pipeline uses EX/MEM and MEM/WB forwarding, load-use
interlocks, branch redirects, and the existing Stage 1/2 RV32I behavior.

Multiplication is combinational. `rv_mul` forms correctly extended 64-bit
products for the signed and unsigned high-half variants and returns the
selected 32-bit result in the ordinary EX path. The behavioral golden core
uses `rv_md_comb`; it does not use the pipeline divider implementation.

Division and remainder use `rv_div_iter`, a radix-2 restoring divider with
latched operands. An accepted operation occupies C0 through C33 inclusive:
the start-accept cycle, 32 restoring iterations, then one FIN/result-transfer
cycle. It therefore has 34 occupied EX cycles and 33 added pipeline hold
cycles. During C0-C32 the PC, IF/ID, and ID/EX hold; EX/MEM receives a bubble;
older work drains through MEM/WB. At C33 the held operation transfers once
and the pipeline resumes. Divide-by-zero and signed overflow are handled
according to the M extension result rules without an arithmetic exception.

The cycle checker uses the ISS retirement trace and the recorded model:

```text
cycles = instret + 5 + stalls + 2*redirects + 33*n_div
```

`n_div` counts architecturally executed DIV/REM instructions, including
operations whose destination is x0. See
[`stage3_4_divider_schedule.md`](stage3_4_divider_schedule.md) for the cycle
table and protocol definitions.

Synchronous faults are precise within the implemented halt model: a faulting
instruction does not retire, its architectural write is suppressed, and
younger pipeline work is killed. Faults are resolved in MEM; they are not
entered through a privileged trap vector. The current integration has no
interrupts, asynchronous external kills, or memory wait states. The fault and
divider-start interaction is covered by the directed pipeline tests and
divider protocol checks.

## Verification sources

- `rv_core_single` plus `rv_md_comb` is the golden RTL core. The iterative
  pipeline has a separate M execution path through `rv_md_exec`.
- `rv32i_iss.py` is an independent Python architectural ISS. It produces
  expected retirement traces and M operand/result sidecars.
- `m_model.py` supplies a separate shift/add and restoring-division model for
  generated/reference arithmetic checks; the M arithmetic testbench also
  uses non-DUT reference calculations.
- `tb_rv_decoder_m.sv` checks the OP/funct7/funct3 M decode space;
  `tb_rv_div_iter.sv` checks exhaustive W=8 and selected W=32 divider cases;
  `tb_rv_md_exec.sv` checks wrapper results, handshakes, and abort positions.
- `check_stage5_results.py`, `stage4_lib.py`, and `stage5_coverage.py` compare
  golden, pipeline, and ISS traces; check timing and divider protocol; validate
  the finite M dictionary; and reject missing or malformed artifacts.

## Stage 3.7 regression evidence

The local owner-supplied reports are retained separately:

- XSim: [`stage3_7_regression_xsim.txt`](../../reports/stage3_7_regression_xsim.txt),
  marker `STAGE3_7_REGRESSION_XSIM PASS`.
- Verilator: [`stage3_7_regression_verilator.txt`](../../reports/stage3_7_regression_verilator.txt),
  marker `STAGE3_7_REGRESSION_VERILATOR PASS`.

The shared checker keeps the historical heading “Stage 3.5 M-extension
coverage regression”; the report filenames and terminal gate markers identify
these runs as Stage 3.7. No Stage 3.5 report was overwritten by the
consolidated entry points.

Both reports show system PASS, unit PASS, 209/209 tests, 108/108 defined M
dictionary bins, zero coverage data errors, and 16/16 pipeline events. The
suite totals are the same in both records:

| Suite | Tests passed |
|---|---:|
| RV32I | 106/106 |
| Existing pipeline | 63/63 |
| Pipeline M | 8/8 |
| Golden M extension | 22/22 |
| Pipeline divider | 8/8 |
| Pipeline divider coverage additions | 2/2 |
| **Total** | **209/209** |

For every system row, both reports mark single-cycle, pipeline, ISS trace,
golden trace, performance-model, and divider-protocol fields `ok`. Unit
results are reported separately because the Stage 1 unit test counts differ
by simulator; neither report's count is substituted for the other.
For the shared `pipe_div_before_fault` row, each report records starts/dones
`1/1`, busy cycles `33`, aborts `0`, and total cycles `42`. The
`pipe_div_forward_sources` row records `2/2`, `66`, `0`, and `81` in both
reports. These are per-test observations, not campaign-wide protocol totals.

| Unit suite | XSim result | Verilator result |
|---|---:|---:|
| Stage 1 | 114,378 checks, 0 errors | 114,339 checks, 0 errors |
| M arithmetic | 1,152 checks, 0 errors | 1,152 checks, 0 errors |
| M decoder | 1,024 checks, 0 errors | 1,024 checks, 0 errors |
| Pipeline units | 624,576 checks, 0 errors | 624,576 checks, 0 errors |
| Divider | W=8: 262,144 checks, 0 errors; W=32: 1,600 checks, 0 errors | W=8: 262,144 checks, 0 errors; W=32: 1,600 checks, 0 errors |
| M wrapper | 49 checks, 0 errors; 34 abort positions | 49 checks, 0 errors; 34 abort positions |

The 16 pipeline-event hit counts are identical in the XSim and Verilator
reports. The reports give per-event hit totals but no aggregate divider
start/done total; protocol values remain per-test in each simulator report.

| Event | Hits in each report |
|---|---:|
| `stall_rs1` | 70 |
| `stall_rs2` | 46 |
| `fwd_a_exmem` | 8,851 |
| `fwd_a_memwb` | 7,908 |
| `fwd_b_exmem` | 11,812 |
| `fwd_b_memwb` | 2,114 |
| `wb_bypass_rs1` | 5,101 |
| `wb_bypass_rs2` | 262 |
| `fwd_a_priority` | 540 |
| `fwd_b_priority` | 3,777 |
| `redirect_branch` | 7,298 |
| `redirect_jal` | 460 |
| `redirect_jalr` | 210 |
| `store_data_fwd` | 314 |
| `branch_operand_fwd` | 7,642 |
| `x0_not_forwarded` | 63 |

These counts describe only the current directed suite and 16 defined events.
The M dictionary is also finite and directed; all defined bins hit is not
full ISA coverage.

## Mutation evidence and scope

The saved Stage 3.6 Verilator campaign has 59 CAUGHT, one scoped EQUIVALENT,
zero unresolved, and zero INVALID outcomes. It has no XSim mutation result.
M26's raw campaign record remains `MISSED`; the separate adjudication
classifies it EQUIVALENT only at the current pipeline integration boundary.
The disconnected abort input is unobservable after an accepted divide under
the current no-wait-state, synchronous-fault pipeline schedule; the wrapper's
abort behavior itself remains tested. See
[`stage3_6_mutation_m26_adjudication.txt`](../../reports/stage3_6_mutation_m26_adjudication.txt)
and the raw campaign report.

Reassess M26 if the design adds interrupts or traps that asynchronously kill
execution, an external kill/flush, memory wait states, delayed older faults,
or any other path that can assert kill after a divide has been accepted and
before FIN transfer.

## Limits and exclusions

- No RISC-V architectural compliance suite has been run; no full compliance
  claim is made.
- No synthesis, FPGA implementation, area, frequency, or timing-closure
  evidence is available. The fixed cycle model is simulation evidence, not a
  physical timing result.
- No XSim mutation campaign was run.
- C, A, Zicsr, Zifencei, and privileged trap/interrupt architecture are not
  implemented or claimed here.
- The broader machine-learning test-selection work has no Stage 3 ML results.

# Stage 3.5 M-extension coverage dictionary

This dictionary is fixed before Stage 3.5 implementation. IDs are stable report keys. Counts are event hits; a test contributes at most one contributor name per bin. Stage 3.5 retains the Stage 3.4 207-test suites unchanged and adds a separate two-test `pipeline_div_coverage` suite, for 209 total. This is finite directed-regression coverage, not full RISC-V coverage.

## Architectural bins (independent ISS evidence; matched against RTL issue side channel)

ISS records each executed M instruction after both source values have been read and the result calculated, but before destination writeback. RTL records the same fields at EX issue: multiply on its one-cycle EX transfer, divide/remainder on the accepted start cycle. The side channel is separate from, and does not alter, the architectural retirement trace. `(pc, insn, rd, rs1, rs2, a, b)` rows must match in order; full architectural traces continue to validate results and retirement.

| ID family | Exact hit condition | Evidence / reachability |
|---|---|---|
| `A.OP.MUL`, `MULH`, `MULHSU`, `MULHU`, `DIV`, `DIVU`, `REM`, `REMU` | One executed ISS M instruction with the named funct3; report count. Each is required. | ISS sidecar; all eight are reachable in checked-in arithmetic tests. RTL issue rows must match. |
| `A.RS1.SIGN.NEG`, `NONNEG`; `A.RS2.SIGN.NEG`, `NONNEG` | Raw 32-bit source interpreted signed; `<0` or `>=0`. | ISS sidecar; required. Zero belongs to NONNEG. |
| `A.RS1.CLASS.ZERO`, `POS_ONE`, `NEG_ONE`, `SMIN`, `SMAX`, `OTHER`; same `RS2` classes | Exact raw value: 0, 1, FFFFFFFF, 80000000, 7FFFFFFF, or none of those. | ISS sidecar; all required. `NEG_ONE` and the separate `UMAX` predicate overlap because FFFFFFFF is both encodings. |
| `A.RS1.CLASS.UMAX`, `A.RS2.CLASS.UMAX` | Raw source equals FFFFFFFF. | ISS sidecar; required; intentionally overlaps `CLASS.NEG_ONE`. |
| `A.ALIAS.RD_EQ_RS1`, `A.ALIAS.RD_EQ_RS2` | Executed M instruction has nonzero rd equal to the named source register. | ISS sidecar; required. Operand values are captured before writeback, so destructive aliases retain the consumed values. |
| `A.RD.X0` | Executed M instruction has rd=x0. | ISS sidecar; required. |
| `A.CORNER.DIV_ZERO_QUOT`, `DIV_ZERO_REM`, `SIGNED_OVERFLOW_QUOT`, `SIGNED_OVERFLOW_REM`, `QUOT_ZERO`, `QUOT_ONE`, `QUOT_NEGATIVE`, `REM_ZERO`, `REM_NEGATIVE` | Operation and operands/result meet the named predicate; quotient bins require nonzero divisor; `REM_ZERO` requires nonzero divisor. `QUOT_NEGATIVE` is a signed DIV result with bit31 set, including overflow. | ISS sidecar; each required and attributed to test names. Signed overflow is MIN_INT/-1. |

## Pipeline bins (RTL evidence; ISS is not used for microarchitectural claims)

| ID family | Exact sampling condition | Evidence / reachability |
|---|---|---|
| `P.ISSUE.<op>`, `P.COMPLETE.<op>`, `P.RETIRE.<op>` for each of the eight operations | Valid M begins EX (accepted start for divide, normal EX for multiply); transfers once to EX/MEM; retires at WB (`ret_valid`). | RTL debug events / retirement port; all required for each operation in the suite. ISS sidecar and full trace provide independent architectural cross-checks. |
| `P.SQUASH.REDIRECT.M`, `P.SQUASH.FAULT.M` | M in IF/ID is discarded by redirect or older fault; additionally include M in ID/EX discarded by fault. Count each distinct instruction. | RTL pipeline registers/state at the squash edge; required. The tests cover a wrong-path DIV and a fault-suppressed younger DIV. |
| `P.FAULT.DIV_START_SUPPRESSED` | Older MEM fault and valid DIV/REM in ID/EX coincide while divider is ready; start is gated off. | RTL `fault`, ID/EX, and divider-ready event; required. No ISS equivalent. |
| `P.FWD.RS1.EXMEM`, `RS1.MEMWB`, `RS2.EXMEM`, `RS2.MEMWB` | At M issue, actual operand selection uses the named forwarding source. | RTL forward select sampled with issue; required. `pipe_div_forward_sources` was added after source-distance inspection showed the previous directed DIV tests did not deliberately place both source registers at both forwarding distances. |
| `P.LOAD_USE.RS1`, `P.LOAD_USE.RS2` | Load-use interlock holds an M instruction in IF/ID because its named source matches the preceding EX load destination. | RTL hazard/decoder state on the stall cycle; required. An RS1-specific directed test is added because the prior load-use programs place the immediately preceding load in RS2. |
| `P.DIV.CONSECUTIVE` | A new accepted divide/remainder start occurs in the cycle immediately following a prior divider completion. | RTL start/done pulse history; required. |
| `P.DIV.WRONG_PATH_SUPPRESSED` | A redirect discards a DIV/REM before issue; no corresponding issue row exists. | RTL squash event plus absence from issue/ISS sidecars; required. |
| `P.RD.X0` | M instruction with rd=x0 issues and retires. | RTL issue/retirement and ISS sidecar; required. |

## Block-level protocol bins (unit-test evidence only)

| ID family | Exact condition | Evidence / reachability |
|---|---|---|
| `B.ABORT.START_CYCLE` | Abort is asserted with start while IDLE; operation is not accepted and no later done occurs. | `tb_rv_md_exec` marker for offset 0 and passing stale-completion checks; required. |
| `B.ABORT.C01` ... `B.ABORT.C33` | Abort an accepted divide at the named cycle offset from acceptance through FIN; done is suppressed and state returns to IDLE next edge. | `tb_rv_md_exec` per-offset markers and unit PASS; all required. These are block-level only and do not count as pipeline abort coverage. |

## Explicit limits

No operand-pair cross product is required: it would mix many arithmetic predicates and inflate this directed suite without defining a practical closure target. The report lists predicate overlaps and contributors. Pipeline abort bins are not defined: ordinary programs do not inject asynchronous pipeline aborts, while the divider wrapper bench does. “All defined bins hit” describes only this dictionary and must not be reported as full RISC-V coverage.

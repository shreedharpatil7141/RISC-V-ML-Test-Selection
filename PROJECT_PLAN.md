# Project Plan

**Title:** Machine Learning-Based Test Selection for Accelerated Functional Coverage Closure in RISC-V Processor Verification

**Process rule:** one stage at a time; explicit approval required before the next stage. A failing test is debugged before moving on. No fabricated results.

## Stage table
| # | Stage | Main deliverables | Exit criteria |
|---|---|---|---|
| 0 | Initialization | Tree, docs, schemas, roadmap | Docs reviewed and approved |
| 1 | RV32I core (non-pipelined) | `rv32_pkg`, PC, decoder, imm-gen, regfile, ALU, control, memory IF, top, TBs | Every RV32I instruction passes directed self-checking tests; clean XSim compile |
| 2 | 5-stage pipeline | Pipeline regs, forwarding, hazard unit, branch handling, stalls/flushes, retirement port | RV32I tests still pass; RAW/load-use/control-hazard tests pass; retirement trace matches Stage 1 |
| 3 | M extension | MUL/DIV unit | All 8 ops; div-by-zero, signed overflow (MIN/-1) corner cases |
| 4 | C extension | RVC expander/decoder, mixed-length fetch | 16/32-bit mixes, boundary-crossing 32-bit fetch, compressed branches/jumps |
| 5 | A extension | LR/SC, AMOs, reservation | Reservation set/clear/failure semantics; all 9 AMOs |
| 6 | Zicsr + Zifencei | CSR unit, FENCE.I | CSR RW/RS/RC(+I) semantics incl. no-write cases, illegal CSR access |
| 7 | M-mode privileged | Traps, MRET, interrupts, exceptions | Each exception cause and 3 interrupt sources verified |
| 8 | Verification environment | Generator, driver, monitor, ref model, scoreboard, regression, fault injection | Scoreboard catches injected faults; independent ref model agrees with DUT on all tests |
| 9 | Advanced coverage | Bins, crosses, reachability/rarity/saturation analysis | Unreachable bins justified; coverage report generated |
| 10 | Dataset generation | features/coverage/runs/bin_dictionary CSVs | Row alignment validated; diversity analysed; no post-execution features |
| 11 | MATLAB ML | RF, DT, NB; metrics; grouped CV | Metrics and calibration reported on grouped splits |
| 12 | Intelligent selection | Cost-aware selector + baselines | Reproducible comparison vs random, greedy-historical, greedy-oracle (upper bound) |
| 13 | Active learning | Exploit / uncertainty / combined / random-exploration | Cold-start and exploration costs included |
| 14 | Advanced analysis | K-means, cost regression, importance, rare bins, ablations, unseen profiles | Findings documented honestly |
| 15 | Final validation | Docs, report, paper outline, resume text, interview prep | Everything reproducible from scripts |

## Cross-cutting rules
1. UVM prohibited. Features must be XSim-verified before use (e.g. classes, randomize with constraints, covergroups, DPI).
2. Independent reference model: no reuse of DUT execution logic.
3. Grouped train/test splits (group by test profile / generator seed family).
4. Cost: executed-instruction count as proxy, labelled "estimated"; wall-clock recorded separately only if measured.
5. Greedy oracle is an upper bound; offline replay is not claimed as real simulation savings.

## Key risks and mitigations
| Risk | Mitigation |
|---|---|
| XSim covergroup / constrained-random support gaps | Early feature probe in Stage 8; fall back to manual bin counting with CSV export |
| Reference model drifting into DUT logic | Separate package, separate author-style (behavioural ISS) |
| Coverage bins unreachable | Reachability analysis in Stage 9; mark `unreachable` in `bin_dictionary.csv` |
| Dataset too uniform | Multiple generator profiles; diversity metrics in Stage 10 |
| Label leakage | Features computed from the program binary only (static analysis) |
| Pipeline bugs | Keep Stage 1 core as a regression baseline for retirement traces |

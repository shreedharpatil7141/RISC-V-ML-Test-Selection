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
| 4 | C extension | RV32C v2.0 integer encodings, independent compressed model/assembler, decompressor, mixed-length fetch and pipeline integration | Gated 4.0 review through 4.8 release; independent exhaustive 16-bit decode checks, mixed 16/32-bit execution, boundary-crossing fetch, precise retirement/fault and pipeline validation |
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

## Current project status (2026-11-08)

Stages 1 and 2 are the RV32I single-cycle reference and five-stage pipeline.
Stage 3 adds and verifies the M extension in both cores. Stages 3.7, 3.8, and
3.9 are approved complete on `stage3-m-extension`, with separate owner XSim
and Verilator evidence and a reviewed documentation package. This completes
Stage 3 only; it does not complete the wider project or imply architectural
compliance.

| Stage 3 gate | Status | Evidence / deliverable |
|---|---|---|
| 3.2 golden-core M | PASS | `reports/stage3_2_xsim.txt`; 22 M programs and M unit suites |
| 3.3 combinational pipeline M | PASS | Separate XSim and Verilator 177-test reports |
| 3.4 iterative division | PASS | Separate XSim and Verilator 207-test reports; divider unit/protocol checks |
| 3.5 coverage | PASS | Saved-artifact reanalysis reports; final Stage 3.7 reports repeat 209 tests and 108 bins |
| 3.6 mutation audit | PASS, scoped | 59 CAUGHT, 1 EQUIVALENT (M26), 0 unresolved/invalid; Verilator only |
| 3.7 consolidated regression | PASS | Separate XSim and Verilator reports, each 209/209 and all defined bins |
| 3.8 documentation package | Complete | Architecture, verification, status, evidence, limitations, and artifact manifest |

Implemented ISA scope is RV32I plus RV32M. The RV32M multiplier is combinational;
DIV/REM use a fixed 34-cycle accepted operation with pipeline holds. C, A,
Zicsr, Zifencei, and privileged trap/interrupt support remain future scope,
not implementation claims. The top-level README and architecture status doc
give exact exclusions and results.

Stage 4 is active on `stage4-c-extension`, created from `stage3-complete`.
The Stage 4.0 review and plan are recorded in
`documentation/architecture/stage4_0_rv32c_review.md`, pinned to the official
Unprivileged ISA manual release v20260120 (RV32C v2.0). Stage 4.1 software
model/assembler/ISS validation was accepted from the owner report
(`STAGE4_1_SOFTWARE_VALIDATION PASS checks=5 failures=0`); this is software
evidence, not RTL simulation or architectural compliance. Stage 4.2 is limited
to standalone combinational decompressor RTL and unit verification; fetch and
pipeline integration remain gated for later substeps.
`stage2-complete`, `stage3-complete`, historical reports, and local outputs
remain preserved.

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

# Stage 3.6 mutation plan

## Entry criteria and scope

Stage 3.6 is a Verilator-only fault-injection campaign. It first requires new, passing unmutated Stage 1, Stage 2, and Stage 3.5 runs. Saved Stage 3.5 reports are checked as an audit precondition, but are not accepted as the current mutation campaign's baseline. The finite Stage 3.5 dictionary is not full RISC-V coverage.

Every mutation runs in a fresh scratch copy of the source tree. The helper reads the literal mutation tables in the unchanged Stage 1 and Stage 2 mutation scripts, applies those same one-at-a-time substitutions in scratch, then runs the unchanged Stage 1/2 regressions. It separately applies the Stage 3 M mutations below and runs the unchanged full Stage 3.5 Verilator regression. The golden single-cycle core and independent ISS are never mutated with a pipeline DUT mutant. Original project files are read-only inputs to this process.

`CAUGHT` requires successful build outputs, nonzero runner status, and explicit test/unit/coverage failure evidence. `PASS DIFF` in the legacy Stage 1 report is accepted only after recomputing the expected architectural trace with the independent assembler/ISS and confirming a real trace difference. Build/startup failures, missing outputs, and malformed results are `INVALID`. A timeout is `CAUGHT` only if the mutated simulator binary exists, its start is proven by a freshly created incomplete trace, and its completion deadline was exceeded; otherwise it is `INVALID`. A clean full run with a mutant is `MISSED` until investigated. `EQUIVALENT` is reserved for a separately justified proof; no test pass is silently relabeled equivalent.

The helper stores the top-level command, exact child argument arrays, tool version, build artifacts' presence, source replacement, exit status, timeout status, stdout, stderr, full checker report, and named detector per case. Run directories are timestamped and preserved. Timeouts kill the runner's process group. An interruption may leave scratch data in the OS temporary directory, but cannot modify this checkout.

## Stage 3.5 saved evidence and checker correction

The separately saved-artifact reanalysis reports were confirmed before Stage 3.6 work:

| Simulator record | System | Dictionary | Errors | Marker |
|---|---:|---:|---:|---|
| XSim | 209/209 | 108/108 | 0 | `STAGE3_5_REGRESSION_XSIM PASS` |
| Verilator | 209/209 | 108/108 | 0 | `STAGE3_5_REGRESSION_VERILATOR PASS` |

The original failed reports (`reports/stage3_5_coverage_xsim.txt`, `reports/stage3_5_coverage_verilator.txt`) are preserved. The separate reanalysis reports remain the passing evidence. Two independent checker bugs were fixed: (1) ISS trace lookup now follows preparation and the functional checker at `sim_dir/iss/<test>.iss.trace`; (2) result-corner bins now have independent ISS and RTL retirement counts, rather than being rendered from operand-class-only counters. No RTL or threshold was changed. All bins in this finite dictionary being hit is not full RISC-V coverage.

## Stage 3 M mutation inventory

All entries below are individually applied to the named DUT source in a fresh copy. Each expected detector is a pre-existing independent verification check; mutation-specific assertions/tests are not added.

| ID | Intended defect | Expected independent detector |
|---|---|---|
| M01 | MULH returns low product word | Wrapper arithmetic unit (`tb_rv_md_exec`) |
| M02 | MULHSU interprets `rs2` as signed | Wrapper arithmetic unit |
| M03 | MULHU selects a signed high product | Wrapper arithmetic unit |
| M04 | Signed quotient sign correction is disabled | Exhaustive W=8 / W=32 divider model |
| M05 | Unsigned division takes signed divisor magnitude | Exhaustive W=8 / W=32 divider model |
| M06 | Signed remainder sign follows divisor | Exhaustive W=8 / W=32 divider model |
| M07 | Divide-by-zero quotient is zero | Divider corner model |
| M08 | Remainder-by-zero loses dividend | Divider corner model |
| M09 | `MIN_INT / -1` returns the wrong quotient | Divider overflow model |
| M10 | `MIN_INT % -1` returns nonzero | Divider overflow model |
| M11 | Divider completes one iteration early | Divider timing and arithmetic unit |
| M12 | Divider consumes a changing live divisor instead of the latched operand | Divider live-input perturbation and model check |
| M13 | Divide-by-zero remainder fails to retain the original dividend | Divider operand-latch corner check |
| M14 | DIV/REM operation selection is inverted | Exhaustive divider operation/model check |
| M15 | Busy omits the acceptance cycle | Wrapper protocol timing/count checks |
| M16 | Done asserts during RUN rather than FIN | Wrapper one-shot/done timing checks |
| M17 | Abort does not suppress FIN done | Wrapper abort offsets C0..C33 |
| M18 | EX/MEM receives entries while divider busy, causing premature/duplicate transfer | `pipe_div_back_to_back` full trace, cycle, and divider counters |
| M19 | IF/ID advances during divider hold | `pipe_div_dependencies` full trace/performance |
| M20 | ID/EX does not retain the accepted divider instruction | `pipe_div_dependencies` full trace/performance |
| M21 | Divider rs1 ignores EX/MEM forwarding | `pipe_div_forward_sources` trace and ISS operand side channel |
| M22 | Divider rs2 uses the wrong source for MEM/WB forwarding | `pipe_div_forward_sources` trace and ISS operand side channel |
| M23 | Retirement reports a write to x0 | `pipe_m_back_to_back_x0` architectural trace |
| M24 | Forwarding unit forwards an EX/MEM x0 result | x0 assertion, M x0 trace and coverage checks |
| M25 | Older fault no longer squashes younger pipeline work | `pipe_div_fault_illegal` precise-fault trace/protocol checks |
| M26 | Pipeline divider is disconnected from kill/abort | Candidate check: `pipe_div_fault_illegal`; later adjudicated equivalent for currently reachable pipeline states (see mutation report/logs) |

Stage 1's 14 and Stage 2's 20 existing mutant tables are also applied one-at-a-time using their unchanged patterns, with full current regressions and the evidence rules above. The current active source is preflighted for every pattern before a campaign. A missing pattern is recorded `INVALID`; it is never counted as caught.

### M26 reachability adjudication

The saved M26 mutation removes only the EX-stage wrapper connection `.abort(kill)`; it does not change `md_start_req`, the divider's own start-versus-abort priority, or the standalone `rv_md_exec` unit. In the current in-order implementation, any older fault is computed from the instruction already in EX/MEM (MEM stage). If a younger DIV is simultaneously in ID/EX, that MEM fault makes `kill` high in the same cycle, and `md_start_req` includes `!kill`; the divider does not accept the operation. If the older instruction does not fault during that MEM cycle, it advances to MEM/WB and cannot fault later. While a DIV is accepted and unfinished, it holds ID/EX, EX/MEM is bubbled, and younger instructions cannot reach MEM and assert a fault. With no interrupts, external kills, or memory wait states, no `kill` source can arise after acceptance and before FIN transfer. The disconnected abort therefore has no behavior on any currently reachable pipeline execution and is classified `EQUIVALENT` at the pipeline integration boundary only.

This does not prove the divider's abort port unnecessary. The standalone wrapper still requires and tests abort at C0..C33; M26 does not alter that wrapper or its direct unit injection. If traps/interrupts, external flush/kill, memory wait states, or another delayed older exception are introduced, a kill can overlap accepted unfinished work and the pipeline abort connection must be retested. No internal signals were forced and no RTL/test was changed for this adjudication.

## Commands and reports

From Windows CMD at the project root, in a working Ubuntu WSL installation with Python 3 and Verilator:

```cmd
cd /d C:\RISC-V-ML-Test-Selection
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage6_mutation.py
```

The helper first records current Stage 1, Stage 2, and Stage 3.5 baselines. It then audits the unchanged Stage 1 and Stage 2 mutant sets and all 26 Stage 3 M mutants. Main summary: `reports/stage3_6_mutation_verilator.txt`. Per-run evidence: `reports/stage3_6_mutation_runs/run_<UTC>/`, with per-mutant JSON/source-change/stdout/stderr/commands/reports. The host-side static check is:

```cmd
python scripts\simulation\run_stage6_mutation.py --preflight-only
```

That command checks the saved Stage 3.5 markers and source mutation patterns only; it is not a mutation or simulator PASS.

## Evidence boundary

This is mutation evidence for the enumerated source changes and specified tests only. It is Verilator-only. XSim is not run by this helper. No mutation campaign result is established until a current baseline passes and every case has an audited classification. Surviving mutants require investigation; missing tests may be added only after a genuine gap is shown, and verification checks may not be weakened.

# Stage 4 C-extension coverage and mutation plan

**Gate: Stage 4 complete and released.** The dictionary IDs and hit rules were fixed before adding C-specific instrumentation. This is finite directed evidence for the implemented RV32IMC subset, not architectural compliance.

## Evidence classes and stable dictionary

Coverage reports keep three evidence classes separate. `E.*` comes from the exhaustive independent decompressor-vector unit. `A.*` is calculated from the independent software ISS trace and STOP record, never from RTL counters. `P.*` is read from pipeline RTL sidecar events and simulator `COV` counters; ISS data is not used to claim microarchitectural activity.

| ID | Hit rule | Evidence / closure rule |
|---|---|---|
| `E.C.HALFWORD.65536` | Exactly one decompressor unit PASS with 65,536 checked input patterns and zero mismatches. | Unit report/vector checker; required. Length classification, decompression status, HINT/illegal, and expansion are checked by that exhaustive unit, not inferred from system execution. |
| `A.C.FAMILY.<name>` | At least one observed 16-bit encoding in each supported integer family: `ADDI4SPN`, `LW`, `SW`, `NOP`, `ADDI`, `JAL`, `LI`, `ADDI16SP`, `LUI`, `SRLI`, `SRAI`, `ANDI`, `SUB`, `XOR`, `OR`, `AND`, `J`, `BEQZ`, `BNEZ`, `SLLI`, `LWSP`, `JR`, `MV`, `EBREAK`, `JALR`, `ADD`, `SWSP`. | Retired families are independently classified from raw ISS halfword fields. `C.EBREAK` is intentionally faulting, so its family bin comes from the independent ISS STOP record only when raw=`0x9002`, length=2, cause=2; this does not count it as retired. The matching DUT fault identity is checked against the sidecar. |
| `A.C.HINT.RETIRED`, `A.C.NOP.RETIRED` | At least one architecturally retired HINT and canonical C.NOP, respectively. | Raw ISS trace; HINTs retire as NOP effects. HINT and NOP are separate bins. |
| `A.C.ILLEGAL.FAULT`, `A.C.UNSUPPORTED_LENGTH.FAULT` | ISS STOP names a compressed illegal encoding, or a prefix requiring instruction length above 32 bits. | Independent ISS STOP raw bits, length, PC, and cause. A faulting instruction is never counted retired. Required for the existing malformed/prefix cases. |
| `A.PC.OFFSET.0`, `A.PC.OFFSET.2` | Retired/faulting instruction begins at the named `PC mod 4`. | ISS records; both required. |
| `A.C.IMM.SIGNED6.MIN`, `A.C.IMM.SIGNED6.MAX`, `A.C.IMM.SHIFT.MAX`, `A.C.IMM.MEM.MAX`, `A.C.IMM.STACK.MAX` | A retired encoding reaches the signed six-bit limits -32/+31, shift amount 31, word offset 124, and stack offset 252. | Raw ISS instruction fields; required. |
| `A.C.REG.PRIME.LOW`, `A.C.REG.PRIME.HIGH`, `A.C.REG.X0.HINT`, `A.C.REG.SP` | A retired C operation uses x8, x15, a legal x0 HINT, or the implicit stack pointer x2. | Raw/canonical ISS records; required. |
| `A.WIDTH.16_TO_32`, `A.WIDTH.32_TO_16` | Adjacent retired records have the named length transition and sequential PC relation. | ISS records; report branch/jump discontinuities separately and do not count as sequential transitions. |
| `A.FETCH.CROSS_WORD` | Retired 32-bit instruction begins at `PC mod 4 == 2`. | ISS records; required. |
| `A.LINK.COMPRESSED_PC_PLUS_2`, `A.LINK.STANDARD_PC_PLUS_4` | A retired JAL/JALR writes the independently expected link value based on raw instruction length. | ISS PC/raw/length/rd-value; required separately. |
| `A.FAULT.PRECISE`, `A.FAULT.NO_RETIRE` | A non-retiring ISS STOP has the same original fault PC/raw/length and no `I` record at that PC. | ISS trace. Cause-specific access, illegal, and breakpoint results remain in the report. |
| `P.ATTEMPTED`, `P.RETIRED`, `P.FAULTING`, `P.SQUASH.REDIRECT`, `P.SQUASH.FAULT` | A distinct original `(PC, raw, length)` appears in the corresponding pipeline sidecar event. | RTL TB samples the pipeline registers/retirement/fault controls. Repeated stalls are deduplicated by identity. All five lifecycle bins must be nonzero; attempted, retired, faulting, and squashed remain separate sets and may not be conflated. |
| `P.DIV.HALFWORD`, `P.DIV.METADATA_HOLD` | An RTL DIV/REM issue occurs at `PC mod 4 == 2`; a busy-hold stream preserves identical `(PC, raw, length)` through all observed hold cycles for that operation. | RTL sidecar plus exact simulator divider protocol counters. Both bins required in the current directed suite. |
| `P.PIPE_EVENT.00` ... `P.PIPE_EVENT.15` | The correspondingly numbered existing pipeline event counter is nonzero. | Actual RTL `COV` record, summarized separately per simulator. All 16 required; definitions remain the Stage 3 pipeline event contract. |

`ATTEMPTED` means present in IF/ID, not merely read from memory. A branch/fault squash is a separate RTL record. The ISS is in-order and does not report wrong-path speculative fetches, so no ISS bin is fabricated for squashed instructions. The 16 legacy pipeline-event counters remain independent of the C-specific sidecar. Exhaustive encodings that cannot legally retire are represented by `E.*` and the precise fault bins, not by inventing architectural instruction executions.

The fixed directed suite has 12 golden-core C sources plus 9 pipeline C sources. The added `coverage_boundaries` case specifically closes the previously absent x15/high-prime-register and immediate-boundary evidence. If a required family/bin proves unreachable or a test does not produce its evidence, report it as a gap; add a directed source only for a demonstrated gap. Do not change the ISA scope or silently waive a required bin.

## Mutation rules and proposed matrix

Each mutant changes one DUT implementation source in a fresh isolated project copy. The golden single-cycle core, Python assembler/ISS, coverage dictionary/checker, and regression tests remain unchanged. Baseline coverage/regression must pass first. A mutant is `CAUGHT` only after successful build, proof the simulator started, and an explicit independent named checker/trace/coverage failure. Build, launch, malformed report, or timeout without startup proof is `INVALID`; a clean full regression is `MISSED` pending analysis. `EQUIVALENT` requires a written scope proof and is never inferred from a passing run.

| ID | Single injected defect | Expected independent detector |
|---|---|---|
| C01 | C.ADDI16SP immediate bit permutation | Exhaustive decompressor unit exact expansion mismatch |
| C02 | C.ADDI4SPN zero immediate accepted | Exhaustive unit legality mismatch |
| C03 | HINT is marked illegal | Exhaustive unit status/HINT mismatch |
| C04 | Compressed-vs-long length prefix classification inverted | Exhaustive unit length mismatch |
| C05 | C-enabled sequential PC stride forced to +4 | ISS-vs-golden/pipeline C trace comparison |
| C06 | Compressed JAL/JALR link uses PC+4 | Independent ISS trace comparison |
| C07 | Offset-two 32-bit word concatenation halves swapped | Cross-word golden/ISS and pipeline/ISS traces |
| C08 | Divider busy hold fails to preserve raw/length metadata | Halfword DIV trace/retirement comparison plus protocol/timing |
| C09 | Redirect flush retains wrong-path instruction | Wrong-path architectural trace/retirement and squash-sidecar checks |
| C10 | Faulting memory operation commits despite a detected fault | Precise-fault ISS trace, no-retire and memory/register checks |

The campaign is Verilator-only. It creates a passing unmutated coverage baseline, applies each mutation to a fresh isolated copy, preserves command/stdout/stderr/source diff/build/reference and checker evidence, and emits `CAUGHT`, `MISSED`, `INVALID`, or separately adjudicated `EQUIVALENT` for every ID. It does not reuse the invoking checkout as scratch. No XSim mutation result is claimed. C01-C04 run only the independent exhaustive decompressor unit, so a mutated shared decompressor is not used by a golden-core oracle. C05-C10 run the C-only 21-case batch against unchanged golden RTL and independent ISS. The detector compares structurally complete DUT traces directly with the ISS reference even when the normal regression stops at a failing terminal cause check.

## Commands, reports, limits

Full XSim coverage/regression from Windows CMD:

```cmd
cd /d C:\RISC-V-ML-Test-Selection
scripts\simulation\run_stage4_coverage_xsim.bat
```

Full Verilator coverage/regression from Windows CMD through Ubuntu WSL:

```cmd
cd /d C:\RISC-V-ML-Test-Selection
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage4_coverage_verilator.sh
```

Explicit Verilator mutation campaign:

```cmd
cd /d C:\RISC-V-ML-Test-Selection
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_mutation.py
```

Coverage reports are separate at `reports/stage4_c_coverage_xsim_<UTC>.txt` and `reports/stage4_c_coverage_verilator_<UTC>.txt`; each full run contains 209 legacy and 21 C cases (230 total), with 460 golden/pipeline-to-ISS and 230 pipeline-to-golden comparisons. Raw run outputs remain in fresh `sim_out_stage4_4_<sim>_<UTC>` directories. Mutation summary is `reports/stage4_c_mutation_verilator_<UTC>.txt`, with isolated raw records under `reports/stage4_c_mutation_runs/run_<UTC>/`. Dependencies: Python 3; Vivado XSim 2026.1 for XSim; WSL Ubuntu, Verilator 5.x, GNU make and C++ compiler for Verilator/mutation.

## Validated results and reanalysis

Separate coverage reports are `reports/stage4_c_coverage_xsim_20261108T161413Z.txt` and `reports/stage4_c_coverage_verilator_20261108T161707Z.txt`. Each records 230 configurations, 460 golden/pipeline-to-ISS comparisons, 230 pipeline-to-golden traces, seven units, 65,536 decompressor patterns, all 16 pipeline events, and zero coverage errors. Divider evidence in each includes 2,027 starts/dones, 66,891 busy cycles, and zero aborts. The original XSim checker report with one false missing EBREAK-family bin (`...160146Z.txt`) remains preserved; its corrected checker rerun reports the EBREAK family from STOP evidence (`...161413Z.txt`).

The original Verilator mutation report `reports/stage4_c_mutation_verilator_20261108T161754Z.txt` records 8 CAUGHT, 0 MISSED, and 2 INVALID because the detector did not compare traces after a failing terminal marker. Saved-trace reanalysis is `reports/stage4_c_mutation_verilator_20261108T161754Z_reanalysis.txt`; it independently identifies C07 and C09 as complete DUT/ISS trace mismatches. A fresh focused run with a full baseline and only C07/C09 is `reports/stage4_c_mutation_verilator_20261108T163835Z.txt` and records 2 CAUGHT, 0 MISSED, 0 INVALID. Combined evidence covers ten detections across two executions; it is not one fresh ten-mutant rerun. Original INVALID records remain unchanged. The focused runner command is:

```cmd
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_mutation.py --mutants C07,C09
```

The finite bins do not imply full RV32C/RV32IMC compliance. Floating-point and Zc extensions, A, CSR, privileged state/traps, interrupts, synthesis/timing closure, and ML results are outside scope. Unreachable bins must be identified with a scope reason and remain visible rather than being counted as hits.

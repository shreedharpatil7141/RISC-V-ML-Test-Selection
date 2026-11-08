# Stage 5.0 — RV32A specification review and software/planning batch

**Status:** Stage 5 implementation and validation passed on `stage5-a-extension`; final release approval is pending. No merge or `stage5-complete` tag has been made. The software/planning checkpoint is `603b1a07b05a9e8e55bae811634e1cdc16baa16d`; baseline is `stage4-complete` at `4a418f1eb94ae2ba6d59b03e0043c438844ed8f8`.

## Pinned specification and scope

Use the RISC-V International ratified Unprivileged ISA release **v20260120**. Its A extension is **A v2.1**, composed of Zaamo and Zalrsc. RVWMO is **v2.0**. The privileged specification is also v20260120 and is cited only for architectural exception names/codes; this project does not implement privileged trap entry.

- [Unprivileged ISA v20260120, A extension v2.1](https://docs.riscv.org/reference/isa/v20260120/unpriv/a-st-ext.html)
- [Unprivileged ISA v20260120, RV32I v2.1](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)
- [Unprivileged ISA v20260120, RVWMO v2.0](https://docs.riscv.org/reference/isa/v20260120/unpriv/rvwmo.html)
- [Privileged ISA v20260120, machine exception codes](https://docs.riscv.org/reference/isa/v20260120/priv/machine.html)
- [RISC-V ratified specifications version index](https://docs.riscv.org/reference/isa/v20260120/index.html)

The software target is RV32I + M + the **word-only integer A subset** listed below. C remains an independent explicit mode. `rv32ima` means A enabled/C disabled; `rv32imac` means both enabled. Existing `rv32im`/`rv32imc` modes keep A disabled. Stage 4 images, traces, scripts, and behavior remain the compatibility baseline.

Included: `LR.W`, `SC.W`, and the nine word AMOs `AMOSWAP.W`, `AMOADD.W`, `AMOXOR.W`, `AMOAND.W`, `AMOOR.W`, `AMOMIN.W`, `AMOMAX.W`, `AMOMINU.W`, and `AMOMAXU.W`.

Excluded: RV64 `.D` atomics; Zabha `.B/.H`; Zacas; Zawrs; cache-block atomics; floating-point, vector, transactional, privileged, and custom atomic extensions. No multi-hart, coherence, RVWMO litmus, I/O-domain, synthesis, or compliance claim follows from this software batch.

## Encoding and legality

Every included instruction is 32 bits, opcode `0101111` (`0x2f`) and `funct3=010` (`.W`). Fields are `funct5[31:27] aq[26] rl[25] rs2[24:20] rs1[19:15] funct3[14:12] rd[11:7] opcode[6:0]`.

| funct5 | Instruction | RV32 rule |
|---|---|---|
| `00010` | `LR.W` | `rs2` must be `x0`; reads the word at `rs1`, writes it to `rd`, and establishes a reservation |
| `00011` | `SC.W` | `rs1` address, `rs2` store data, `rd` receives zero on success or nonzero on failure |
| `00001` | `AMOSWAP.W` | writes `rs2`, returns old memory word in `rd` |
| `00000` | `AMOADD.W` | 32-bit modular addition |
| `00100` | `AMOXOR.W` | bitwise XOR |
| `01100` | `AMOAND.W` | bitwise AND |
| `01000` | `AMOOR.W` | bitwise OR |
| `10000` | `AMOMIN.W` | signed two's-complement minimum |
| `10100` | `AMOMAX.W` | signed two's-complement maximum |
| `11000` | `AMOMINU.W` | unsigned minimum |
| `11100` | `AMOMAXU.W` | unsigned maximum |

All four `aq/rl` combinations are legal encoding values. `aq=1` is acquire and `rl=1` is release for the accessed memory/I/O domain; both together are RCsc. The project executes one in-order hart with blocking memory and has no observers or I/O domain, so these bits are retained and checked in the encoding/atomic sidecar but introduce no externally observable reordering model. This does not validate RVWMO across harts. The specification advises software not to use LR.rl without LR.aq or SC.aq without SC.rl; those encodings remain legal and are not reclassified as illegal.

Legality rules: any supported `funct5` with `funct3 != 010` is rejected; unsupported `funct5` values are rejected; `LR.W` with nonzero `rs2` is rejected. `SC.W` and AMOs accept any integer register fields. `aq/rl` do not affect legality. `.D`, `.B`, `.H`, offsets, and aliases are not accepted by the explicit assembler syntax. A disabled decoder rejects all opcode `0x2f` instructions as illegal. Source and destination register overlap is legal: all source/address values are sampled from the pre-instruction register state, and only then is `rd` written (with normal `x0` discard).

## Required behavior, project policy, and precise faults

Required instruction behavior: LR reads one naturally aligned 32-bit word and writes its value to `rd`; SC writes only on success and writes zero/nonzero status to `rd`; each AMO atomically reads the old word, computes the selected operation, writes the new word, and returns the old word in `rd`. Signed comparison applies only to MIN/MAX; all values/results are XLEN-wide in RV32. A misaligned LR/SC/AMO raises an exception; an inaccessible address raises a corresponding access fault. Faulting operations must not retire, write `rd`, alter memory, or publish a completed atomic sidecar row. A failed but valid SC returns nonzero and has no memory-write operation. An SC must pass memory permission checks before it may retire.

Project policy for this finite single-hart model:

- Reservation granule is exactly the naturally aligned four-byte word containing the LR address. One valid bit and one word address represent the hart's reservation. A successful LR replaces any prior reservation.
- An SC pairs only with the most recent LR. It succeeds deterministically only when its aligned word address matches the valid reservation and the memory access is permitted; success writes `rs2` and `rd=0`. A valid-access mismatch returns `rd=1`, has no memory side effect, and still consumes the reservation. This deterministic policy is convenient for directed software checks; it does not claim the specification's constrained-loop eventual-success property.
- Every completed SC attempt consumes the reservation. An ordinary committed store or AMO whose written byte range overlaps the reserved four-byte word clears it. Reset clears it. Future trap entry/return integration must clear it per the existing project policy. Current precise faults stop the test core and do not implement trap entry; a fault must never allow a younger atomic to act.
- There is one hart and no external/device writer in the present model. No external invalidation input exists. A future memory interface must report writes from other agents that touch the reserved word, or explicitly limit its platform contract. The four-byte granule and exact address match are project policy, not a claim about the only allowed architectural reservation-set shape.
- Misalignment is checked before bounds/access in the software model, matching the existing project memory-fault priority. The ISA permits implementation/environment-specific choice between misalignment and access fault for certain cases. Project halt cause IDs are internal legacy model IDs; they are not architectural `mcause` values. In particular, the existing internal store-misalignment/access IDs map to architectural Store/AMO causes 6/7, not their internal numeric values.
- The existing project rule that same-word ordinary stores invalidate reservations is retained. It is a conservative implementation choice; the architectural atomicity rules do not require a matching SC to succeed after every possible intervening same-hart store.

## Reservation and retirement contract

The independent ISS uses pre-instruction `rs1/rs2`, applies effects only after alignment/access checks, and records a sidecar row only for a completed/retired atomic operation. The `I` trace continues to carry original PC/raw instruction/length and the prior Stage 4 fields. A-enabled mode is tagged `TRACE_V3`; its companion `<test>.iss.a.tsv` contains the atomic opcode, aq/rl, source/destination registers, effective address, old/source/new values, SC status, and reservation before/after. A fault is represented by the existing `STOP` raw-instruction record and halt cause, with no atomic retirement row. A-disabled Stage 4 output remains byte-for-byte in its Stage 4 schema.

The pipeline does not start atomic effects until the instruction reaches its valid, fault-free MEM commit slot. Redirect/fault flushes kill younger instructions. Faults suppress the register write, memory write, retirement, and reservation change. Reservation belongs to the core/hart state in MEM, not a speculative stage. Divider holds insert an EX/MEM bubble while older MEM state advances once, preventing duplicate atomic transactions.

## Existing memory and pipeline constraints

### Implemented atomic MEM contract

Both core interfaces expose `dmem_atomic_commit`. In the pipeline it is asserted only for a valid, fault-free A operation at MEM; in the golden core it marks the committed single-cycle A instruction. The existing no-wait-state interface provides the pre-edge old word on `dmem_rdata`. At the active memory edge, AMOs and successful SC use `dmem_we=4'b1111` and `dmem_wdata` to perform exactly one word update. LR and failed SC have no write strobes. LR/AMOs write the old word to rd; SC writes zero/nonzero status. Alignment/access faults suppress the transaction and reservation update.

Fault-free qualification gates the read request and commit. This is atomic for the project's single hart and no-concurrent-writer memory model: no other observer can interleave between the combinational read and synchronous edge write. It is not a general bus protocol or multi-hart guarantee. `aq/rl` are accepted and retained; no cross-hart ordering behavior is modeled.

Pipeline requirements: `rs1` is an address source for all A operations; `rs2` is a data source for SC/AMO but not LR; every A instruction has an `rd` result, including SC status. Forward both sources using the existing bypass network, retain load-use interlocks, and forward the AMO old value/SC result after completion. Freeze younger stages while an atomic transaction is outstanding. Existing divider protocol/holds must remain independent. Carry Stage 4 original instruction metadata through the atomic hold, and verify redirect/fault flushes cannot issue speculative requests.

## Software implementation and independent validation

Software additions are `rv32a_model.py`, explicit A encodings, A-enabled ISS, A software programs, a C-enabled AMO at PC offset two, and pipeline interaction/fault programs. The assembler and ISS decoder do not call each other. The software gate passed 14 encoding anchors, 2,048 legality combinations, 36 arithmetic pairs, 13 directed ISS checks, and exact 230-case Stage 4 compatibility. RTL traces and atomic sidecars are compared separately against ISS and golden-core evidence.

Keep the existing names `run_stage5.py`, `run_stage5_xsim.bat`, `prepare_stage5.py`, and `stage5_coverage.py`: these are historical Stage 3.5 M-extension regression/coverage entry points, not Stage 5 A-extension runners. This batch adds `validate_stage5_a.py` and does not repurpose historical scripts or reports.

Windows CMD commands from repo root:

```cmd
py -3 scripts\simulation\validate_stage5_a.py --stage4-dir sim_out_stage4_4_xsim_20261108T154108Z
```

Preparation only (use a fresh output directory): `scripts\simulation\prepare_stage5_a.bat sim_out_stage5_a_prepare_OWNER1`.
Full Verilator from Windows CMD via Ubuntu WSL: `wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage5_a_verilator.sh`.
Full XSim in initialized Vivado CMD: `scripts\simulation\run_stage5_a_xsim.bat`.
Focused Verilator mutants, only after source-matched XSim and Verilator full-suite PASS reports: `wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage5_a_mutation.py`. For A01/A02 only: append `--mutants A01,A02`.

Expected separate reports: `reports/stage5_a_pipeline_verilator_<UTC>.txt`, `reports/stage5_a_pipeline_xsim_<UTC>.txt`, and `reports/stage5_a_mutation_verilator_<UTC>.txt`. The full functional suite is 209 legacy + 21 Stage 4 C + 18 A/C+A = 248 tests, with 496 golden/pipeline-to-ISS trace comparisons and 248 pipeline-to-golden comparisons. It includes eight unit suites, a 2,048-combination RTL legality sweep, atomic operation/status/aqrl coverage, and actual 16 pipeline event counters. Outputs are fresh-only; no automatic resume is supported.

The software gate passed all five groups; the owner-recorded marker was `STAGE5_A_SOFTWARE_VALIDATION PASS groups=5 failures=0 stage4_cases=230`. Compatibility used the preserved Stage 4 output directory and checked 230 images/results/traces. XSim PASS evidence is `reports/stage5_a_pipeline_xsim_20261108T195247Z.txt`; Verilator PASS evidence includes `reports/stage5_a_pipeline_verilator_20261108T194647Z.txt` and later fresh PASS reports. Each simulator reports 248 cases (209 legacy, 21 C, 18 A/C+A), 496 ISS comparisons, 248 pipeline-to-golden traces, eight units, 65,536 decompressor patterns, 41 atomic reference events (23 writes), all 11 A operations, both SC statuses, and all four aq/rl combinations. Divider protocol records: 2,029 starts, 2,029 dones, 66,957 busy cycles, zero aborts (XSim report; simulator reports remain separate).

Verilator-only mutation evidence is distributed across runs and reanalysis: the original campaign caught A03–A05 and retained A01/A02 as INVALID; the focused A01/A02 run caught A01 and retained A02 as INVALID; retained A02 logs independently show four LR.W `rs2=1` legality mismatches and the expected `RV32A_UNIT FAIL` `$fatal`, recorded in `reports/stage5_a_mutation_verilator_20261108T204623Z_A02_reanalysis.txt`. Thus there is detection evidence for five mutants across separate runs and reanalysis, not one fresh five-mutant campaign. Original INVALID reports remain unchanged. The updated A02 classifier was not executable in this local environment because Python is unavailable; the saved-evidence reanalysis is distinct from an implementation test.

## Current implementation gate

Implemented scope is RV32I/M/C plus the RV32A word subset: LR.W, SC.W, and nine word AMOs. The design assumes one hart, no wait states, and no concurrent external writer. Results do not establish full architectural compliance, multi-hart/RVWMO behavior, synthesis/timing, unsupported extensions, CSR/privileged behavior, or ML results. The validated Stage 5 checkpoint is awaiting final owner release approval; Stage 6 has not started.

## Original gated follow-on plan

| Substep | Scope | Gate |
|---|---|---|
| 5.0/5.1 | This specification review, assembler/model/ISS support, directed software vectors, and exact 230-case A-disabled compatibility | `validate_stage5_a.py` all five groups pass; software-only |
| 5.2 | Standalone synthesizable atomic decode/result unit plus independent vector/unit checks | All legal/reserved encodings and AMO arithmetic vectors agree with independent literals in XSim and Verilator |
| 5.3 | Golden single-cycle core and atomic memory handshake; precise faults and retirement/sidecar records | Golden RTL vs independent A ISS on all A programs; Stage 4 compatibility preserved |
| 5.4 | Five-stage pipeline atomic transaction/holds, reservation ownership, hazards/forwarding/flush/fault behavior and divider interaction | Full pipeline vs both golden RTL and ISS; atomic protocol counters checked independently |
| 5.5 | A architectural and pipeline coverage dictionary, directed gap closure, mutation suite, C-disabled regression | Separate simulator coverage and Verilator mutation evidence; finite scope reported explicitly |
| 5.6 | Final documentation, report manifest, review, commit/push, owner release | No merge/tag until owner approval |

No RTL, CSR, privileged/trap, multi-hart, coherence, synthesis/timing, or ML work is part of Stage 5.0/5.1.

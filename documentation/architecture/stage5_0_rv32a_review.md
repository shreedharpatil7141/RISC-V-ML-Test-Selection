# Stage 5.0 — RV32A specification review and software/planning batch

**Status:** Stage 5 software/planning changes are implemented and awaiting the combined software validation gate. No RTL has changed. The release baseline is `stage4-complete` at Stage 4 commit `4a418f1eb94ae2ba6d59b03e0043c438844ed8f8`.

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

## Reservation and retirement contract for future RTL

The independent ISS uses pre-instruction `rs1/rs2`, applies effects only after alignment/access checks, and records a sidecar row only for a completed/retired atomic operation. The `I` trace continues to carry original PC/raw instruction/length and the prior Stage 4 fields. A-enabled mode is tagged `TRACE_V3`; its companion `<test>.iss.a.tsv` contains the atomic opcode, aq/rl, source/destination registers, effective address, old/source/new values, SC status, and reservation before/after. A fault is represented by the existing `STOP` raw-instruction record and halt cause, with no atomic retirement row. A-disabled Stage 4 output remains byte-for-byte in its Stage 4 schema.

Future pipeline implementation must not start atomic side effects before the operation reaches the oldest commit-authorized MEM position. Redirect/fault flushes kill younger requests. The atomic result is written only after the memory transaction succeeds; faulting operations suppress register write, memory write, retirement, and younger work. The reservation state belongs to the core/hart, not to a speculative stage. A valid SC consumes reservation regardless of SC success; trap/fault handling clears reservation as defined above. DIV holds must preserve all atomic/non-atomic instruction metadata and cannot issue duplicate atomic transactions.

## Existing memory and pipeline constraints

The current core interfaces expose combinational `dmem_rdata`, `dmem_re`, byte-enable `dmem_we`, and `dmem_wdata`; the SystemVerilog testbench performs synchronous writes. There is no atomic request/response, transaction lock, or external-write invalidation port. Splitting AMO into an ordinary load and later store would not provide atomicity against another memory agent. Stage 5 RTL must therefore define a single atomic transaction handshake (request with op/address/operand/aq/rl; response with old word, completion, and access status) or an explicitly locked atomic memory transaction before implementation. The one-hart testbench can implement the response atomically on one memory edge, but that is not multi-hart validation.

Pipeline requirements: `rs1` is an address source for all A operations; `rs2` is a data source for SC/AMO but not LR; every A instruction has an `rd` result, including SC status. Forward both sources using the existing bypass network, retain load-use interlocks, and forward the AMO old value/SC result after completion. Freeze younger stages while an atomic transaction is outstanding. Existing divider protocol/holds must remain independent. Carry Stage 4 original instruction metadata through the atomic hold, and verify redirect/fault flushes cannot issue speculative requests.

## Software implementation and independent validation

Software additions in this batch are `rv32a_model.py` (table-based legal decode/arithmetic; no assembler dependency), explicit A encodings in the mixed-width assembler, an A-enabled ISS mode, 12 `rv32ima_software` programs, and a C-enabled AMO at PC offset two. The assembler and ISS decoder do not call each other. The validator has literal hand-derived word anchors and separate literal arithmetic expectations. It scans 2,048 `funct5/funct3/rs2/aq/rl` legality combinations (expected 84 legal field combinations), checks all 36 operation/boundary arithmetic pairs, runs the directed assembly/ISS programs, and compares all 230 Stage 4 sources/images/ISS traces plus saved golden/pipeline traces in A-disabled mode.

Keep the existing names `run_stage5.py`, `run_stage5_xsim.bat`, `prepare_stage5.py`, and `stage5_coverage.py`: these are historical Stage 3.5 M-extension regression/coverage entry points, not Stage 5 A-extension runners. This batch adds `validate_stage5_a.py` and does not repurpose historical scripts or reports.

One Windows CMD command from the repo root:

```cmd
py -3 scripts\simulation\validate_stage5_a.py --stage4-dir sim_out_stage4_4_xsim_20261108T154108Z
```

Required terminal marker after a successful run: `STAGE5_A_SOFTWARE_VALIDATION PASS groups=5 failures=0 stage4_cases=230`. Expected group markers are `STAGE5_A_ENCODING PASS checks=14`, `STAGE5_A_LEGALITY PASS checks=2048`, `STAGE5_A_ARITHMETIC PASS checks=36`, `STAGE5_A_DIRECTED_ISS PASS checks=13`, and `STAGE5_A_STAGE4_COMPAT PASS checks=230`. These are expected markers only; no software PASS is claimed until the command runs successfully. Compatibility requires the preserved Stage 4 output directory; the supplied default corresponds to the accepted XSim run and includes archived images, ISS references, golden traces, and pipeline traces.

## Gated follow-on plan

| Substep | Scope | Gate |
|---|---|---|
| 5.0/5.1 | This specification review, assembler/model/ISS support, directed software vectors, and exact 230-case A-disabled compatibility | `validate_stage5_a.py` all five groups pass; software-only |
| 5.2 | Standalone synthesizable atomic decode/result unit plus independent vector/unit checks | All legal/reserved encodings and AMO arithmetic vectors agree with independent literals in XSim and Verilator |
| 5.3 | Golden single-cycle core and atomic memory handshake; precise faults and retirement/sidecar records | Golden RTL vs independent A ISS on all A programs; Stage 4 compatibility preserved |
| 5.4 | Five-stage pipeline atomic transaction/holds, reservation ownership, hazards/forwarding/flush/fault behavior and divider interaction | Full pipeline vs both golden RTL and ISS; atomic protocol counters checked independently |
| 5.5 | A architectural and pipeline coverage dictionary, directed gap closure, mutation suite, C-disabled regression | Separate simulator coverage and Verilator mutation evidence; finite scope reported explicitly |
| 5.6 | Final documentation, report manifest, review, commit/push, owner release | No merge/tag until owner approval |

No RTL, CSR, privileged/trap, multi-hart, coherence, synthesis/timing, or ML work is part of Stage 5.0/5.1.

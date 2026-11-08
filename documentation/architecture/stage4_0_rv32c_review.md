# Stage 4.0 — RV32C specification review and implementation plan

**Status:** Stage 4.0 review approved; this file remains the planning baseline.
Stage 4.0 itself made no RTL, assembler, ISS, or test behavior changes.

## 1. Specification baseline and scope

Use the RISC-V International ratified Unprivileged ISA manual release
**v20260120** as the pinned source set. Its C chapter is **“C” Extension for
Compressed Instructions, Version 2.0**; the base is RV32I Version 2.1 and the
existing M extension is Version 2.0. Pin URLs, rather than a moving `stable`
alias:

* [C extension v2.0, manual release v20260120](https://docs.riscv.org/reference/isa/v20260120/unpriv/c-st-ext.html)
* [RV32I v2.1, manual release v20260120](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)
* [Unprivileged ISA introduction and instruction-length encoding, v20260120](https://docs.riscv.org/reference/isa/v20260120/unpriv/intro.html)
* [Zc* extension v1.0.0, manual release v20260120](https://docs.riscv.org/reference/isa/v20260120/unpriv/zc.html)
* [Official Unprivileged ISA index](https://docs.riscv.org/reference/isa/v20260120/unpriv/unpriv-index.html)

Stage 4 target: RV32IMC, meaning the existing RV32I+M implementation plus the
standard **RV32C v2.0 integer compressed encodings** that expand to currently
implemented RV32I/M operations. C allows 16- and 32-bit instructions on
halfword boundaries (IALIGN=16); a 32-bit instruction can start at PC bit 1.
All C control-flow offsets are multiples of two, and C.JAL/C.JALR link to
`PC+2`.

Explicitly outside this stage: floating-point state and C.FLW/C.FSW,
C.FLD/C.FSD families (including stack-relative forms); RV64C-only C.ADDIW,
C.SUBW, C.ADDW, LD/SD encodings; RV128; Zcb, Zcmp, Zcmt and other Zc* additions
not part of the selected RV32C v2.0 integer scope; A, CSR, privileged, and
other extensions. In particular, C.MUL and byte/halfword compressed
load/store or bit-manipulation instructions are not RV32C v2.0 integer C
instructions and must not be accepted as part of this work.
The v1.0.0 Zc terminology calls the integer-only portion of C (excluding the
compressed floating-point loads/stores) **Zca**; this is a naming/subset
relationship, not a request to implement additional instructions. C.NTL.*
HINT interpretations require Zihintntl and remain ignored HINTs in this
project.

### RV32C integer encoding/legality map

The table maps the three quadrants (`inst[1:0]`) and major opcode
(`inst[15:13]`). Within an opcode, the operand/immediate constraints below
still determine legal, HINT, or reserved/custom code points. `rd′/rs1′/rs2′`
map the three-bit fields to x8–x15. Other operands and immediates use the
field diagrams in the pinned C chapter.

| Quadrant | funct3 | RV32C v2.0 interpretation | RV32 policy |
|---|---:|---|---|
| Q0 `00` | `000` | C.ADDI4SPN | Legal iff its unsigned scaled immediate is nonzero; zero is reserved/illegal. |
| Q0 `00` | `001` | C.FLD (RV32D); same major opcode as RV64C C.FLD | Floating-point instruction, illegal here. |
| Q0 `00` | `010` | C.LW | Legal, expands to LW. |
| Q0 `00` | `011` | C.FLW in RV32FC; C.LD in RV64C | F is absent here, so illegal; it is not RV32 integer LD. |
| Q0 `00` | `100` | Reserved | Illegal. |
| Q0 `00` | `101` | C.FSD (RV32D/RV64D) | Floating-point instruction, illegal here. |
| Q0 `00` | `110` | C.SW | Legal, expands to SW. |
| Q0 `00` | `111` | C.FSW in RV32FC; C.SD in RV64C | F is absent here, so illegal; it is not RV32 integer SD. |
| Q1 `01` | `000` | C.ADDI / C.NOP | Legal ADDI for rd≠x0 and imm≠0; imm=0 is HINT; rd=x0, imm=0 is C.NOP; rd=x0, imm≠0 is HINT. |
| Q1 `01` | `001` | C.JAL in RV32C; C.ADDIW in RV64C | RV32C C.JAL legal; RV64 interpretation must not leak into RV32. Link is PC+2. |
| Q1 `01` | `010` | C.LI | Legal for rd≠x0; rd=x0 is HINT. |
| Q1 `01` | `011` | C.ADDI16SP if rd=x2; otherwise C.LUI | ADDI16SP requires nonzero immediate; LUI requires rd∉{x0,x2} and nonzero immediate. rd=x0 with nonzero immediate is HINT; zero immediate is reserved. |
| Q1 `01` | `100` | C.SRLI, C.SRAI, C.ANDI, or CA register-register group | SRLI/SRAI/ANDI legal on x8–x15; shift amount zero is HINT for SRLI/SRAI. CA bit12=0 selects SUB/XOR/OR/AND. With bit12=1, SUBW/ADDW slots are RV64-only and reserved in RV32; remaining slots reserved. RV32 shift bit5=1 is custom-designated and unsupported here, so illegal. |
| Q1 `01` | `101` | C.J | Legal jump, sign-extended offset in multiples of 2. |
| Q1 `01` | `110` | C.BEQZ | Legal branch on x8–x15. |
| Q1 `01` | `111` | C.BNEZ | Legal branch on x8–x15. |
| Q2 `10` | `000` | C.SLLI | Legal RV32 shift when bit5=0; rd=x0 or shift amount zero is HINT. bit5=1 is custom-designated/unsupported and illegal here. |
| Q2 `10` | `001` | C.FLDSP (RV32DC/RV64DC) | D is absent here; illegal. |
| Q2 `10` | `010` | C.LWSP | Legal iff rd≠x0; rd=x0 reserved/illegal. |
| Q2 `10` | `011` | C.FLWSP in RV32FC; C.LDSP in RV64C | F is absent here; illegal; RV64 integer meaning must not leak into RV32. |
| Q2 `10` | `100` | CR: C.JR, C.MV, C.EBREAK, C.JALR, C.ADD | rs2=x0 and bit12=0 selects JR (rs1≠x0; rs1=x0 reserved); rs2≠x0 and bit12=0 selects MV (rd=x0 HINT); bit12=1, rs2=x0, rs1=x0 is EBREAK, otherwise JALR; bit12=1, rs2≠x0 selects ADD (rd=x0 HINT). JALR link is PC+2. |
| Q2 `10` | `101` | C.FSDSP (RV32D/RV64D) | D absent; illegal. |
| Q2 `10` | `110` | C.SWSP | Legal, expands to SW. |
| Q2 `10` | `111` | C.FSWSP (RV32F); C.SDSP (RV64C) | F is absent here; illegal, not an RV32 integer store. |
| all `11` | any | Instruction longer than 16 bits; includes standard 32-bit base instructions and longer-length prefixes | Fetch length predecode distinguishes 32-bit from >32-bit. Stage 4 accepts supported 32-bit RV32IM encodings and reports longer forms as precise unsupported/illegal, without execution or partial retirement. |

All-zero 16-bit encoding is permanently illegal. All-ones encodings and
prefixes indicating lengths above the implemented 16/32-bit set are rejected
as unsupported illegal instructions. The manual labels some slots reserved
and some custom-designated; this core has no such custom extension, so both
classes have deterministic illegal-instruction handling. Floating-point
forms are legal only when the matching F or D extension is implemented;
because this project has no FP register file or FP execution, these encodings
must fault rather than alias into integer instructions. RV64 interpretations
above are reference distinctions only: the configured base remains RV32.
Length predecode follows the pinned introduction: `inst[1:0] != 2'b11` is
16-bit; otherwise `inst[4:2] != 3'b111` is 32-bit; the 48-bit prefix is
`inst[5:0] == 6'b011111`, with remaining longer encodings classified by the
subsequent length bits: 64 bits uses `inst[6:0] == 7'b0111111`; the proposed
80–176-bit encodings use `inst[6:0] == 7'b1111111` and `inst[14:12] != 3'b111`
to select 80+16×nnn; `nnn=111` is reserved for lengths at least 192 bits.
The pinned manual states that only 16- and 32-bit encodings are frozen and
that the entire >32-bit encoding space remains reserved/tentative. Stage 4
supports only 16/32-bit instructions; it classifies longer prefixes for
precise rejection and does not treat a recognized length prefix as an
implemented instruction.

HINTs are architecturally no-ops except PC advance and applicable counters.
The implementation plan is to retire them once, advance by two bytes, and
make no register or memory change. Preserve their raw encoding in the trace.
The standard HINT list includes C.NOP with nonzero immediate, C.ADDI with
zero immediate or rd=x0, C.LI/C.LUI with rd=x0 (C.LUI immediate must be
nonzero), C.MV/C.ADD with rd=x0 under the table constraints, C.SLLI with
rd=x0 or zero shift, and C.SRLI/C.SRAI with zero shift. C.ADD's x0 source
register cases encode other CR instructions, including C.JALR/C.EBREAK, and
must be decoded before HINT classification.

## 2. Existing implementation seams read for this plan

* `rv_if_stage` and `rv_core_single` fetch fixed 32-bit words and increment
  PC by four. The testbench memory is a 64 KiB word array indexed by
  `PC[15:2]`; it cannot select a halfword at offset two or signal a missing
  second parcel.
* `rv_pipe_pkg` carries PC and one 32-bit `insn` through IF/ID, ID/EX,
  EX/MEM, and MEM/WB, without raw bits or instruction length. The shared
  decoder consumes the instruction directly. Forwarding/hazard source-use
  comes from decoded opcode fields.
* `rv_ex_stage` redirects branch/JAL/JALR and raises `HALT_FETCH_MISALIGN`
  on target bit 1. Its link selection is PC+4. `rv_core_single` has matching
  fixed-width PC/link/alignment assumptions.
* `rv32_asm.py` emits one 32-bit word per statement and sizes ordinary
  instructions as four bytes. `rv32i_iss.py` fetches aligned words, advances
  PC by four, and rejects encodings whose low bits are not `11`.
* `tb_rv_core`, pipeline benches, traces, and checkers assume 32-bit raw
  instructions and a seven-field retirement row. Current Stage 3 regression
  checks 209 programs, independent golden/ISS traces, cycle behavior, M
  protocol, and unit suites. New C work must preserve the existing reports
  and Stage 3 commands/artifacts.

## 3. Required implementation design decisions

### Software model and assembly

Create a compressed-aware assembler path that tracks byte addresses per
statement, packs little-endian 16-bit parcels into the existing memory image,
and resolves labels using mixed instruction sizes. Add explicit `.2byte`
or compressed directives/raw-halfword support for tests and use deterministic
automatic compression only if separately specified. Retain current Stage 3
assembler output byte-for-byte for legacy 32-bit programs. Build the ISS's
compressed expansion/legality logic independently from RTL: model raw fetch,
length, HINTs, reserved/custom/extension-disabled cases, and architectural
execution. Do not import RTL decode tables or call the decompressor to produce
ISS expected behavior.

### RTL decompression and mixed fetch

Add a combinational decompressor before the existing base decoder. It returns
expanded 32-bit instruction, legal/HINT status, raw 16-bit bits, and length.
For 32-bit instructions, preserve the original word and length. Fetch parcels
in little-endian order from a halfword-addressable interface. A 32-bit
instruction beginning at PC[1]=1 combines the upper half of one memory word
with the lower half of the next word. Hold both parcels and their PC/length
metadata stable across stalls. Redirects and faults discard younger partial
fetch state.

Use `PC + instruction_length_bytes` for sequential PC and every link address;
control target remains `PC + expanded immediate`, with JALR clearing bit 0.
Under IALIGN=16, branch/JAL targets with bit1=1 are valid; no instruction
address misalignment fault is raised for a halfword-aligned PC. Preserve
precise synchronous halting: a faulting instruction does not retire or
modify architectural state; older pipeline operations may retire; younger
operations are squashed. HINTs retire as no-ops. Illegal/reserved/unsupported
instructions retain the raw encoding and fault at their own PC.

Current 64 KiB simulation memory needs a valid/error indication per parcel.
For a 32-bit instruction whose second parcel crosses the end of executable
memory, report a precise instruction-fetch access failure at the instruction
PC, do not retire it, and do not count a testbench out-of-bounds read as a
passing fetch. This may require a new implementation halt cause/trace marker;
it is not a new privileged trap claim. C.LW/LWSP and C.SW/SWSP expand through
the existing LSU and keep its alignment and data-boundary checks.

Extend pipeline records with raw instruction bits and `ilen` while passing
the normalized 32-bit instruction to current decode/execute logic. Compressed
register fields must be expanded before use-source detection, forwarding,
load-use detection, and writeback destination matching. Keep IF/ID raw bits,
length, PC and validity together through stalls. Verify redirect flush takes
priority over partially fetched younger instructions; preserve the divider
hold contract (PC and front-end metadata hold while an iterative DIV/REM is
busy, then the held instruction advances once). Compressed branches and
jumps must squash younger work exactly once.

### Trace and retirement compatibility

Keep the Stage 3 trace schema and default RV32IM behavior reproducible.
Proposed gate: add an explicit `ENABLE_C` parameter/mode defaulting off on
existing core/bench entry points. Legacy tests then retain IALIGN=32, their
old halt causes, exact trace rows, and known reports. Add an explicit RV32IMC
mode/runner using a versioned trace schema carrying `pc`, `raw_insn`,
`ilen_bytes`, normalized instruction if useful to checkers, and the existing
architectural write/store columns. Never represent a 16-bit instruction by
silently substituting its expanded word in the legacy `insn` field. The
checker must compare raw encoding/length as well as architectural behavior.

Keep the Stage 3 tag and historical outputs immutable. Stage 4 regressions
must rerun the released Stage 3 mode and report it separately from new C
coverage; enabling C must be explicit. The proposed parameter/schema design
needs review before implementation because it affects public benches and
trace consumers.

## 4. Existing target-alignment tests affected

The following generated Stage 1 / pipeline tests currently expect
`HALT_FETCH_MISALIGN` for a taken transfer to a PC that is 2 mod 4. With C
enabled, these targets are legal IALIGN=16 addresses. Preserve their Stage 3
versions and baseline expected causes unchanged. Add corresponding
RV32IMC cases with a real instruction at the halfword target, then expect the
target instruction to execute and retire. Do not merely change the expected
cause or remove a test:

* `tests/directed/rv32i/misalign_branch_taken.s` / manifest entry.
* `tests/directed/rv32i/misalign_jal_target.s` / manifest entry.
* `tests/directed/rv32i/misalign_jalr_target.s` / manifest entry.
* `tests/directed/pipeline/pipe_misalign_branch_taken_squash.s` / manifest.
* `tests/directed/pipeline/pipe_misalign_jalr_after_load.s` / manifest.

Keep `branch_notaken_misaligned_ok` as a distinct not-taken control-transfer
check: a branch that is not taken does not validate/use its target. Keep all
data load/store alignment tests; C changes instruction alignment, not LSU
alignment. Add negative odd-address JALR tests only for semantics other than
the architectural low-bit clearing, since JALR clears bit 0 before target
alignment and IALIGN=16 permits bit1.

## 5. Gated implementation sequence

Each substep has its own review gate and must preserve earlier reports.

1. **4.1 Software model and assembler.** Independent RV32C ISS; mixed-size
   assembler/layout/labels and packed byte/halfword output; legality tests.
2. **4.2 Decompressor units.** Pure combinational RTL; legal expansion,
   HINT and illegal classification; exhaustive encoding checks and directed
   field/immediate tests; no core integration.
3. **4.3 Golden-core fetch.** Add parcel fetch, halfword alignment,
   cross-word 32-bit fetch, PC/link updates, trace-v2 and precise faults to
   the single-cycle golden/reference RTL only. Compare against ISS.
4. **4.4 Pipeline integration.** Carry raw/length metadata; forwarding,
   load-use, redirect/flush, divider hold, and exact-once retirement with
   mixed lengths. Compare pipeline, golden RTL, and ISS traces.
5. **4.5 Coverage.** Define finite stable bins for opcode families,
   legal/reserved/HINT cases, RV32-vs-RV64 distinctions, instruction length,
   PC[1] cross-word fetch, target/link behavior, boundaries, and pipeline
   hazards before adding sampling. State denominator and reachability.
6. **4.6 Mutation.** Separate explicit RV32C campaign, scoped mutants for
   decompression/fetch/length/PC/trace/hazards, preserve raw outcomes, and
   adjudicate equivalent mutants with evidence.
7. **4.7 Regression.** Consolidated explicit RV32IM baseline and RV32IMC
   suites for XSim and Verilator; fresh outputs, preflight, per-test progress,
   malformed/missing artifact failure, separate reports and historical names.
8. **4.8 Documentation/release.** Evidence, finite scope, limitations,
   manifest and commands; owner review before release tag/merge.

Stage 4.0 approval authorized Stage 4.1 software-only implementation. Stage
4.1 has passed its owner-supplied software validation gate. RTL work remains
substep-gated; Stage 4.2 is limited to a standalone combinational decompressor
and its independent unit validation, with no fetch/core/pipeline integration.

## 6. Independent and exhaustive validation

Do not derive expected results from the RTL decompressor or share a decoder
implementation between ISS and RTL. The independent ISS should be written
from the pinned encoding tables and execute decompressed semantics itself.
For every 16-bit value (65,536 encodings), compare the RTL decompressor's
expanded instruction, legality/HINT class, and length against an independently
written software oracle generated from the specification tables. Include
specific counts by quadrant/funct3 and assert that each encoding is accounted
for exactly once as legal, HINT, reserved/custom/unsupported, or
extension-disabled. Validate that legal expansion re-encodes to expected
base operation fields and that HINTs leave state unchanged except PC/counters.

Also run an independent trusted assembler/disassembler or formal decoder
cross-check for legal encodings (record tool/version), plus hand-derived
golden vectors for every immediate permutation, register mapping, control
target, link PC, and reserved boundary. The external tool is corroboration,
not the sole expected source. Use directed memory images to exercise every
16-bit PC phase, especially a 32-bit fetch at PC[1]=1 across adjacent words,
last-halfword fetch, and missing second parcel. Validate mixed-length golden
core and pipeline architectural traces byte-for-byte against the independent
ISS, then test load-use, forwarding, branch/JAL/JALR flush, and an older or
younger iterative divide with compressed instructions around held/redirected
fetch. Keep Stage 3 cycle/protocol and exact baseline regression commands as
reproduction checks.

## 7. Stage 4.0 completion boundary

This document records the approved scope and implementation plan. Stage 4.1
software validation is recorded in the project logs. Later substeps still
require their own validation and review gates; no whole-extension compliance
claim follows from this plan or the Stage 4.1 software result.

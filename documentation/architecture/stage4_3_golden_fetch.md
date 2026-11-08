# Stage 4.3: mixed-width fetch and golden-core contract

**Scope:** Stage 4.3 only. This adds RV32IMC fetch/decompression and
retirement metadata to the single-cycle golden core. It does not integrate
the pipeline. C remains explicitly disabled by default.

## Fetch interface

The golden core keeps a combinational instruction-memory interface and
exposes two aligned 32-bit word addresses:

| Signal | Direction | Contract |
|---|---|---|
| `imem_addr` | output | `{pc[31:2],2'b00}`, the word containing the current PC. |
| `imem_rdata` | input | Little-endian word at `imem_addr`. For a PC at word offset 2, its upper halfword is the first parcel. |
| `imem_valid` | input | Current word exists. Low validity causes a fetch-access fault at the original PC before retirement. |
| `imem_addr_next` | output | `imem_addr + 4`, the next word address. |
| `imem_rdata_next` | input | Little-endian next word. For a 32-bit instruction at offset 2, its low halfword completes the instruction. |
| `imem_next_valid` | input | Next word exists. It is required only when a 32-bit prefix begins at offset 2. A missing second parcel faults at the instruction PC; no partial instruction retires. |

The TB memory reports validity instead of performing invalid array reads.
The final compressed halfword at `0xfffe` is fetchable; advancing beyond it
then produces a fetch-access halt. A 32-bit prefix at `0xfffe` needs the next
parcel and faults at `0xfffe` if it is absent. Odd instruction PCs fault as
instruction-address-misaligned; with C enabled, PC bit 1 is valid.

`dmem_valid` indicates that the data address is within the 64 KiB data memory.
In C mode an invalid load/store halts precisely with local halt causes 7/8;
the LSU's existing alignment causes 4/5 retain priority. The TB suppresses an
out-of-range transaction and never indexes outside its memory array. These
halt codes are project-local and do not claim privileged trap support.

## Instruction and retirement metadata

`ENABLE_C` is a core parameter defaulting to zero. When zero, fetch remains a
single full 32-bit instruction, PC advances by four, targets retain Stage 3
IALIGN=32 checks, and the existing trace format and behavior remain unchanged.
The additional fetch ports are driven by the testbench but the C-disabled
core ignores the second word and validity metadata.

When enabled, the core selects the parcel at `pc[1]`, invokes the standalone
combinational decompressor, and forms a crossing 32-bit instruction as
`{imem_rdata_next[15:0], imem_rdata[31:16]}`. Legal compressed forms execute
through the existing RV32I/M decoder as their canonical expansions. HINTs
retire as NOPs; reserved/unsupported compressed encodings and >32-bit length
prefixes fault without retirement. A standard 32-bit prefix uses the original
32-bit instruction and is checked by the existing decoder.

PC fall-through and JAL/JALR links use `pc + ilen_bytes` (2 or 4). Branch,
JAL and JALR targets use the canonical immediate and permit halfword alignment;
JALR clears bit zero. M behavior remains unchanged.

The legacy `ret_insn` field stays the raw encoding (zero-extended for a
compressed instruction). New `ret_expanded_insn` and `ret_ilen_bytes` fields
carry the canonical operation and original length. New `ret_raw_insn` makes
the raw/expanded distinction explicit. On a precise halt, `halt_pc`,
`halt_raw_insn`, and `halt_ilen_bytes` retain the faulting PC and known
encoding metadata. A faulting instruction has `ret_valid=0` and cannot write
registers or data memory.

The C-mode golden trace is versioned:

```text
TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data
I <pc> <raw> <2|4> <expanded> <rd> <rdval> <st_size> <st_addr> <st_data>
STOP <fault_pc> <raw_or_prefix> <known_length_bytes_or_0> <local_cause>
HALT <local_cause> <fault_pc>
REG ...
MEM ...
```

The disabled mode keeps the existing seven-field retirement rows and footer.
The independent software ISS supplies all expected traces; no expected
compressed instruction or architectural result is generated from RTL.

## Compatibility and verification boundary

Stage 4.3 modifies `rv_core_single` and updates its legacy TB port wiring, so
the released 209 C-disabled cases must be rerun against the Stage 3 software
ISS. Their assembler sources, expectations, and trace schema remain intact.
New RV32IMC programs use explicit compressed mnemonics and the independent
`rv32imc_iss` reference. The regression inventory is read from manifests and
reported from the actual rows rather than a guessed fixed suite count.

The combined Stage 4.3 runners also rerun the 65,536-pattern decompressor
unit and 16 hand anchors, then compare each golden-core C trace byte-for-byte
against the software ISS trace. XSim and Verilator results remain separate.
This gate does not cover pipeline C integration, performance, whole-ISA
compliance, or architectural trap CSRs.

## Reproducibility and current status

The checked-in inventory is 209 released C-disabled programs plus 12 explicit
RV32IMC programs, so the complete core comparison is 221 rows. The C cases
cover the supported Q0/Q1/Q2 integer families, stack loads/stores, HINTs/x0,
compressed and standard control flow, PC-offset-2 32-bit crossing, illegal
and long prefixes, a data boundary fault, the final compressed parcel, and
compressed JALR link behavior.

The assembler's stack-relative compressed memory syntax is `c.lwsp rd,offset`
and `c.swsp rs2,offset`; the base is implicitly `x2`. This differs from the
register-base compressed forms `c.lw rd,offset(rs1')` and
`c.sw rs2,offset(rs1')`. Stage 4.3 preparation first assembles every C source,
reports per-file errors with source line numbers, and fails before running ISS
preparation if any source does not assemble.

Windows CMD (Vivado XSim and Python 3 on PATH):

```bat
cd /d C:\RISC-V-ML-Test-Selection
scripts\simulation\run_stage4_3_xsim.bat
```

Windows CMD to Ubuntu WSL (Python 3, Verilator 5.x, GNU make and C++ compiler):

```bat
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage4_3_verilator.sh
```

Each command preflights tools, prepares independent software traces, runs the
65,536-pattern decompressor check, prints per-test progress, checks one
terminal test result per program, and compares complete traces. It writes a
fresh `sim_out_stage4_3_<sim>_<UTC>/` directory and separate
`reports/stage4_3_golden_<sim>_<UTC>.txt`. Expected final markers are
`STAGE4_3_GOLDEN_XSIM PASS rtl_vs_iss=221` and
`STAGE4_3_GOLDEN_VERILATOR PASS rtl_vs_iss=221`. Owner-verified XSim resume
evidence is recorded in `reports/stage4_3_golden_xsim_resume_20261108T102530Z.txt`:
209 source-consistent legacy results and 12/12 newly executed C trace matches.
Fresh owner Verilator evidence is recorded in
`reports/stage4_3_golden_verilator_20261108T102658Z.txt`: 221/221
RTL-vs-ISS comparisons PASS. Simulator evidence remains separate by tool;
local reruns are unavailable in the current Codex environment.

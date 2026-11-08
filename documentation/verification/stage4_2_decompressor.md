# Stage 4.2 standalone RV32C decompressor

## Scope and interface

`rtl/decoder/rv32c_decompressor.sv` implements a combinational, standalone
RV32C v2.0 integer decompressor. It does not modify or connect the Stage 3
decoder, fetch path, golden core, or pipeline. Its ports are:

| Port | Meaning |
|---|---|
| `raw_halfword[15:0]` | Current little-endian instruction parcel. |
| `expanded_insn[31:0]` | Canonical RV32I/M instruction for legal compressed forms; canonical NOP for HINTs; zero for illegal compressed forms and noncompressed prefixes. |
| `length_bits[7:0]` | Prefix-classified length in bits: 16, 32, 48, 64, or 80–176. Zero means the reserved ≥192-bit prefix has no exact length in this parcel. |
| `is_compressed` | One only for a 16-bit parcel (`raw_halfword[1:0] != 2'b11`), regardless of legality. |
| `is_32bit_prefix` | One only for a standard 32-bit prefix. The full 32-bit instruction must be fetched elsewhere; expansion is zero here. |
| `unsupported_length` | One for every prefix longer than 32 bits. This classifies fetch length, not C legality. |
| `illegal` | One only for reserved, unsupported, or otherwise illegal *compressed* encodings. Zero for noncompressed prefixes. |
| `hint` | One for RV32C HINT encodings; expansion is canonical `addi x0,x0,0`. |

Only RV32C v2.0 integer forms in the approved Stage 4.0 plan are accepted.
Floating-point, RV64-only, custom/unsupported shift, reserved, and non-C
extension instructions do not acquire an integer interpretation. Illegal
compressed encodings set `illegal`, clear `hint`, and return zero expansion.
A 32-bit prefix has `is_32bit_prefix=1`, `illegal=0`, `unsupported_length=0`;
its upper parcel and legality belong to the later fetch/decode stage. Longer
prefixes set `unsupported_length=1` and return zero expansion. HINTs remain
legal no-ops and are distinct from illegal encodings.

The length output follows the pinned v20260120 manual prefix rules, but only
16- and 32-bit lengths are frozen. The >32-bit classes are tentative/reserved
and unsupported by the project.

Hand-derived branch anchor: `0xc009` has quadrant `01`, funct3 `110`
(`C.BEQZ`), prime rs1 field `000` (x8), and immediate bit `inst[3]` set,
which maps to byte offset +2. The canonical `beq x8,x0,+2` is
`0x00040163`. `0x00040463` encodes a different branch displacement and was an
incorrect anchor expectation; the decompressor output was correct.

## Exhaustive independent validation

`scripts/simulation/generate_stage4_2_vectors.py` emits one vector for every
16-bit halfword. Expected classification and expansion come from the
Stage 4.1 table-oriented specification oracle and are cross-checked against
the separately written `rv32c_model` before serialization. Neither source
loads or calls RTL. The SystemVerilog testbench reads the vectors and compares
all output fields with case inequality, reports the first 25 mismatches with
raw input and expected/actual fields, asserts exactly 65,536 rows, and runs 16
hand-derived anchors for expansions, HINT/illegal distinctions, and length
prefixes. The vector-generator marker also reports status counts,
quadrant/funct3 counts, and full prefix-length bins; the unit marker reports
class counts.

Expected markers:

* `RV32C_VECTOR_GENERATION PASS halfwords=65536 oracle_mismatches=0 legal=28461 hint=362 illegal=20329 prefix32=14336 unsupported_length=2048 ...`
* `RV32C_DECOMPRESS_UNIT PASS halfwords=65536 mismatches=0 anchors=16 legal=28461 hint=362 illegal=20329 prefix32=14336 unsupported_length=2048`
* `STAGE4_2_DECOMPRESSOR_XSIM PASS halfwords=65536 anchors=16` or
  `STAGE4_2_DECOMPRESSOR_VERILATOR PASS halfwords=65536 anchors=16`.

## Runners and dependencies

Windows XSim (Vivado 2026.1 command environment):

```cmd
scripts\simulation\run_stage4_2_decompressor_xsim.bat
```

Requires `py -3` (Python 3), `xvlog`, `xelab`, and `xsim` on PATH. The runner
preflights them, creates a unique timestamped
`sim_out_stage4_2_xsim_<timestamp>` directory, generates fresh
vectors/build/logs there, and writes a unique report under
`reports\stage4_2_decompressor_xsim_<timestamp>.txt`.

Ubuntu/WSL Verilator (run from the repository mount):

```bash
cd /mnt/c/RISC-V-ML-Test-Selection
bash scripts/simulation/run_stage4_2_decompressor_verilator.sh
```

Requires Python 3, Verilator with `--binary --timing` support, GNU Make, and a
G++ compiler. It uses fresh `sim_out_stage4_2_verilator_<UTC>` and
`reports/stage4_2_decompressor_verilator_<UTC>.txt` paths. Both runners fail
on missing tools, vector-generation errors, compile/run errors, missing or
malformed final markers, and nonzero simulator exits. They do not clean or
reuse existing outputs.

These names explicitly identify the ISA substep. Existing `run_stage4_xsim`
and `run_stage5_xsim` files are historical Stage 3 regression names (Stage
3.7 and 3.5 compatibility entry points respectively); they are not Stage 4
and Stage 5 ISA-extension runners.

No simulator is available in the current Windows environment, and WSL is not
retried because it was previously inaccessible. No simulation PASS is
claimed until the separate XSim and Verilator unit runners produce their
markers.

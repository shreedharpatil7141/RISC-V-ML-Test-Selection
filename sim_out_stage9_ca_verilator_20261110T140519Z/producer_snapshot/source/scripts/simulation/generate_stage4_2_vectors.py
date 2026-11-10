#!/usr/bin/env python3
"""Create exhaustive standalone RV32C decompressor vectors.

Expected values come from the Stage 4.1 table-oriented oracle and are checked
against the separately written software decoder before being emitted. No RTL
source is parsed or executed by this generator.
"""
import argparse
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from validate_stage4_1 import oracle_decode, oracle_length
import rv32c_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    parent = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(parent, exist_ok=True)
    counts = {"legal": 0, "hint": 0, "illegal": 0, "prefix32": 0, "unsupported": 0}
    lengths = Counter()
    qf_counts = Counter()
    with open(args.output, "w", encoding="ascii", newline="\n") as out:
        for raw in range(65536):
            length = oracle_length(raw)
            lengths[length] += 1
            model_length = rv32c_model.instruction_length(raw)
            if model_length != length:
                raise SystemExit(
                    f"LENGTH_ORACLE_DIFF raw={raw:04x} table={length} model={model_length}"
                )
            cls, expanded = oracle_decode(raw)
            qf_counts[((raw & 3), (raw >> 13) & 7, cls)] += 1
            decoded = rv32c_model.decode16(raw)
            if (decoded.status, decoded.expanded) != (cls, expanded):
                raise SystemExit(
                    f"VECTOR_ORACLE_DIFF raw={raw:04x} table={cls}/{expanded:08x} "
                    f"model={decoded.status}/{decoded.expanded:08x}"
                )
            if length == 16:
                compressed, prefix32, unsupported = 1, 0, 0
                counts[cls] += 1
                illegal, hint = int(cls == "illegal"), int(cls == "hint")
                word = expanded
            elif length == 32:
                compressed, prefix32, unsupported = 0, 1, 0
                counts["prefix32"] += 1
                illegal = hint = 0
                word = 0
            else:
                compressed, prefix32, unsupported = 0, 0, 1
                counts["unsupported"] += 1
                illegal = hint = 0
                word = 0
            length_field = 0 if length is None else length
            out.write(
                f"{raw:04x} {length_field:02x} {compressed:d} {prefix32:d} "
                f"{unsupported:d} {illegal:d} {hint:d} {word:08x}\n"
            )
    expected_lengths = {
        16: 49152, 32: 14336, 48: 1024, 64: 512,
        80: 64, 96: 64, 112: 64, 128: 64,
        144: 64, 160: 64, 176: 64, None: 64,
    }
    expected_classes = {
        "legal": 28461, "hint": 362, "illegal": 20329,
        "prefix32": 14336, "unsupported": 2048,
    }
    if dict(lengths) != expected_lengths or counts != expected_classes:
        raise SystemExit(
            f"VECTOR_TOTALS_DIFF lengths={dict(lengths)} classes={counts} "
            f"expected_lengths={expected_lengths} expected_classes={expected_classes}"
        )
    qf_totals = Counter()
    for (quadrant, funct3, status), value in qf_counts.items():
        qf_totals[(quadrant, funct3)] += value
    if any(qf_totals[(q, f)] != 2048 for q in range(4) for f in range(8)):
        raise SystemExit(f"VECTOR_QF_ACCOUNTING_DIFF totals={dict(qf_totals)}")
    qf_summary = ";".join(
        f"q{q}f{f}:L{qf_counts[(q,f,'legal')]}H{qf_counts[(q,f,'hint')]}"
        f"I{qf_counts[(q,f,'illegal')]}X{qf_counts[(q,f,'long')]}"
        for q in range(4) for f in range(8)
    )
    print(
        "RV32C_VECTOR_GENERATION PASS halfwords=65536 oracle_mismatches=0 "
        f"legal={counts['legal']} hint={counts['hint']} illegal={counts['illegal']} "
        f"prefix32={counts['prefix32']} unsupported_length={counts['unsupported']} "
        f"length_bins={dict(lengths)} qf_counts={qf_summary} "
        f"oracle_crosscheck=rv32c_model output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

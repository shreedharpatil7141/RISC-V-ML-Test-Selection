#!/usr/bin/env python3
"""Fail closed on contradictory or incomplete decompressor simulator logs."""
import argparse
import re
import sys

PASS = re.compile(
    r"RV32C_DECOMPRESS_UNIT PASS halfwords=65536 mismatches=0 anchors=16 "
    r"legal=28461 hint=362 illegal=20329 prefix32=14336 unsupported_length=2048"
)
TERMINAL = re.compile(r"RV32C_DECOMPRESS_UNIT (?:PASS|FAIL)\b")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    args = parser.parse_args()
    try:
        with open(args.log, encoding="utf-8", errors="replace") as source:
            text = source.read()
    except OSError as exc:
        print(f"RV32C_SIM_LOG_CHECK FAIL cannot_read={exc}")
        return 1

    markers = list(TERMINAL.finditer(text))
    pass_markers = list(re.finditer(r"RV32C_DECOMPRESS_UNIT PASS\b", text))
    failures = []
    if "ANCHOR_DIFF" in text:
        failures.append("anchor_difference_present")
    if "VECTOR_DIFF" in text:
        failures.append("vector_difference_present")
    if len(markers) != 1:
        failures.append(f"terminal_marker_count={len(markers)}")
    if len(pass_markers) != 1:
        failures.append(f"pass_marker_count={len(pass_markers)}")
    elif not PASS.search(text):
        failures.append("pass_marker_counts_malformed")
    if re.search(r"RV32C_DECOMPRESS_UNIT FAIL\b", text):
        failures.append("terminal_fail_present")
    if re.search(r"\bFATAL\b", text, re.IGNORECASE):
        failures.append("fatal_diagnostic_present")

    if failures:
        print("RV32C_SIM_LOG_CHECK FAIL " + " ".join(failures))
        return 1
    print(
        "RV32C_SIM_LOG_CHECK PASS terminal_markers=1 pass_markers=1 "
        "halfwords=65536 mismatches=0 anchors=16"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

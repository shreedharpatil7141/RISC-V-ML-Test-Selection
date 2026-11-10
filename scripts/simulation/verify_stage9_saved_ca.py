#!/usr/bin/env python3
"""Validate an existing Stage 9 C/A run before reusing its saved evidence."""
import argparse
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from prepare_stage9_recovery import validate_stage5_ca_reuse


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim",choices=("xsim","verilator"),required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    details=validate_stage5_ca_reuse(args.report.resolve(),args.sim)
    print(f"STAGE9_SAVED_CA_REUSE PASS simulator={args.sim} selected=39 source_hashes_checked={details['source_hashes_checked']} "
          f"report_sha256={details['report_sha256']}")


if __name__=="__main__":
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"STAGE9_SAVED_CA_REUSE INVALID {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)

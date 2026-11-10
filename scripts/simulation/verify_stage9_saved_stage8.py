#!/usr/bin/env python3
"""Validate a saved Stage 8 report and its complete selected evidence."""
import argparse
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from prepare_stage9_recovery import validate_stage8_reuse


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim",choices=("xsim","verilator"),required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    args=parser.parse_args()
    details=validate_stage8_reuse(args.report.resolve(),args.sim,args.manifest.resolve())
    print(f"STAGE9_SAVED_STAGE8_REUSE PASS simulator={args.sim} selected=23 "
          f"source_hashes_checked={details['source_hashes_checked']} "
          f"report_sha256={details['report_sha256']} manifest_sha256={details['prepared_manifest_sha256']} "
          f"preparation_artifacts_checked={details['preparation_artifacts_checked']}")


if __name__=="__main__":
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"STAGE9_SAVED_STAGE8_REUSE INVALID {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Validate a saved Stage 6 run before reusing it in Stage 9 recovery."""
import argparse
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from prepare_stage9_recovery import validate_stage6_reuse


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim",choices=("xsim","verilator"),required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    args=parser.parse_args()
    details=validate_stage6_reuse(args.report.resolve(),args.sim,args.manifest.resolve())
    cmp=details["prepared_manifest_comparison"]
    print(f"STAGE9_SAVED_STAGE6_REUSE PASS simulator={args.sim} selected=11 "
          f"source_hashes_checked={details['source_hashes_checked']} report_sha256={details['report_sha256']} "
          f"semantic={cmp['status']} rows={cmp['rows_compared']} path_relocations={cmp['hexpath_relocations']} "
          f"artifact_hashes={cmp['image_and_reference_hashes_compared']} "
          f"original_manifest_sha256={cmp['original_manifest_sha256']} "
          f"refreshed_manifest_sha256={cmp['refreshed_manifest_sha256']}")


if __name__=="__main__":
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"STAGE9_SAVED_STAGE6_REUSE INVALID {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)

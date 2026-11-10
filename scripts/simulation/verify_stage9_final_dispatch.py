#!/usr/bin/env python3
"""Fail before simulation if Stage 9 final simulator dispatch is misrouted."""
import argparse
import re
import sys
from pathlib import Path


def check_dispatch(batch: Path) -> None:
    lines=batch.read_text(encoding="utf-8").splitlines()
    commands=[(i,line.strip()) for i,line in enumerate(lines)
              if "run_stage4_4.py" in line and "--stage9-legacy-gap" in line]
    verilator=[(i,line) for i,line in commands if "--sim verilator" in line.lower()]
    xsim=[(i,line) for i,line in commands if "--sim xsim" in line.lower()]
    if len(verilator)!=1 or len(xsim)!=1 or len(commands)!=2:
        raise ValueError("expected exactly one Verilator and one XSim legacy-gap launch")
    vi,vc=verilator[0]; xi,xc=xsim[0]
    if '"c:\\windows\\system32\\wsl.exe"' not in vc.lower() or "--distribution ubuntu" not in vc.lower():
        raise ValueError("Verilator must launch through quoted System32 WSL")
    if '"%python_exe%"' not in xc.lower() or "wsl.exe" in xc.lower():
        raise ValueError("XSim must launch Windows Python directly; XSim-under-WSL is forbidden")
    vivado=max((i for i,line in enumerate(lines) if line.strip().lower()=='call "%vivado_settings%"'),default=-1)
    if vivado<0 or xi<vivado:
        raise ValueError("Windows Vivado initialization must precede the direct XSim launch")
    if not re.search(r"--sim\s+verilator",vc,re.I) or not re.search(r"--sim\s+xsim",xc,re.I):
        raise ValueError("simulator flag does not match its launch route")


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("batch",type=Path)
    args=p.parse_args()
    check_dispatch(args.batch)
    print("STAGE9_SIMULATOR_DISPATCH PASS verilator=WSL xsim=Windows-after-Vivado")


if __name__=="__main__":
    try: main()
    except (OSError,ValueError) as exc:
        print(f"STAGE9_SIMULATOR_DISPATCH FAIL: {exc}",file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Run the complete Stage 4.4 regression, then its fixed RV32C coverage checker."""
import argparse, re, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
p=argparse.ArgumentParser(description=__doc__); p.add_argument('--sim',choices=('xsim','verilator'),required=True); a=p.parse_args()
cmd=[sys.executable,str(HERE/'run_stage4_4.py'),'--sim',a.sim]
proc=subprocess.Popen(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
lines=[]
for line in proc.stdout:
    sys.stdout.write(line); sys.stdout.flush(); lines.append(line)
rc=proc.wait(); text=''.join(lines)
if rc:
    raise SystemExit(rc)
match=re.search(r'TOOL PREFLIGHT PASS sim='+re.escape(a.sim)+r'.*?output=(.+)',text)
if not match:
    print('STAGE4_C_COVERAGE FAIL: runner did not identify fresh output directory',file=sys.stderr); raise SystemExit(1)
out=Path(match.group(1).strip())
if not out.is_dir():
    print(f'STAGE4_C_COVERAGE FAIL: missing regression output {out}',file=sys.stderr); raise SystemExit(1)
raise SystemExit(subprocess.run([sys.executable,str(HERE/'stage4_c_coverage.py'),str(out),a.sim],cwd=ROOT).returncode)

#!/usr/bin/env python3
"""Regenerate tests, assemble every Stage-1 test to .hex and write ISS reference traces.
Usage: python assemble_all.py [out_dir]   (default: sim_out_xsim/iss under project root)
Needed by run_stage1_xsim.bat (Windows/Vivado flow), which has no Python dependency beyond this step."""
import csv, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rv32_asm import assemble, to_hex
import rv32i_iss
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
TD = os.path.join(ROOT, 'tests', 'directed', 'rv32i')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'sim_out_xsim', 'iss')
subprocess.run([sys.executable, os.path.join(HERE, 'gen_rv32i_tests.py')], check=True)
os.makedirs(OUT, exist_ok=True)
for row in csv.DictReader(open(os.path.join(TD, 'manifest.csv'))):
    n = row['name']; mem = assemble(open(os.path.join(TD, n + '.s')).read())
    open(os.path.join(TD, n + '.hex'), 'w').write(to_hex(mem))
    words = [mem.get(4*i, 0) for i in range(max(mem)//4 + 1)]
    _, _, tr, foot, _, _ = rv32i_iss.run(words)
    open(os.path.join(OUT, n + '.iss.trace'), 'w', newline='\n').write("\n".join(tr + foot) + "\n")
print("assembled; hex in", TD, "ISS traces in", OUT)

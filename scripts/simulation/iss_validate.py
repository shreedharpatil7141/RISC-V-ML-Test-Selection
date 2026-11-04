#!/usr/bin/env python3
"""Assemble every Stage-1 test and run it on the Python ISS; check against manifest expectations."""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
from rv32_asm import assemble, to_hex
import rv32i_iss
D = os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'directed', 'rv32i')
bad = 0
for row in csv.DictReader(open(os.path.join(D, 'manifest.csv'))):
    n = row['name']; mem = assemble(open(os.path.join(D, n + '.s')).read())
    open(os.path.join(D, n + '.hex'), 'w').write(to_hex(mem))
    words = [mem.get(4*i, 0) for i in range(max(mem)//4 + 1)]
    cause, x, tr, foot, oob, cnt = rv32i_iss.run(words)
    ok = cause == int(row['expect_cause']) and (row['check_gp'] != '1' or x[3] == 1) and oob == 0
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {n:34s} cause={cause} gp={x[3]:#x} instret={cnt} oob={oob}")
print("ISS_VALIDATE", "PASS" if not bad else f"FAIL({bad})")
sys.exit(bad != 0)

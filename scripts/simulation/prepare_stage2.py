#!/usr/bin/env python3
"""Prepare Stage-2 regression inputs (does NOT touch Stage 1 sources).
Usage: python prepare_stage2.py <out_dir>
  - regenerates the pipeline directed tests (gen_pipe_tests.py)
  - assembles .hex for the Stage 1 suite (existing .s/manifest untouched) and the pipeline suite
  - runs the independent ISS on every test -> <out_dir>/iss/<name>.iss.trace
  - writes <out_dir>/manifest_all.csv   (name,expect_cause,check_gp,hexpath)
  - writes <out_dir>/expected.csv       (ISS-derived instret and stall/redirect model + constructed counts)"""
import csv, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rv32_asm import assemble, to_hex
import rv32i_iss, stage2_lib
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'sim_out_xsim_s2')
subprocess.run([sys.executable, os.path.join(HERE, 'gen_pipe_tests.py')], check=True)
os.makedirs(os.path.join(OUT, 'iss'), exist_ok=True)
SUITES = [('rv32i', os.path.join(ROOT, 'tests', 'directed', 'rv32i')), ('pipeline', os.path.join(ROOT, 'tests', 'directed', 'pipeline'))]
man = open(os.path.join(OUT, 'manifest_all.csv'), 'w', newline='\n'); man.write("name,expect_cause,check_gp,hexpath\n")
exp = open(os.path.join(OUT, 'expected.csv'), 'w', newline='\n')
exp.write("name,suite,iss_cause,instret,model_stalls,model_redirects,exp_stalls,exp_redirects\n")
bad = 0
for suite, d in SUITES:
    perf = {}
    if suite == 'pipeline':
        for r in csv.DictReader(open(os.path.join(d, 'expected_perf.csv'))): perf[r['name']] = (r['exp_stalls'], r['exp_redirects'])
    for r in csv.DictReader(open(os.path.join(d, 'manifest.csv'))):
        n = r['name']; mem = assemble(open(os.path.join(d, n + '.s')).read())
        hexf = os.path.join(d, n + '.hex'); open(hexf, 'w', newline='\n').write(to_hex(mem))
        words = [mem.get(4 * i, 0) for i in range(max(mem) // 4 + 1)]
        cause, x, tr, foot, oob, cnt = rv32i_iss.run(words)
        txt = "\n".join(tr + foot) + "\n"
        open(os.path.join(OUT, 'iss', n + '.iss.trace'), 'w', newline='\n').write(txt)
        ok = cause == int(r['expect_cause']) and (r['check_gp'] != '1' or x[3] == 1) and oob == 0
        if not ok: bad += 1; print(f"ISS expectation mismatch: {n} cause={cause} gp={x[3]:#x}")
        inst, st, rd = stage2_lib.perf_model(txt, words)
        cs, cr = perf.get(n, ('-1', '-1'))
        rel = os.path.relpath(hexf, ROOT).replace('\\', '/')
        man.write(f"{n},{r['expect_cause']},{r['check_gp']},{rel}\n")
        exp.write(f"{n},{suite},{cause},{inst},{st},{rd},{cs},{cr}\n")
man.close(); exp.close()
print(f"prepared {sum(1 for _ in open(os.path.join(OUT, 'manifest_all.csv'))) - 1} tests in {OUT}; ISS mismatches: {bad}")
sys.exit(1 if bad else 0)

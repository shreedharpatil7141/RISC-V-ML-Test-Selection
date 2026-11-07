#!/usr/bin/env python3
"""Evaluate Stage 3.3 traces, units, performance, and all Stage 2 coverage events."""
import csv, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import stage2_lib as L
sim_dir, label = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(os.path.join(sim_dir, 'manifest_all.csv'), newline='')))
expected = {r['name']:r for r in csv.DictReader(open(os.path.join(sim_dir, 'expected.csv'), newline=''))}
lines, functional_ok, bad, ncov = L.evaluate(sim_dir, rows, expected, label)
out = [f"Stage 3.3 pipeline M regression  {time.strftime('%Y-%m-%d %H:%M:%S')}  simulator={label}", ""]
unit_ok = True
for fn, pat, name in (('units_s1.log', r"UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)", 'Stage 1 unit TB'),
                      ('units_md.log', r"MD_UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)", 'M arithmetic unit TB'),
                      ('units_decoder_m.log', r"DECODER_M_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)", 'M decoder exhaustive unit TB'),
                      ('units_pipe.log', r"PIPE_UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)", 'Pipeline unit TB')):
    t = L.read(os.path.join(sim_dir, fn)); m = re.search(pat, t or '')
    if m:
        ok = m.group(1) == 'PASS' and int(m.group(3)) == 0
        out.append(f"{name}: {m.group(1)} checks={m.group(2)} errors={m.group(3)}")
        unit_ok &= ok
    else:
        out.append(f"{name}: NO RESULT ({fn} missing or malformed)"); unit_ok = False
out += [''] + lines
final = functional_ok and unit_ok
out.append(f"STAGE3_3_REGRESSION_{label.upper()} {'PASS' if final else 'FAIL'}")
report = '\n'.join(out) + '\n'
print(report, end='')
if len(sys.argv) > 3:
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[3])), exist_ok=True)
    open(sys.argv[3], 'w', newline='\n').write(report)
sys.exit(0 if final else 1)

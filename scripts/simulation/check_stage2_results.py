#!/usr/bin/env python3
"""Evaluate a Stage-2 regression directory (Verilator or XSim layout) and print/write the report.
Usage: python check_stage2_results.py <sim_dir> <simulator_label> [report_path]
Expected files per test <n>: <n>.s1.log/.s1.trace (Stage 1 golden core), <n>.pipe.log/.pipe.trace, iss/<n>.iss.trace.
Unit-test logs (optional): units_s1.log (UNIT_RESULT), units_pipe.log (PIPE_UNIT_RESULT).
Exit code 0 only if every test passes all five checks, unit tests pass and all 16 coverage events are hit."""
import csv, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import stage2_lib as L
sim_dir, label = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(os.path.join(sim_dir, 'manifest_all.csv'))))
expected = {r['name']: r for r in csv.DictReader(open(os.path.join(sim_dir, 'expected.csv')))}
lines, ok, bad, ncov = L.evaluate(sim_dir, rows, expected, label)
out = [f"Stage 2 regression  {time.strftime('%Y-%m-%d %H:%M:%S')}  simulator={label}", ""]
unit_ok = True
for fn, pat, name in (('units_s1.log', r"UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)", 'Stage 1 unit TB (regression)'),
                      ('units_pipe.log', r"PIPE_UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)", 'Stage 2 pipe unit TB')):
    t = L.read(os.path.join(sim_dir, fn)); m = re.search(pat, t or '')
    if m: out.append(f"{name}: {m.group(1)} checks={m.group(2)} errors={m.group(3)}"); unit_ok &= m.group(1) == 'PASS'
    else: out.append(f"{name}: NO RESULT ({fn} missing or malformed)"); unit_ok = False
out += [""] + lines
final = ok and unit_ok
out.append(f"STAGE2_REGRESSION_{label.upper()} {'PASS' if final else 'FAIL'}")
print("\n".join(out))
if len(sys.argv) > 3: open(sys.argv[3], 'w', newline='\n').write("\n".join(out) + "\n")
sys.exit(0 if final else 1)

#!/usr/bin/env python3
"""Prepare additive Stage 3.3 inputs without rewriting checked-in test images."""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rv32_asm import assemble, to_hex
import rv32i_iss, stage2_lib
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'sim_out_stage3_3')
SUITES = [('rv32i', 'rv32i'), ('pipeline', 'pipeline'), ('pipeline_m', 'pipeline_m')]
os.makedirs(os.path.join(OUT, 'iss'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'hex'), exist_ok=True)
bad = total = 0
with open(os.path.join(OUT, 'manifest_all.csv'), 'w', newline='') as mf, \
     open(os.path.join(OUT, 'expected.csv'), 'w', newline='') as ef:
    man = csv.writer(mf, lineterminator='\n'); man.writerow(['name','expect_cause','check_gp','hexpath'])
    exp = csv.writer(ef, lineterminator='\n'); exp.writerow(['name','suite','iss_cause','instret','model_stalls','model_redirects','exp_stalls','exp_redirects'])
    for suite, folder in SUITES:
        d = os.path.join(ROOT, 'tests', 'directed', folder)
        perf = {}
        pp = os.path.join(d, 'expected_perf.csv')
        if os.path.isfile(pp):
            perf = {r['name']:(r['exp_stalls'], r['exp_redirects']) for r in csv.DictReader(open(pp, newline=''))}
        for row in csv.DictReader(open(os.path.join(d, 'manifest.csv'), newline='')):
            total += 1; name = row['name']
            mem = assemble(open(os.path.join(d, name + '.s'), encoding='utf-8').read())
            hexfile = os.path.join(OUT, 'hex', name + '.hex')
            open(hexfile, 'w', newline='\n').write(to_hex(mem))
            words = [mem.get(4*i, 0) for i in range(max(mem)//4 + 1)]
            cause, regs, trace, footer, oob, _ = rv32i_iss.run(words)
            open(os.path.join(OUT, 'iss', name + '.iss.trace'), 'w', newline='\n').write('\n'.join(trace + footer) + '\n')
            check_gp = row['check_gp']
            if cause != int(row['expect_cause']) or (check_gp == '1' and regs[3] != 1) or oob:
                bad += 1; print(f"ISS expectation mismatch: {name}: cause={cause}, gp={regs[3]:#x}, oob={oob}")
            inst, stalls, redirects = stage2_lib.perf_model('\n'.join(trace + footer), words)
            exps = perf.get(name, ('-1','-1'))
            relhex = os.path.relpath(hexfile, ROOT).replace('\\','/')
            man.writerow([name, row['expect_cause'], check_gp, relhex])
            exp.writerow([name, suite, cause, inst, stalls, redirects, *exps])
print(f"STAGE3_3_PREPARED tests={total} iss_mismatches={bad} out={OUT}")
sys.exit(1 if bad else 0)

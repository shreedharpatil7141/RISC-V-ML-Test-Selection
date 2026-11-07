#!/usr/bin/env python3
"""Stage 3.1 ISS-level validation (no RTL):
  1. every test in tests/directed/{rv32i,m_extension,pipeline} assembles, runs on the ISS and meets its manifest
     expectation (halt cause, gp==1 for self-checking tests, no out-of-range access)
  2. exhaustive decode-legality sweep of the OP opcode: all 128 funct7 x 8 funct3 combinations
     legal set must be exactly {f7=0000000 all f3} U {f7=0100000, f3 in (0,5)} U {f7=0000001 all f3 (M)}
  3. M instructions leave unrelated state untouched and retire exactly once"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rv32_asm import assemble, to_hex
import rv32i_iss
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
bad = 0
def words_of(mem): return [mem.get(4 * i, 0) for i in range(max(mem) // 4 + 1)]
total = 0
for suite in ('rv32i', 'm_extension', 'pipeline'):
    d = os.path.join(ROOT, 'tests', 'directed', suite); n = ok_n = 0
    for row in csv.DictReader(open(os.path.join(d, 'manifest.csv'))):
        mem = assemble(open(os.path.join(d, row['name'] + '.s')).read())
        cause, x, tr, foot, oob, cnt = rv32i_iss.run(words_of(mem))
        ok = cause == int(row['expect_cause']) and (row['check_gp'] != '1' or x[3] == 1) and oob == 0
        n += 1; ok_n += ok
        if not ok: print(f"FAIL {suite}/{row['name']} cause={cause} gp={x[3]:#x} oob={oob}")
    print(f"ISS suite {suite:12s}: {ok_n}/{n} as expected"); bad += n - ok_n; total += n
# 2. exhaustive legality sweep
bad2 = 0
for f7 in range(128):
    for f3 in range(8):
        insn = (f7 << 25) | (2 << 20) | (1 << 15) | (f3 << 12) | (5 << 7) | 0x33
        cause, x, tr, foot, oob, cnt = rv32i_iss.run([insn])
        legal = cnt == 1
        exp = (f7 == 0) or (f7 == 0x20 and f3 in (0, 5)) or (f7 == 1)
        if legal != exp or (not legal and cause != 3): bad2 += 1; print(f"LEGALITY MISMATCH f7={f7:07b} f3={f3}")
print(f"ISS OP-opcode legality sweep: {1024 - bad2}/1024 correct"); bad += bad2
# 3. M op: exactly one retirement, only rd changes
bad3 = 0
for f3 in range(8):
    insn = (1 << 25) | (2 << 20) | (1 << 15) | (f3 << 12) | (5 << 7) | 0x33
    prog = assemble("li x1, -7\nli x2, 2\n.word 0x%08x\nli x6, 1\n" % insn)
    cause, x, tr, foot, oob, cnt = rv32i_iss.run(words_of(prog))
    exp5 = rv32i_iss.md_exec(f3, 0xFFFFFFF9, 2)
    if not (cnt == 4 and x[5] == exp5 and x[1] == 0xFFFFFFF9 and x[2] == 2 and x[6] == 1 and cause == 3): bad3 += 1; print("M single-op check failed f3", f3)
print(f"ISS M single-instruction checks: {8 - bad3}/8"); bad += bad3
print("ISS_VALIDATE_STAGE3", "PASS" if not bad else f"FAIL({bad})", f"tests={total}")
sys.exit(bad != 0)

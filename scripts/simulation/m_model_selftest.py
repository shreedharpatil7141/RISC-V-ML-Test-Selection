#!/usr/bin/env python3
"""Stage 3.1 arithmetic cross-validation. Three independent sources must agree:
  (1) hand-verified known-answer vectors (derivations in comments)
  (2) rv32i_iss.md_exec  (big-int / magnitude formulation)
  (3) m_model.md_ref     (shift-add multiply + restoring division)
plus algebraic identities (dividend = divisor*quotient + remainder, product reconstruction)."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv32i_iss as iss, m_model as mm
F3 = {n: i for i, n in enumerate(mm.OPS)}
MIN, MAXP, ALL1 = 0x80000000, 0x7FFFFFFF, 0xFFFFFFFF
def n(x): return x & ALL1      # negative literal -> 32-bit pattern

# (op, a, b, expected) - each line derived by hand from the spec, not by running code
KAT = [
 # (-1)*(-1)=1 ; unsigned (2^32-1)^2 = 2^64-2^33+1 -> high word 0xFFFFFFFE ; (-1)*(2^32-1) = -2^32+1 -> high word -1
 ('mul', ALL1, ALL1, 1), ('mulh', ALL1, ALL1, 0), ('mulhu', ALL1, ALL1, 0xFFFFFFFE), ('mulhsu', ALL1, ALL1, ALL1),
 # (-2^31)^2 = 2^62 -> low 0, high 0x40000000
 ('mul', MIN, MIN, 0), ('mulh', MIN, MIN, 0x40000000), ('mulhu', MIN, MIN, 0x40000000), ('mulhsu', MIN, MIN, 0xC0000000),
 # MIN * -1 = 2^31: low 0x80000000, signed high 0; MIN*(2^32-1) unsigned = 2^63-2^31 -> high 0x7FFFFFFF; MIN(signed)*(2^32-1) = -2^63+2^31 -> high 0x80000000
 ('mul', MIN, ALL1, MIN), ('mulh', MIN, ALL1, 0), ('mulhu', MIN, ALL1, 0x7FFFFFFF), ('mulhsu', MIN, ALL1, 0x80000000),
 # (2^31-1)^2 = 2^62-2^32+1 -> low 1, high 0x3FFFFFFF
 ('mul', MAXP, MAXP, 1), ('mulh', MAXP, MAXP, 0x3FFFFFFF), ('mulhu', MAXP, MAXP, 0x3FFFFFFF), ('mulhsu', MAXP, MAXP, 0x3FFFFFFF),
 ('mul', 0x10000, 0x10000, 0), ('mulhu', 0x10000, 0x10000, 1), ('mulh', n(-0x10000), 0x10000, ALL1), ('mulhsu', n(-0x10000), 0x10000, ALL1),
 # division truncates toward zero; remainder has the dividend's sign
 ('div', n(-7), 2, n(-3)), ('rem', n(-7), 2, n(-1)),
 ('div', 7, n(-2), n(-3)), ('rem', 7, n(-2), 1),
 ('div', n(-7), n(-2), 3), ('rem', n(-7), n(-2), n(-1)),
 ('div', 7, 2, 3), ('rem', 7, 2, 1),
 # unsigned view of -7 = 0xFFFFFFF9 = 2*0x7FFFFFFC + 1
 ('divu', n(-7), 2, 0x7FFFFFFC), ('remu', n(-7), 2, 1),
 # division by zero: quotient all ones, remainder = dividend (spec Table 1)
 ('div', 5, 0, ALL1), ('divu', 5, 0, ALL1), ('rem', 5, 0, 5), ('remu', 5, 0, 5),
 ('div', MIN, 0, ALL1), ('rem', MIN, 0, MIN), ('divu', 0, 0, ALL1), ('rem', 0, 0, 0), ('remu', n(-1), 0, ALL1),
 # signed overflow: MIN / -1 -> quotient MIN, remainder 0 ; unsigned view of same bits is ordinary
 ('div', MIN, ALL1, MIN), ('rem', MIN, ALL1, 0), ('divu', MIN, ALL1, 0), ('remu', MIN, ALL1, MIN),
 ('div', n(-1), MIN, 0), ('rem', n(-1), MIN, ALL1), ('div', MIN, MIN, 1), ('rem', MIN, MIN, 0),
 ('div', MIN, 1, MIN), ('rem', MIN, 1, 0), ('div', MIN, 2, 0xC0000000), ('rem', MIN, 3, n(-2)),
 ('divu', ALL1, 1, ALL1), ('divu', 1, ALL1, 0), ('remu', 1, ALL1, 1), ('div', 0, n(-5), 0), ('rem', 0, n(-5), 0),
]
bad = 0
def fail(msg):
    global bad; bad += 1
    if bad < 20: print("FAIL:", msg)
for op, a, b, e in KAT:
    gi, gm = iss.md_exec(F3[op], a, b), mm.md_ref(op, a, b)
    if gi != e: fail(f"ISS {op} {a:#x} {b:#x} got {gi:#x} exp {e:#x}")
    if gm != e: fail(f"MODEL {op} {a:#x} {b:#x} got {gm:#x} exp {e:#x}")
checks = len(KAT) * 2
CORN = [0, 1, 2, 3, 7, 0xFFFF, 0x10000, MAXP, MIN, MIN + 1, ALL1, n(-2), n(-3), n(-7), 0x12345678, 0xA5A5A5A5, 0xDEADBEEF]
rng = random.Random(20260301)
vecs = [(a, b) for a in CORN for b in CORN] + [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(150000)] + \
       [(rng.getrandbits(32), rng.getrandbits(rng.randrange(1, 17))) for _ in range(50000)]       # small divisors
s32 = iss.s32
for a, b in vecs:
    for op in mm.OPS:
        gi, gm = iss.md_exec(F3[op], a, b), mm.md_ref(op, a, b); checks += 1
        if gi != gm: fail(f"ISS!=MODEL {op} {a:#x} {b:#x}: {gi:#x} vs {gm:#x}")
    # identities (independent of both formulations)
    checks += 2
    q, r = iss.md_exec(5, a, b), iss.md_exec(7, a, b)
    if b != 0 and (q * b + r) != a: fail(f"unsigned identity {a:#x}/{b:#x}")
    qs, rs = s32(iss.md_exec(4, a, b)), s32(iss.md_exec(6, a, b))
    if b != 0 and not (s32(a) == -(1 << 31) and s32(b) == -1):
        if qs * s32(b) + rs != s32(a): fail(f"signed identity {a:#x}/{b:#x}")
        if rs != 0 and (rs < 0) != (s32(a) < 0): fail(f"remainder sign {a:#x}/{b:#x}")
        if abs(rs) >= abs(s32(b)): fail(f"remainder magnitude {a:#x}/{b:#x}")
    checks += 4
    lo, hs, hsu, hu = (iss.md_exec(i, a, b) for i in (0, 1, 2, 3))
    if (hu << 32) | lo != a * b: fail(f"unsigned product rebuild {a:#x}*{b:#x}")
    if ((hs << 32) | lo) != (s32(a) * s32(b)) & ((1 << 64) - 1): fail(f"signed product rebuild {a:#x}*{b:#x}")
    if ((hsu << 32) | lo) != (s32(a) * b) & ((1 << 64) - 1): fail(f"su product rebuild {a:#x}*{b:#x}")
print(f"M_MODEL_SELFTEST {'PASS' if bad == 0 else f'FAIL({bad})'} checks={checks} known_answer_vectors={len(KAT)} vector_pairs={len(vecs)}")
sys.exit(bad != 0)

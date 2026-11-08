#!/usr/bin/env python3
"""Independent RV32M reference model for the TEST GENERATOR (Stage 3).
Deliberately uses a different formulation from rv32i_iss.md_exec:
  * multiplication: bitwise shift-and-add over 64-bit two's-complement operands (no '*' operator)
  * division: bitwise restoring long division on magnitudes (no '//', '%', 'divmod')
Semantics: RISC-V Unprivileged ISA, "M" Extension v2.0 (see documentation/architecture/isa_specification.md)."""
M32 = 0xFFFFFFFF
M64 = (1 << 64) - 1
OPS = ['mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu', 'rem', 'remu']

def _mul64(x, y):
    """low 64 bits of x*y for 64-bit patterns x, y, by shift-and-add"""
    acc = 0
    for i in range(64):
        if (y >> i) & 1: acc = (acc + (x << i)) & M64
    return acc

def _sext64(v): return (v | ~M32) & M64 if v & 0x80000000 else v       # 32-bit pattern -> 64-bit sign-extended pattern

def _udiv(n, d):
    """restoring division, d != 0, 32-bit magnitudes -> (q, r)"""
    q = r = 0
    for i in range(31, -1, -1):
        r = (r << 1) | ((n >> i) & 1)
        if r >= d: r -= d; q |= 1 << i
    return q, r

def _neg32(v): return ((~v) + 1) & M32
def _mag(v): return _neg32(v) if v & 0x80000000 else v                 # |v| as unsigned 32-bit (MIN -> 0x80000000)

def md_ref(op, a, b):
    """op: mnemonic string; a=rs1, b=rs2 raw 32-bit patterns -> 32-bit result"""
    a &= M32; b &= M32
    if op == 'mul':    return _mul64(a, b) & M32
    if op == 'mulh':   return (_mul64(_sext64(a), _sext64(b)) >> 32) & M32
    if op == 'mulhsu': return (_mul64(_sext64(a), b) >> 32) & M32
    if op == 'mulhu':  return (_mul64(a, b) >> 32) & M32
    if op in ('divu', 'remu'):
        if b == 0: return M32 if op == 'divu' else a
        q, r = _udiv(a, b); return q if op == 'divu' else r
    # signed
    if b == 0: return M32 if op == 'div' else a
    if a == 0x80000000 and b == M32: return a if op == 'div' else 0
    q, r = _udiv(_mag(a), _mag(b))
    neg_q = bool(a & 0x80000000) != bool(b & 0x80000000)
    if op == 'div': return _neg32(q) if neg_q else q
    return _neg32(r) if (a & 0x80000000) else r                          # remainder takes dividend's sign

#!/usr/bin/env python3
"""Explicit-mnemonic mixed-width assembler for RV32IMC software validation.

No automatic compression or relaxation is performed.  Legacy programs can be
assembled with `--mode rv32im`; C mnemonics require `--mode rv32imc`.
Output is packed little-endian into 32-bit $readmemh words.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import rv32_asm as base


def _check(cond, msg):
    if not cond:
        raise ValueError(msg)


def _signed(v, bits, name):
    lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    _check(lo <= v <= hi, f"{name} out of range [{lo},{hi}]: {v}")
    return v & ((1 << bits) - 1)


def _regp(text):
    r = base.reg(text)
    _check(8 <= r <= 15, f"compressed register must be x8-x15, got x{r}")
    return r - 8


def _memop(text):
    m = re.fullmatch(r"\s*(-?(?:0[xX][0-9a-fA-F]+|\d+))\s*\(\s*([\w]+)\s*\)\s*", text)
    _check(m is not None, f"expected offset(base), got {text!r}")
    return int(m.group(1), 0), base.reg(m.group(2))


def _target(token, pc, labels):
    return int(token, 0) if base.is_num(token) else labels[token] - pc


def encode_c(mn, ops, pc, labels):
    """Encode one explicit RV32C v2.0 integer mnemonic into a 16-bit value."""
    mn = mn.lower()
    if mn.startswith("c."):
        mn = mn[2:]
    q0, q1, q2 = 0, 1, 2
    def ci(f3, rd, imm, quadrant=q1):
        v = _signed(imm, 6, "CI immediate")
        return (f3 << 13) | (((v >> 5) & 1) << 12) | (rd << 7) | ((v & 31) << 2) | (quadrant << 0) | 1
    def cj(f3, offset):
        v = _signed(offset, 12, "CJ offset")
        _check(offset % 2 == 0, "CJ offset must be 2-byte aligned")
        return (f3 << 13) | (((v >> 11) & 1) << 12) | (((v >> 4) & 1) << 11) | (((v >> 8) & 3) << 9) | (((v >> 10) & 1) << 8) | (((v >> 6) & 1) << 7) | (((v >> 7) & 1) << 6) | (((v >> 1) & 7) << 3) | (((v >> 5) & 1) << 2) | 1
    def cb(f3, rs1p, offset):
        v = _signed(offset, 9, "CB offset")
        _check(offset % 2 == 0, "CB offset must be 2-byte aligned")
        return (f3 << 13) | (((v >> 8) & 1) << 12) | (((v >> 3) & 3) << 10) | (rs1p << 7) | (((v >> 6) & 3) << 5) | (((v >> 1) & 3) << 3) | (((v >> 5) & 1) << 2) | 1
    def memops():
        _check(len(ops) == 2, "expected register, offset(base)")
        offset, rs1 = _memop(ops[1])
        return base.reg(ops[0]), offset, rs1

    if mn == "nop":
        _check(not ops, "c.nop takes no operands")
        return 0x0001
    if mn == "addi":
        _check(len(ops) == 2, "expected rd, imm")
        return ci(0, base.reg(ops[0]), int(ops[1], 0))
    if mn == "addi4spn":
        _check(len(ops) == 2, "expected rd', nzuimm")
        rd, imm = _regp(ops[0]), int(ops[1], 0)
        _check(4 <= imm <= 1020 and imm % 4 == 0, "C.ADDI4SPN immediate must be nonzero, 4-byte scaled, and <=1020")
        v = imm
        return ((v >> 6) & 15) << 7 | ((v >> 4) & 3) << 11 | ((v >> 2) & 1) << 6 | ((v >> 3) & 1) << 5 | rd << 2
    if mn in ("lw", "sw"):
        r, off, base_r = memops()
        _check(0 <= off <= 124 and off % 4 == 0, f"C.{mn.upper()} offset must be 4-byte scaled in [0,124]")
        _check(8 <= base_r <= 15, "C.LW/C.SW base must be x8-x15")
        rp, bp = _regp(ops[0]), base_r - 8
        return (2 if mn == "lw" else 6) << 13 | ((off >> 3) & 7) << 10 | bp << 7 | ((off >> 2) & 1) << 6 | ((off >> 6) & 1) << 5 | rp << 2
    if mn == "addi16sp":
        _check(len(ops) == 1, "expected signed byte immediate")
        imm = int(ops[0], 0)
        _check(-512 <= imm <= 496 and imm != 0 and imm % 16 == 0, "C.ADDI16SP immediate must be nonzero, 16-byte scaled, in [-512,496]")
        v = imm & 0x3FF
        return 0x6101 | ((v >> 9) & 1) << 12 | ((v >> 4) & 1) << 6 | ((v >> 6) & 1) << 5 | ((v >> 7) & 3) << 3 | ((v >> 5) & 1) << 2
    if mn == "li":
        _check(len(ops) == 2, "expected rd, imm")
        return ci(2, base.reg(ops[0]), int(ops[1], 0))
    if mn == "lui":
        _check(len(ops) == 2, "expected rd, signed six-bit immediate")
        rd, imm = base.reg(ops[0]), int(ops[1], 0)
        _check(rd != 2 and -32 <= imm <= 31 and imm != 0, "C.LUI requires rd!=x2 and nonzero signed 6-bit immediate (rd=x0 is a HINT)")
        return ci(3, rd, imm)
    if mn in ("srli", "srai"):
        _check(len(ops) == 2, "expected rd', shamt")
        rp, shamt = _regp(ops[0]), int(ops[1], 0)
        _check(0 <= shamt <= 31, "RV32 C.SRLI/C.SRAI shamt must be 0..31 (zero is a HINT)")
        return 0x8001 | (0 if mn == "srli" else 0x400) | ((shamt >> 5) & 1) << 12 | ((0 if mn == "srli" else 1) << 10) | rp << 7 | (shamt & 31) << 2
    if mn == "andi":
        _check(len(ops) == 2, "expected rd', signed immediate")
        imm = int(ops[1], 0)
        _check(-32 <= imm <= 31, "C.ANDI immediate must be signed 6-bit")
        return 0x8801 | (((imm & 0x20) != 0) << 12) | _regp(ops[0]) << 7 | ((imm & 31) << 2)
    if mn in ("sub", "xor", "or", "and"):
        _check(len(ops) == 2, "expected rd', rs2'")
        code = {"sub": 0, "xor": 1, "or": 2, "and": 3}[mn]
        return 0x8C01 | (_regp(ops[0]) << 7) | (code << 5) | (_regp(ops[1]) << 2)
    if mn == "j" or mn == "jal":
        _check(len(ops) == 1, "expected target")
        return cj(5 if mn == "j" else 1, _target(ops[0], pc, labels))
    if mn in ("beqz", "bnez"):
        _check(len(ops) == 2, "expected rs1', target")
        return cb(6 if mn == "beqz" else 7, _regp(ops[0]), _target(ops[1], pc, labels))
    if mn == "slli":
        _check(len(ops) == 2, "expected rd, shamt")
        rd, shamt = base.reg(ops[0]), int(ops[1], 0)
        _check(0 <= shamt <= 31, "RV32 C.SLLI shamt must be 0..31")
        return 0x0002 | (rd << 7) | ((shamt & 31) << 2)
    if mn == "lwsp":
        _check(len(ops) == 2, "expected rd, offset")
        rd, off = base.reg(ops[0]), int(ops[1], 0)
        _check(rd != 0 and 0 <= off <= 252 and off % 4 == 0, "C.LWSP requires rd!=x0 and offset 0..252 scaled by 4")
        return 0x4002 | (rd << 7) | ((off >> 5) & 1) << 12 | ((off >> 2) & 7) << 4 | ((off >> 6) & 3) << 2
    if mn == "swsp":
        _check(len(ops) == 2, "expected rs2, offset")
        rs2, off = base.reg(ops[0]), int(ops[1], 0)
        _check(0 <= off <= 252 and off % 4 == 0, "C.SWSP offset must be 0..252 scaled by 4")
        return 0xC002 | ((off >> 2) & 15) << 9 | ((off >> 6) & 3) << 7 | rs2 << 2
    if mn == "jr":
        _check(len(ops) == 1, "expected rs1")
        rs1 = base.reg(ops[0]); _check(rs1 != 0, "C.JR rs1 cannot be x0")
        return 0x8002 | rs1 << 7
    if mn == "jalr":
        _check(len(ops) == 1, "expected rs1")
        rs1 = base.reg(ops[0]); _check(rs1 != 0, "C.JALR rs1 cannot be x0")
        return 0x9002 | rs1 << 7
    if mn == "mv":
        _check(len(ops) == 2, "expected rd, rs2")
        return 0x8002 | base.reg(ops[0]) << 7 | base.reg(ops[1]) << 2
    if mn == "add":
        _check(len(ops) == 2, "expected rd, rs2")
        return 0x9002 | base.reg(ops[0]) << 7 | base.reg(ops[1]) << 2
    if mn == "ebreak":
        _check(not ops, "c.ebreak takes no operands")
        return 0x9002
    raise ValueError(f"unsupported compressed mnemonic c.{mn}")


def _parse(source):
    items = []
    for line_no, raw in enumerate(source.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        while True:
            m = re.match(r"^([A-Za-z_.][\w.]*):\s*(.*)$", line)
            if not m:
                break
            items.append(("label", m.group(1), [], line_no))
            line = m.group(2)
        if not line:
            continue
        parts = line.split(None, 1)
        items.append(("statement", parts[0].lower(), [x.strip() for x in parts[1].split(",")] if len(parts) > 1 else [], line_no))
    return items


def _size(mn, ops, c_enabled):
    if mn in (".2byte", ".hword", ".half"):
        return 2 * len(ops)
    if mn in (".word",):
        return 4 * len(ops)
    if mn == ".org":
        return 0
    if mn.startswith("c."):
        if not c_enabled:
            raise ValueError(f"{mn} requires explicit RV32IMC mode")
        return 2
    if mn == "la":
        return 8
    if mn == "li":
        return 4 * base.li_size(ops[1])
    return 4


def assemble_bytes(source, c_enabled=False):
    """Return `{byte_address: byte}` for an explicitly selected ISA mode."""
    items = _parse(source)
    labels, pc = {}, 0
    for kind, mn, ops, line_no in items:
        if kind == "label":
            if mn in labels:
                raise ValueError(f"line {line_no}: duplicate label {mn}")
            labels[mn] = pc
        elif mn == ".org":
            _check(len(ops) == 1, f"line {line_no}: .org needs one address")
            pc = int(ops[0], 0)
            _check(pc >= 0, f"line {line_no}: negative .org")
        else:
            pc += _size(mn, ops, c_enabled)
    memory, pc = {}, 0

    def emit(value, width, line_no):
        nonlocal pc
        _check(pc % 2 == 0, f"line {line_no}: instruction/data halfword begins at odd address {pc:#x}")
        for j in range(width):
            memory[pc + j] = (value >> (8 * j)) & 0xFF
        pc += width

    def ordinary(mn, ops, line_no):
        resolved = list(ops)
        if mn in base.BR_OPS:
            resolved[-1] = str(_target(resolved[-1], pc, labels))
        elif mn in ("j", "jal"):
            idx = 0 if len(resolved) == 1 else 1
            resolved[idx] = str(_target(resolved[idx], pc, labels))
        elif mn in ("beqz", "bnez"):
            resolved[-1] = str(_target(resolved[-1], pc, labels))
        try:
            encoded = base.assemble(mn + (" " + ", ".join(resolved) if resolved else ""))
        except Exception as exc:
            raise ValueError(f"line {line_no}: {mn} {ops}: {exc}") from exc
        n = _size(mn, ops, c_enabled) // 4
        return [encoded.get(4 * i, 0) for i in range(n)]

    for kind, mn, ops, line_no in items:
        if kind == "label":
            continue
        try:
            if mn == ".org":
                pc = int(ops[0], 0)
            elif mn in (".2byte", ".hword", ".half"):
                for op in ops:
                    emit(int(op, 0) & 0xFFFF, 2, line_no)
            elif mn == ".word":
                for op in ops:
                    emit(int(op, 0) & 0xFFFFFFFF, 4, line_no)
            elif mn.startswith("c."):
                emit(encode_c(mn, ops, pc, labels), 2, line_no)
            elif mn == "la":
                rd = base.reg(ops[0]); value = labels[ops[1]] & 0xFFFFFFFF
                # Keep the legacy fixed two-instruction address expansion.
                # split_li accepts an integer; stringifying here breaks every
                # symbolic `la` because its first operation is a bit mask.
                hi, lo = base.split_li(value)
                if hi is None:
                    hi, lo = 0, lo
                words = [base.enc_u(hi, rd, 0x37), base.enc_i(lo, rd, 0, rd, 0x13)]
                for w in words:
                    emit(w, 4, line_no)
            else:
                for w in ordinary(mn, ops, line_no):
                    emit(w, 4, line_no)
        except Exception as exc:
            if isinstance(exc, ValueError) and str(exc).startswith(f"line {line_no}:"):
                raise
            raise ValueError(f"line {line_no}: {mn} {ops}: {exc}") from exc
    return memory


def to_words(byte_memory):
    """Pack byte-addressed image into little-endian 32-bit words."""
    if not byte_memory:
        return []
    words = []
    for base_addr in range(0, max(byte_memory) + 1, 4):
        words.append(sum((byte_memory.get(base_addr + i, 0) & 0xFF) << (8 * i) for i in range(4)))
    return words


def to_hex(byte_memory):
    return "".join(f"{w:08x}\n" for w in to_words(byte_memory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("rv32im", "rv32imc"), help="ISA mode is always explicit")
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    with open(args.source, encoding="utf-8") as src:
        image = assemble_bytes(src.read(), c_enabled=args.mode == "rv32imc")
    with open(args.output, "w", newline="\n", encoding="ascii") as dst:
        dst.write(to_hex(image))
    print(f"RV32C_ASM mode={args.mode} bytes={len(image)} words={len(to_words(image))}")


if __name__ == "__main__":
    main()

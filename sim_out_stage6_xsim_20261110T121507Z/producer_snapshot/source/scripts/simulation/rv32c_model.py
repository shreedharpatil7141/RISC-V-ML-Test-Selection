#!/usr/bin/env python3
"""Software-only RV32C v2.0 integer decoder used by the independent ISS.

This module implements only C/Zca integer forms for RV32.  It contains no RTL
interfaces and does not use the assembler's encoders.  Floating-point,
RV64-only, Zcb/Zcmp/Zcmt and custom encodings are never accepted.
"""
from dataclasses import dataclass

MASK32 = 0xFFFFFFFF


def sx(value, width):
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


def enc_i(imm, rs1, funct3, rd, opcode=0x13):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def enc_r(rs2, rs1, funct3, rd, funct7=0, opcode=0x33):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def enc_s(imm, rs2, rs1, funct3=2):
    imm &= 0xFFF
    return ((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | ((imm & 31) << 7) | 0x23


def enc_b(imm, rs2, rs1, funct3):
    imm &= 0x1FFF
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (((imm >> 1) & 15) << 8) | (((imm >> 11) & 1) << 7) | 0x63


def enc_j(imm, rd):
    imm &= 0x1FFFFF
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F


@dataclass(frozen=True)
class Decoded:
    status: str                 # legal, hint, illegal, or long
    expanded: int = 0
    mnemonic: str = ""
    reason: str = ""


def instruction_length(prefix):
    """Decode the manual's length-prefix convention.

    16/32 are the frozen standard lengths. The >32 encodings remain reserved
    proposal space, but their prefix-declared length can still be classified:
    48, 64, and 80..176 bits. None identifies the reserved >=192-bit prefix,
    whose exact length is not supplied by this 16-bit parcel.
    """
    prefix &= 0xFFFF
    if prefix & 3 != 3:
        return 16
    if (prefix >> 2) & 7 != 7:
        return 32
    if prefix & 0x3F == 0x1F:
        return 48
    if prefix & 0x7F == 0x3F:
        return 64
    if prefix & 0x7F == 0x7F:
        nnn = (prefix >> 12) & 7
        return None if nnn == 7 else 80 + 16 * nnn
    return None


def decode16(h):
    """Decode one RV32C halfword using the pinned C v2.0 field definitions."""
    h &= 0xFFFF
    if instruction_length(h) != 16:
        return Decoded("long", reason="not-a-16-bit-instruction")
    q = h & 3
    f3 = h >> 13
    rd = (h >> 7) & 31
    rs2 = (h >> 2) & 31
    rdp = 8 + ((h >> 2) & 7)
    rs1p = 8 + ((h >> 7) & 7)
    rs2p = 8 + ((h >> 2) & 7)
    ci = sx(((h >> 12) & 1) << 5 | ((h >> 2) & 31), 6)

    def legal(word, name):
        return Decoded("legal", word & MASK32, name)

    def hint(name):
        return Decoded("hint", 0x00000013, name, "architectural no-op")

    def illegal(reason):
        return Decoded("illegal", reason=reason)

    if q == 0:
        if f3 == 0:  # ADDI4SPN: unsigned nzuimm[9:2]
            imm = (((h >> 11) & 3) << 4) | (((h >> 7) & 15) << 6) | (((h >> 6) & 1) << 2) | (((h >> 5) & 1) << 3)
            if imm == 0:
                return illegal("reserved-zero-addi4spn")
            return legal(enc_i(imm, 2, 0, rdp), "c.addi4spn")
        if f3 == 2:  # LW
            imm = (((h >> 10) & 7) << 3) | (((h >> 6) & 1) << 2) | (((h >> 5) & 1) << 6)
            return legal(enc_i(imm, rs1p, 2, rdp, 0x03), "c.lw")
        if f3 == 6:  # SW
            imm = (((h >> 10) & 7) << 3) | (((h >> 6) & 1) << 2) | (((h >> 5) & 1) << 6)
            return legal(enc_s(imm, rs2p, rs1p), "c.sw")
        if f3 == 4:
            return illegal("reserved-q0-funct3-100")
        return illegal("floating-point-or-rv64-only-q0")

    if q == 1:
        if f3 == 0:  # ADDI/NOP/HINT
            if rd == 0:
                return legal(enc_i(0, 0, 0, 0), "c.nop") if ci == 0 else hint("c.nop-hint")
            if ci == 0:
                return hint("c.addi-hint")
            return legal(enc_i(ci, rd, 0, rd), "c.addi")
        if f3 == 1:  # RV32 JAL, not RV64 ADDIW
            imm = (((h >> 12) & 1) << 11) | (((h >> 11) & 1) << 4) | (((h >> 9) & 3) << 8) | (((h >> 8) & 1) << 10) | (((h >> 7) & 1) << 6) | (((h >> 6) & 1) << 7) | (((h >> 3) & 7) << 1) | (((h >> 2) & 1) << 5)
            return legal(enc_j(sx(imm, 12), 1), "c.jal")
        if f3 == 2:
            return hint("c.li-hint") if rd == 0 else legal(enc_i(ci, 0, 0, rd), "c.li")
        if f3 == 3:
            if rd == 2:
                imm = (((h >> 12) & 1) << 9) | (((h >> 6) & 1) << 4) | (((h >> 5) & 1) << 6) | (((h >> 3) & 3) << 7) | (((h >> 2) & 1) << 5)
                imm = sx(imm, 10)
                return illegal("reserved-zero-addi16sp") if imm == 0 else legal(enc_i(imm, 2, 0, 2), "c.addi16sp")
            if ci == 0:
                return illegal("reserved-zero-lui-immediate")
            if rd == 0:
                return hint("c.lui-hint")
            if rd == 2:
                return illegal("reserved-addi16sp-zero")
            return legal(((ci & 0xFFFFF) << 12) | (rd << 7) | 0x37, "c.lui")
        if f3 == 4:
            subop = (h >> 10) & 3
            if subop < 2:
                shamt = (((h >> 12) & 1) << 5) | ((h >> 2) & 31)
                if shamt & 32:
                    return illegal("custom-rv32-shift-amount-bit5")
                if shamt == 0:
                    return hint("c.srli-hint" if subop == 0 else "c.srai-hint")
                imm = (0x400 if subop == 1 else 0) | shamt
                return legal(enc_i(imm, rs1p, 5, rs1p), "c.srli" if subop == 0 else "c.srai")
            if subop == 2:
                return legal(enc_i(ci, rs1p, 7, rs1p), "c.andi")
            if (h >> 12) & 1:
                return illegal("rv64-only-or-reserved-ca-op")
            op2 = (h >> 5) & 3
            names = ("c.sub", "c.xor", "c.or", "c.and")
            f3s = (0, 4, 6, 7)
            f7 = 0x20 if op2 == 0 else 0
            return legal(enc_r(rs2p, rs1p, f3s[op2], rs1p, f7), names[op2])
        if f3 in (5, 6, 7):
            if f3 == 5:
                imm = (((h >> 12) & 1) << 11) | (((h >> 11) & 1) << 4) | (((h >> 9) & 3) << 8) | (((h >> 8) & 1) << 10) | (((h >> 7) & 1) << 6) | (((h >> 6) & 1) << 7) | (((h >> 3) & 7) << 1) | (((h >> 2) & 1) << 5)
                return legal(enc_j(sx(imm, 12), 0), "c.j")
            imm = (((h >> 12) & 1) << 8) | (((h >> 10) & 3) << 3) | (((h >> 5) & 3) << 6) | (((h >> 3) & 3) << 1) | (((h >> 2) & 1) << 5)
            return legal(enc_b(sx(imm, 9), 0, rs1p, 0 if f3 == 6 else 1), "c.beqz" if f3 == 6 else "c.bnez")

    if q == 2:
        if f3 == 0:
            shamt = (((h >> 12) & 1) << 5) | ((h >> 2) & 31)
            if shamt & 32:
                return illegal("custom-rv32-slli-bit5")
            if rd == 0 or shamt == 0:
                return hint("c.slli-hint")
            return legal(enc_i(shamt, rd, 1, rd), "c.slli")
        if f3 == 2:
            imm = (((h >> 12) & 1) << 5) | (((h >> 4) & 7) << 2) | (((h >> 2) & 3) << 6)
            return illegal("reserved-lwsp-rd-zero") if rd == 0 else legal(enc_i(imm, 2, 2, rd, 0x03), "c.lwsp")
        if f3 == 4:
            high = (h >> 12) & 1
            if not high:
                if rs2 == 0:
                    return illegal("reserved-jr-rs1-zero") if rd == 0 else legal(enc_i(0, rd, 0, 0, 0x67), "c.jr")
                return hint("c.mv-hint") if rd == 0 else legal(enc_r(rs2, 0, 0, rd), "c.mv")
            if rs2 == 0:
                if rd == 0:
                    return legal(0x00100073, "c.ebreak")
                return legal(enc_i(0, rd, 0, 1, 0x67), "c.jalr")
            return hint("c.add-hint") if rd == 0 else legal(enc_r(rs2, rd, 0, rd), "c.add")
        if f3 == 6:
            imm = (((h >> 9) & 15) << 2) | (((h >> 7) & 3) << 6)
            return legal(enc_s(imm, rs2, 2), "c.swsp")
        return illegal("floating-point-or-rv64-only-q2")

    return illegal("reserved-or-extension-disabled")

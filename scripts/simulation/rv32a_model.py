#!/usr/bin/env python3
"""Independent RV32A word-operation decoder and arithmetic reference.

This module follows the ratified A 2.1 encodings in the official
Unprivileged ISA v20260120. It intentionally has no assembler imports.
"""

MASK32 = 0xFFFFFFFF
OPCODE_AMO = 0x2F
FUNCT3_WORD = 0b010

# funct5 values from the RV32A Standard Extension encoding table.
FUNCT5_TO_NAME = {
    0b00010: "lr.w",
    0b00011: "sc.w",
    0b00001: "amoswap.w",
    0b00000: "amoadd.w",
    0b00100: "amoxor.w",
    0b01100: "amoand.w",
    0b01000: "amoor.w",
    0b10000: "amomin.w",
    0b10100: "amomax.w",
    0b11000: "amominu.w",
    0b11100: "amomaxu.w",
}
NAME_TO_FUNCT5 = {name: code for code, name in FUNCT5_TO_NAME.items()}


def s32(value):
    value &= MASK32
    return value - (1 << 32) if value & 0x80000000 else value


def decode_atomic(word):
    """Return a field dict for a legal RV32A word instruction, else None.

    A word with opcode 0101111 but an unsupported/reserved function is
    rejected by returning None. aq/rl are independent legal bits for every
    supported operation. LR requires rs2=x0.
    """
    word &= MASK32
    if (word & 0x7F) != OPCODE_AMO or ((word >> 12) & 7) != FUNCT3_WORD:
        return None
    funct5 = (word >> 27) & 0x1F
    op = FUNCT5_TO_NAME.get(funct5)
    if op is None:
        return None
    rs2 = (word >> 20) & 31
    if op == "lr.w" and rs2 != 0:
        return None
    return {
        "op": op,
        "funct5": funct5,
        "aq": (word >> 26) & 1,
        "rl": (word >> 25) & 1,
        "rs2": rs2,
        "rs1": (word >> 15) & 31,
        "rd": (word >> 7) & 31,
    }


def amo_result(op, old_word, source_word):
    """Return the 32-bit value stored by an AMO (not its rd old-value)."""
    old_word &= MASK32
    source_word &= MASK32
    if op == "amoswap.w":
        result = source_word
    elif op == "amoadd.w":
        result = old_word + source_word
    elif op == "amoxor.w":
        result = old_word ^ source_word
    elif op == "amoand.w":
        result = old_word & source_word
    elif op == "amoor.w":
        result = old_word | source_word
    elif op == "amomin.w":
        result = old_word if s32(old_word) < s32(source_word) else source_word
    elif op == "amomax.w":
        result = old_word if s32(old_word) > s32(source_word) else source_word
    elif op == "amominu.w":
        result = min(old_word, source_word)
    elif op == "amomaxu.w":
        result = max(old_word, source_word)
    else:
        raise ValueError(f"not an AMO arithmetic operation: {op}")
    return result & MASK32

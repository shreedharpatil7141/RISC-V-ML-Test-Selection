#!/usr/bin/env python3
"""Independent RV32IMC software ISS with an explicit RV32IM baseline mode.

The `rv32im` mode delegates to the released Stage 3 ISS unchanged, preserving
its seven-field architectural trace. `rv32imc` emits trace schema V2 with raw
bits, instruction length, and normalized instruction. The C decoder is a
software implementation; it has no RTL dependency.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import rv32i_iss as legacy
import rv32a_model as atomics
from rv32c_model import MASK32, decode16, instruction_length, sx

MEM_BYTES = legacy.MEM_BYTES
DIV_EXTRA_CYCLES = 33
CAUSE_ECALL, CAUSE_EBREAK, CAUSE_ILLEGAL = 1, 2, 3
CAUSE_LOAD_MIS, CAUSE_STORE_MIS, CAUSE_FETCH_MIS = 4, 5, 6
CAUSE_LOAD_ACCESS, CAUSE_STORE_ACCESS, CAUSE_FETCH_ACCESS = 7, 8, 9


def _load_image(words):
    mem = bytearray(MEM_BYTES)
    oob = 0
    for i, word in enumerate(words):
        base_addr = i * 4
        if base_addr + 4 > MEM_BYTES:
            oob += 1
            break
        mem[base_addr:base_addr + 4] = (word & MASK32).to_bytes(4, "little")
    return mem, oob


def _decode32(raw, a_enabled=False):
    """Return (legal, canonical) for the existing RV32I+M software ISA."""
    if raw & 3 != 3:
        return False, 0
    opcode = raw & 0x7F
    f3 = (raw >> 12) & 7
    f7 = raw >> 25
    rd = (raw >> 7) & 31
    rs1 = (raw >> 15) & 31
    rs2 = (raw >> 20) & 31
    if opcode in (0x37, 0x17, 0x6F):
        return True, raw
    if opcode == 0x67:
        return (f3 == 0), raw
    if opcode == 0x63:
        return (f3 in (0, 1, 4, 5, 6, 7)), raw
    if opcode == 0x03:
        return (f3 in (0, 1, 2, 4, 5)), raw
    if opcode == 0x23:
        return (f3 in (0, 1, 2)), raw
    if opcode == 0x13:
        if f3 == 1:
            return f7 == 0, raw
        if f3 == 5:
            return f7 in (0, 0x20), raw
        return f3 in (0, 2, 3, 4, 6, 7), raw
    if opcode == 0x33:
        return (f7 == 0 or (f7 == 0x20 and f3 in (0, 5)) or f7 == 1), raw
    if opcode == 0x0F:
        return f3 == 0, raw
    if opcode == 0x73:
        return raw in (0x00000073, 0x00100073), raw
    if opcode == atomics.OPCODE_AMO and a_enabled:
        return atomics.decode_atomic(raw) is not None, raw
    return False, 0


def run(words, c_enabled=False, max_steps=2_000_000, m_events=None, divider_cost_events=None,
        start_pc=0, a_enabled=False, a_events=None):
    """Return legacy six-tuple; A and C are explicit independent mode flags.

    In V2 each retired row is:
    I pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data
    Raw bits occupy the low 16 bits for a compressed instruction. Causes 7/8/9
    are model-local data/load/store/fetch access faults; they do not claim
    privileged architectural trap support. A STOP row records the raw bits
    and known length of the stopping instruction/prefix, including illegal
    encodings and access faults.
    """
    if not c_enabled and not a_enabled:
        if start_pc != 0:
            raise ValueError("nonzero start_pc is available only in explicit RV32IMC mode")
        return legacy.run(words, max_steps=max_steps, m_events=m_events)

    mem, oob = _load_image(words)
    regs = [0] * 32
    pc = start_pc & MASK32
    trace = []
    steps = 0
    cause = 0
    stop_raw, stop_ilen = 0, 0
    m_events = m_events if m_events is not None else None
    divider_cost_events = divider_cost_events if divider_cost_events is not None else None
    reservation_valid = False
    reservation_addr = 0

    def data_read(addr, n):
        if addr + n > MEM_BYTES:
            return None
        return int.from_bytes(mem[addr:addr + n], "little")

    def data_write(addr, n, value):
        if addr + n > MEM_BYTES:
            return False
        mem[addr:addr + n] = (value & ((1 << (n * 8)) - 1)).to_bytes(n, "little")
        return True

    while steps < max_steps:
        steps += 1
        stop_raw, stop_ilen = 0, 0
        if pc & 1 or (not c_enabled and pc & 3):
            cause = CAUSE_FETCH_MIS
            break
        if pc + 2 > MEM_BYTES:
            cause = CAUSE_FETCH_ACCESS
            break
        prefix = int.from_bytes(mem[pc:pc + 2], "little")
        ilen = instruction_length(prefix) if c_enabled else 32
        stop_raw, stop_ilen = prefix, (ilen // 8 if ilen else 0)
        if c_enabled and ilen == 16:
            raw = prefix
            dec = decode16(prefix)
            if dec.status == "illegal" or dec.status == "long":
                cause = CAUSE_ILLEGAL
                break
            insn = dec.expanded
            stop_raw, stop_ilen = raw, 2
            hint = dec.status == "hint"
        elif ilen == 32:
            if pc + 4 > MEM_BYTES:
                cause = CAUSE_FETCH_ACCESS
                break
            raw = int.from_bytes(mem[pc:pc + 4], "little")
            stop_raw, stop_ilen = raw, 4
            legal, insn = _decode32(raw, a_enabled=a_enabled)
            if not legal:
                cause = CAUSE_ILLEGAL
                break
            hint = False
        else:
            raw = prefix
            cause = CAUSE_ILLEGAL
            break

        opcode = insn & 0x7F
        rd = (insn >> 7) & 31
        f3 = (insn >> 12) & 7
        rs1 = (insn >> 15) & 31
        rs2 = (insn >> 20) & 31
        f7 = insn >> 25
        a, b = regs[rs1], regs[rs2]
        wr = None
        next_pc = (pc + ilen // 8) & MASK32
        store_record = (0, 0, 0)
        atom_record = None

        if hint:
            pass
        elif opcode == 0x37:
            wr = insn & 0xFFFFF000
        elif opcode == 0x17:
            wr = (pc + (insn & 0xFFFFF000)) & MASK32
        elif opcode == 0x6F:
            imm = (((insn >> 31) & 1) << 20) | (((insn >> 12) & 0xFF) << 12) | (((insn >> 20) & 1) << 11) | (((insn >> 21) & 0x3FF) << 1)
            target = (pc + sx(imm, 21)) & MASK32
            if target & 1:
                cause = CAUSE_FETCH_MIS
                break
            wr, next_pc = next_pc, target
        elif opcode == 0x67:
            target = (a + sx(insn >> 20, 12)) & MASK32 & ~1
            wr, next_pc = next_pc, target
        elif opcode == 0x63:
            imm = (((insn >> 31) & 1) << 12) | (((insn >> 7) & 1) << 11) | (((insn >> 25) & 0x3F) << 5) | (((insn >> 8) & 15) << 1)
            target = (pc + sx(imm, 13)) & MASK32
            taken = {0: a == b, 1: a != b, 4: legacy.s32(a) < legacy.s32(b), 5: legacy.s32(a) >= legacy.s32(b), 6: a < b, 7: a >= b}[f3]
            if taken:
                if target & 1:
                    cause = CAUSE_FETCH_MIS
                    break
                next_pc = target
        elif opcode == 0x03:
            addr = (a + sx(insn >> 20, 12)) & MASK32
            size = {0: 1, 1: 2, 2: 4, 4: 1, 5: 2}[f3]
            if addr % size:
                cause = CAUSE_LOAD_MIS
                break
            value = data_read(addr, size)
            if value is None:
                cause = CAUSE_LOAD_ACCESS
                break
            wr = sx(value, size * 8) & MASK32 if f3 in (0, 1, 2) else value
        elif opcode == 0x23:
            imm = ((insn >> 25) << 5) | ((insn >> 7) & 31)
            addr = (a + sx(imm, 12)) & MASK32
            size = 1 << f3
            if addr % size:
                cause = CAUSE_STORE_MIS
                break
            if not data_write(addr, size, b):
                cause = CAUSE_STORE_ACCESS
                break
            store_record = (size, addr, b & ((1 << (size * 8)) - 1))
            if reservation_valid and addr < reservation_addr + 4 and addr + size > reservation_addr:
                reservation_valid = False
        elif opcode == atomics.OPCODE_AMO:
            fields = atomics.decode_atomic(raw)
            if not a_enabled or fields is None:
                cause = CAUSE_ILLEGAL
                break
            op = fields["op"]
            addr = a & MASK32
            reservation_before = reservation_addr if reservation_valid else None
            old = None
            new = None
            sc_status = -1
            if addr & 3:
                cause = CAUSE_LOAD_MIS if op == "lr.w" else CAUSE_STORE_MIS
                break
            old = data_read(addr, 4)
            if old is None:
                cause = CAUSE_LOAD_ACCESS if op == "lr.w" else CAUSE_STORE_ACCESS
                break
            if op == "lr.w":
                wr = old
                reservation_addr, reservation_valid = addr, True
            elif op == "sc.w":
                success = reservation_valid and reservation_addr == addr
                reservation_valid = False
                sc_status = 0 if success else 1
                wr = sc_status
                if success:
                    new = b
                    if not data_write(addr, 4, new):
                        cause = CAUSE_STORE_ACCESS
                        break
                    store_record = (4, addr, new)
            else:
                wr = old
                new = atomics.amo_result(op, old, b)
                if not data_write(addr, 4, new):
                    cause = CAUSE_STORE_ACCESS
                    break
                store_record = (4, addr, new)
                if reservation_valid and addr < reservation_addr + 4 and addr + 4 > reservation_addr:
                    reservation_valid = False
            if a_events is not None:
                a_events.append((pc, raw, op, fields["aq"], fields["rl"], rd, rs1, rs2,
                                 addr, old, b, new, sc_status,
                                 -1 if reservation_before is None else reservation_before,
                                 -1 if not reservation_valid else reservation_addr))
        elif opcode == 0x13:
            imm = sx(insn >> 20, 12)
            shamt = (insn >> 20) & 31
            if f3 == 0: wr = (a + imm) & MASK32
            elif f3 == 2: wr = int(legacy.s32(a) < imm)
            elif f3 == 3: wr = int(a < (imm & MASK32))
            elif f3 == 4: wr = a ^ (imm & MASK32)
            elif f3 == 6: wr = a | (imm & MASK32)
            elif f3 == 7: wr = a & (imm & MASK32)
            elif f3 == 1: wr = (a << shamt) & MASK32
            elif f3 == 5:
                wr = a >> shamt if f7 == 0 else (legacy.s32(a) >> shamt) & MASK32
        elif opcode == 0x33:
            if f7 == 1:
                wr = legacy.md_exec(f3, a, b)
                if m_events is not None:
                    m_events.append((pc, insn, f3, rd, rs1, rs2, a, b, wr & MASK32))
                if f3 >= 4 and divider_cost_events is not None:
                    # `ilen` is measured in bits by the classifier; the
                    # external trace/event schema records instruction bytes.
                    divider_cost_events.append((pc, raw, ilen // 8, DIV_EXTRA_CYCLES))
            elif f7 == 0:
                wr = {0: (a + b) & MASK32, 1: (a << (b & 31)) & MASK32, 2: int(legacy.s32(a) < legacy.s32(b)), 3: int(a < b), 4: a ^ b, 5: a >> (b & 31), 6: a | b, 7: a & b}[f3]
            elif f7 == 0x20 and f3 == 0: wr = (a - b) & MASK32
            elif f7 == 0x20 and f3 == 5: wr = (legacy.s32(a) >> (b & 31)) & MASK32
        elif opcode == 0x0F:
            pass
        elif opcode == 0x73:
            cause = CAUSE_ECALL if insn == 0x73 else CAUSE_EBREAK
            break
        else:
            cause = CAUSE_ILLEGAL
            break

        rd_written = 0
        rd_value = 0
        if wr is not None and rd != 0:
            regs[rd] = wr & MASK32
            rd_written, rd_value = rd, regs[rd]
        trace.append(f"I {pc:08x} {raw:08x} {ilen // 8:02d} {insn:08x} {rd_written:02d} {rd_value:08x} {store_record[0]} {store_record[1]:08x} {store_record[2]:08x}")
        pc = next_pc
    else:
        cause = -1

    footer = [f"HALT {cause} {pc:08x}"] + [f"REG {i} {regs[i]:08x}" for i in range(1, 32)]
    footer.insert(0, f"STOP {pc:08x} {stop_raw:08x} {stop_ilen:02d} {cause}")
    for addr in range(0x4000, 0x6000, 4):
        value = int.from_bytes(mem[addr:addr + 4], "little")
        if value:
            footer.append(f"MEM {addr:08x} {value:08x}")
    return cause, regs, trace, footer, oob, len(trace)


def load_hex(path):
    with open(path, encoding="ascii") as src:
        return [int(line, 16) for line in src.read().split()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("rv32im", "rv32imc", "rv32ima", "rv32imac"), help="never infer A or C enablement")
    parser.add_argument("image", help="little-endian 32-bit word hex image")
    parser.add_argument("trace")
    parser.add_argument("--a-events", help="optional independent atomic retirement sidecar TSV")
    args = parser.parse_args()
    words = load_hex(args.image)
    c_on = args.mode in ("rv32imc", "rv32imac")
    a_on = args.mode in ("rv32ima", "rv32imac")
    atomic_events = [] if args.a_events else None
    cause, regs, rows, footer, oob, n = run(words, c_enabled=c_on, a_enabled=a_on, a_events=atomic_events)
    with open(args.trace, "w", newline="\n", encoding="ascii") as dst:
        if a_on:
            dst.write(f"TRACE_V3 RV32IM{'AC' if c_on else 'A'} pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar\n")
        elif c_on:
            dst.write("TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data\n")
        dst.write("\n".join(rows + footer) + "\n")
    if args.a_events:
        import csv
        with open(args.a_events, "w", newline="", encoding="ascii") as dst:
            writer = csv.writer(dst, delimiter="\t", lineterminator="\n")
            writer.writerow(["pc", "raw", "op", "aq", "rl", "rd", "rs1", "rs2", "address", "old", "source", "new", "sc_status", "reservation_before", "reservation_after"])
            writer.writerows((f"{row[0]:08x}", f"{row[1]:08x}", *row[2:8], f"{row[8]:08x}",
                              "-" if row[9] is None else f"{row[9]:08x}", f"{row[10]:08x}",
                              "-" if row[11] is None else f"{row[11]:08x}", *row[12:]) for row in atomic_events or [])
    print(f"RV32IMC_ISS mode={args.mode} cause={cause} gp={regs[3]:08x} instret={n} oob={oob} div_extra_cycles_per_op={DIV_EXTRA_CYCLES}")


if __name__ == "__main__":
    main()

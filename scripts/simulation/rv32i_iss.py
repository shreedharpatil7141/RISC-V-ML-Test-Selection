#!/usr/bin/env python3
"""Independent RV32I instruction-set simulator (Stage 1 reference for trace comparison).
Written from the ISA spec; shares no code with the RTL. Mirrors Stage-1 halt behaviour.
Halt causes (impl-defined, match rv32_pkg): 1 ECALL 2 EBREAK 3 ILLEGAL 4 LOAD_MIS 5 STORE_MIS 6 FETCH_MIS.
Trace line: pc insn rd rdval st_size st_addr st_data  (rd=0/rdval=0 when no x1-x31 write; st_*=0 if no store)
Footer: HALT cause pc | REG n val (x1..x31) | MEM addr val (non-zero words 0x4000..0x5FFF)"""
import sys
M = 0xFFFFFFFF
MEM_BYTES = 65536
def s32(x): x &= M; return x - (1 << 32) if x >> 31 else x
def sx(v, bits): v &= (1 << bits) - 1; return v - (1 << bits) if v >> (bits - 1) else v

def run(words, max_steps=2_000_000):
    mem = bytearray(MEM_BYTES)
    for i, w in enumerate(words):
        mem[4*i:4*i+4] = (w & M).to_bytes(4, 'little')
    x = [0]*32; pc = 0; trace = []; oob = 0
    def rd32(a):
        nonlocal oob
        if a >= MEM_BYTES: oob += 1; return 0
        a &= ~3; return int.from_bytes(mem[a:a+4], 'little')
    def load(a, n):
        nonlocal oob
        if a + n > MEM_BYTES: oob += 1; return 0
        return int.from_bytes(mem[a:a+n], 'little')
    def store(a, n, v):
        nonlocal oob
        if a + n > MEM_BYTES: oob += 1; return
        mem[a:a+n] = (v & ((1 << (8*n)) - 1)).to_bytes(n, 'little')
    cause = 0; steps = 0
    while steps < max_steps:
        steps += 1
        insn = rd32(pc)
        opc = insn & 0x7F; rd = (insn >> 7) & 31; f3 = (insn >> 12) & 7
        rs1 = (insn >> 15) & 31; rs2 = (insn >> 20) & 31; f7 = insn >> 25
        a, b = x[rs1], x[rs2]
        wr = None; npc = (pc + 4) & M; st = (0, 0, 0)
        if insn & 3 != 3: cause = 3; break
        if opc == 0x37: wr = insn & 0xFFFFF000
        elif opc == 0x17: wr = (pc + (insn & 0xFFFFF000)) & M
        elif opc == 0x6F:
            i = ((insn >> 31) << 20) | (((insn >> 12) & 0xFF) << 12) | (((insn >> 20) & 1) << 11) | (((insn >> 21) & 0x3FF) << 1)
            t = (pc + sx(i, 21)) & M
            if t & 3: cause = 6; break
            wr = npc; npc = t
        elif opc == 0x67:
            if f3 != 0: cause = 3; break
            t = (a + sx(insn >> 20, 12)) & M & ~1
            if t & 3: cause = 6; break
            wr = npc; npc = t
        elif opc == 0x63:
            if f3 in (2, 3): cause = 3; break
            i = ((insn >> 31) << 12) | (((insn >> 7) & 1) << 11) | (((insn >> 25) & 0x3F) << 5) | (((insn >> 8) & 0xF) << 1)
            t = (pc + sx(i, 13)) & M
            tk = {0: a == b, 1: a != b, 4: s32(a) < s32(b), 5: s32(a) >= s32(b), 6: a < b, 7: a >= b}[f3]
            if tk:
                if t & 3: cause = 6; break
                npc = t
        elif opc == 0x03:
            if f3 not in (0, 1, 2, 4, 5): cause = 3; break
            ad = (a + sx(insn >> 20, 12)) & M
            n = {0: 1, 1: 2, 2: 4, 4: 1, 5: 2}[f3]
            if ad % n: cause = 4; break
            v = load(ad, n)
            wr = sx(v, 8*n) & M if f3 in (0, 1, 2) else v
        elif opc == 0x23:
            if f3 not in (0, 1, 2): cause = 3; break
            ad = (a + sx(((insn >> 25) << 5) | ((insn >> 7) & 31), 12)) & M
            n = 1 << f3
            if ad % n: cause = 5; break
            st = (n, ad, b & ((1 << (8*n)) - 1)); store(ad, n, b)
        elif opc == 0x13:
            imm = sx(insn >> 20, 12); sh = (insn >> 20) & 31
            if f3 == 1:
                if f7 != 0: cause = 3; break
                wr = (a << sh) & M
            elif f3 == 5:
                if f7 == 0: wr = a >> sh
                elif f7 == 0x20: wr = (s32(a) >> sh) & M
                else: cause = 3; break
            else:
                wr = {0: (a + imm) & M, 2: int(s32(a) < imm), 3: int(a < (imm & M)),
                      4: (a ^ imm) & M, 6: (a | imm) & M, 7: (a & imm) & M}[f3]
        elif opc == 0x33:
            if f7 == 0:
                wr = {0: (a + b) & M, 1: (a << (b & 31)) & M, 2: int(s32(a) < s32(b)), 3: int(a < b),
                      4: a ^ b, 5: a >> (b & 31), 6: a | b, 7: a & b}[f3]
            elif f7 == 0x20 and f3 == 0: wr = (a - b) & M
            elif f7 == 0x20 and f3 == 5: wr = (s32(a) >> (b & 31)) & M
            else: cause = 3; break
        elif opc == 0x0F:
            if f3 != 0: cause = 3; break
        elif opc == 0x73:
            if insn == 0x73: cause = 1
            elif insn == 0x100073: cause = 2
            else: cause = 3
            break
        else: cause = 3; break
        rdw = 0; rdv = 0
        if wr is not None and rd != 0:
            x[rd] = wr & M; rdw = rd; rdv = wr & M
        trace.append(f"{pc:08x} {insn:08x} {rdw:02d} {rdv:08x} {st[0]} {st[1]:08x} {st[2]:08x}")
        pc = npc
    else:
        cause = -1
    foot = [f"HALT {cause} {pc:08x}"] + [f"REG {i} {x[i]:08x}" for i in range(1, 32)]
    for ad in range(0x4000, 0x6000, 4):
        v = int.from_bytes(mem[ad:ad+4], 'little')
        if v: foot.append(f"MEM {ad:08x} {v:08x}")
    return cause, x, trace, foot, oob, len(trace)

def load_hex(path):
    return [int(l, 16) for l in open(path).read().split()]

if __name__ == '__main__':
    cause, x, trace, foot, oob, n = run(load_hex(sys.argv[1]))
    open(sys.argv[2], 'w').write("\n".join(trace + foot) + "\n")
    print(f"ISS cause={cause} gp={x[3]} instret={n} oob={oob}")

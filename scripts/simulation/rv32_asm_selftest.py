#!/usr/bin/env python3
"""Anchor the assembler to known-good RISC-V encodings (from the ISA manual / common toolchain output)."""
from rv32_asm import assemble
KNOWN = [
 ("addi x1,x0,1",       0x00100093), ("lui x1,0x12345",    0x123450B7), ("jal x0,0",        0x0000006F),
 ("ecall",              0x00000073), ("ebreak",            0x00100073), ("sw x1,0(x2)",     0x00112023),
 ("beq x0,x0,0",        0x00000063), ("lw x1,0(x2)",       0x00012083), ("sub x1,x2,x3",    0x403100B3),
 ("srai x1,x2,3",       0x40315093), ("add x1,x2,x3",      0x003100B3), ("nop",             0x00000013),
 ("ret",                0x00008067), ("addi x5,x5,-1",     0xFFF28293), ("fence",           0x0FF0000F),
 ("auipc x1,0x1",       0x00001097), ("beq x1,x2,8",       0x00208463), ("jal x1,2048",     0x001000EF),
 # RV32M: hand-assembled from the spec field layout funct7=0000001|rs2|rs1|funct3|rd|0110011
 ("mul x1,x2,x3",       0x023100B3), ("mulh x1,x2,x3",     0x023110B3), ("mulhsu x1,x2,x3",   0x023120B3),
 ("mulhu x1,x2,x3",     0x023130B3), ("div x1,x2,x3",      0x023140B3), ("divu x1,x2,x3",     0x023150B3),
 ("rem x1,x2,x3",       0x023160B3), ("remu x1,x2,x3",     0x023170B3),
 ("mul a0,a0,a1",       0x02B50533), ("div a0,a0,a1",      0x02B54533), ("remu a0,a0,a1",     0x02B57533),
 ("mul x0,x1,x2",       0x02208033), ("mulhu x31,x31,x31", 0x03FFBFB3),
 ("sb x5,3(x6)",        0x005301A3), ("slli x1,x1,31",     0x01F09093), ("bne x0,x0,-4",    0xFE001EE3),
]
bad = 0
for src, exp in KNOWN:
    got = assemble(src)[0]
    ok = got == exp
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {src:20s} got={got:08x} exp={exp:08x}")
print("ASM_SELFTEST", "PASS" if bad == 0 else f"FAIL({bad})")
raise SystemExit(bad != 0)

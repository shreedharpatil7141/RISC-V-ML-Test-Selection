# 32-bit ADDI starts at PC=2 and spans adjacent aligned words.
c.nop
addi x8, x0, 17
c.addi x8, 1
c.ebreak

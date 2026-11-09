c.nop
li x1, 24
li x2, 0x00700293
sw x2, 0(x1)
fence.i
c.nop
ebreak
ecall

li x1, 20
li x2, 0x00700293
amoswap.w x3, x2, (x1)
fence.i
ebreak
ecall

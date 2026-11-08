c.nop
li x1, 0x5000
li x2, 0x80000000
sw x2, 0(x1)
amomin.w.aqrl x3, x2, (x1)
ecall

li x1, 0x5001
li x2, 1
sw x2, 0(x1)
amoadd.w x3, x2, (x1)
ecall

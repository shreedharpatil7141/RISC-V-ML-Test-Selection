li x4, 0x5000
li x5, 0xa55aa55a
sw x5, 0(x4)
li x1, 0x10000
li x2, 1
amoadd.w x3, x2, (x1)
ecall

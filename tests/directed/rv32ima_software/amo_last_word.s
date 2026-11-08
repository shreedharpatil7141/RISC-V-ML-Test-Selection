li x1, 0xfffc
li x2, 0x55
sw x2, 0(x1)
li x3, 1
amoadd.w x4, x3, (x1)
lw x5, 0(x1)
ecall

li x1, 0x5000
li x2, 0x80000000
li x3, 0x7fffffff
sw x2, 0(x1)
amoswap.w x4, x3, (x1)
amoadd.w.aq x5, x3, (x1)
amoxor.w.rl x6, x2, (x1)
amoand.w.aqrl x7, x3, (x1)
amoor.w x8, x2, (x1)
amomin.w x9, x3, (x1)
amomax.w x10, x2, (x1)
amominu.w x11, x3, (x1)
amomaxu.w x12, x2, (x1)
ecall

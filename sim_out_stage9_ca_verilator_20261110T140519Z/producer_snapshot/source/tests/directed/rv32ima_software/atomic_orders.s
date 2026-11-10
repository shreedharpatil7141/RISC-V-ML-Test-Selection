li x1, 0x5000
li x2, 1
sw x0, 0(x1)
amoadd.w x3, x2, (x1)
amoadd.w.aq x4, x2, (x1)
amoadd.w.rl x5, x2, (x1)
amoadd.w.aqrl x6, x2, (x1)
sc.w.aq x7, x2, (x1)
lr.w.rl x8, (x1)
lr.w.aqrl x9, (x1)
lr.w x0, (x1)
sc.w x0, x2, (x1)
amoadd.w x0, x2, (x1)
ecall

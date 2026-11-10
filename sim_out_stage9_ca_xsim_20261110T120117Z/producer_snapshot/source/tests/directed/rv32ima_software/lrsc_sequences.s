li x1, 0x5000
li x2, 0x11223344
sw x2, 0(x1)
lr.w.aq x3, (x1)
li x4, 0x55667788
sc.w.rl x5, x4, (x1)
sc.w x6, x4, (x1)
lr.w x7, (x1)
addi x8, x1, 4
sc.w x9, x4, (x8)
lr.w x10, (x1)
sw x4, 0(x1)
sc.w x11, x2, (x1)
sc.w x12, x2, (x1)
ecall

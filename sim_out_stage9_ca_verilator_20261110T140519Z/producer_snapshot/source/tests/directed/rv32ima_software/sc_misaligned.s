li x1, 0x5000
li x2, 0xa55aa55a
sw x2, 0(x1)
lr.w x3, (x1)
addi x4, x1, 1
sc.w x5, x2, (x4)
ecall

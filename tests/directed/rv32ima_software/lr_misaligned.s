li x1, 0x5000
li x2, 0xa55aa55a
sw x2, 0(x1)
addi x3, x1, 1
lr.w x4, (x3)
ecall

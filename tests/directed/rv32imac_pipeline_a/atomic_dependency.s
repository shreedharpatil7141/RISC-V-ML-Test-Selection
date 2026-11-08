li x1, 0x5000
li x2, 1
sw x2, 0(x1)
lr.w x3, (x1)
addi x4, x3, 2
amoadd.w x5, x2, (x1)
addi x6, x5, 3
sc.w x7, x2, (x1)
ecall

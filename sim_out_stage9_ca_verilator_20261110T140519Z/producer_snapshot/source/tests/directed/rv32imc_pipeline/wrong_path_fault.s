c.li x8, 1
c.bnez x8, target
.hword 0x0000
target:
c.addi x8, 1
ecall

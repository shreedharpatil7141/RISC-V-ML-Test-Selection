c.jal subroutine
c.addi x8, 1
c.ebreak
subroutine:
addi x9, x1, 0
jal x10, after
c.addi x11, 1
after:
addi x12, x10, 0
ecall

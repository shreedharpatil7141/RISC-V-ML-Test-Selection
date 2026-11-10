lui x5, 16
addi x5, x5, -6
c.li x8, 0
jalr x0, 0(x5)
.org 0xFFF2
target:
ecall
.org 0xFFFA
c.beqz x8, target
.org 0xFFFC
.2byte 0x0003

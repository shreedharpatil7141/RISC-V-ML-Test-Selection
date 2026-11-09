li x1, 0x40
csrrw x0, 0x305, x1
c.nop
ecall
lui x6, 0x10
li x5, 0x53544737
sw x5, -4(x6)
jal x0, 0
.org 0x40
csrrs x2, 0x341, x0
addi x2, x2, 2
csrrw x0, 0x341, x2
mret

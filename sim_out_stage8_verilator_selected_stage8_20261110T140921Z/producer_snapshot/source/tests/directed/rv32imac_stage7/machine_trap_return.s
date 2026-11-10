li x1, 0x40
csrrw x0, 0x305, x1
csrrsi x0, 0x300, 8
csrrs x4, 0xCC0, x0
lui x6, 0x10
li x5, 0x53544737
csrrs x3, 0xCC1, x0
ecall
ebreak
sw x5, -4(x6)
jal x0, 0
.org 0x40
csrrs x2, 0x341, x0
addi x2, x2, 4
csrrw x0, 0x341, x2
mret

li x1, 0x80
csrrw x0, 0x305, x1
li x2, 0x88
csrrw x0, 0x304, x2
csrrsi x0, 0x300, 8
addi x3, x0, 5
lui x6, 0x10
li x7, 0x53544737
sw x7, -4(x6)
jal x0, 0
.org 0x80
mret

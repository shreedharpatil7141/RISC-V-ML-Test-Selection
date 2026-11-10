li x1, 0x80
csrrw x0, 0x305, x1
li x2, 0x888
csrrw x0, 0x304, x2
li x5, 84
addi x6, x0, 7
csrrsi x0, 0x300, 8
div x4, x5, x6
lui x7, 0x10
li x8, 0x53544737
sw x8, -4(x7)
jal x0, 0
.org 0x80
mret

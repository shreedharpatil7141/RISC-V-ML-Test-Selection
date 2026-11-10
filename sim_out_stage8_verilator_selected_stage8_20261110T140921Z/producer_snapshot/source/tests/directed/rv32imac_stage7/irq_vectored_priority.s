li x1, 0x81
csrrw x0, 0x305, x1
li x2, 0x888
csrrw x0, 0x304, x2
csrrsi x0, 0x300, 8
addi x3, x0, 9
lui x6, 0x10
li x5, 0x53544737
sw x5, -4(x6)
jal x0, 0
.org 0xac
mret

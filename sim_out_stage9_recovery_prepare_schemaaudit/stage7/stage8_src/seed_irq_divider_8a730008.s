li x1, 0x180
csrrw x0, 0x305, x1
li x2, 0x800
csrrw x0, 0x304, x2
csrrsi x0, 0x300, 8
li x5, 1044
li x6, 12
jal x0, div_start
.org 0x100
div_start:
div x7, x5, x6
addi x8, x7, 1
jal x0, test_done
.org 0x180
mret
.org 0x200
test_done:
lui x30, 0x10
li x31, 0x53544737
sw x31, -4(x30)
jal x0, 0

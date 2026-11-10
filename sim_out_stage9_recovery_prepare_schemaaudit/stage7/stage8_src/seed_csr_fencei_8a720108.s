li x1, 0x180
csrrw x0, 0x305, x1
li x2, 81
csrrw x10, 0x800, x2
csrrs x11, 0x800, x0
csrrwi x12, 0x801, 17
csrrci x13, 0x801, 5
li x3, 0x4000
sw x11, 0(x3)
fence.i
lw x14, 0(x3)
jal x0, test_done
.org 0x180
mret
.org 0x200
test_done:
lui x30, 0x10
li x31, 0x53544737
sw x31, -4(x30)
jal x0, 0

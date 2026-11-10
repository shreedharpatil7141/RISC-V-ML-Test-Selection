li x1, 0x180
csrrw x0, 0x305, x1
li x2, 0x4000
lw x4, 1(x2)
addi x5, x0, 45
jal x0, test_done
.org 0x180
csrrs x20, 0x341, x0
addi x20, x20, 4
csrrw x0, 0x341, x20
mret
.org 0x200
test_done:
lui x30, 0x10
li x31, 0x53544737
sw x31, -4(x30)
jal x0, 0

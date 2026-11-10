li x1, 0x180
csrrw x0, 0x305, x1
li x2, 0x4000
li x8, 10
addi x9, x8, 6
slli x10, x9, 1
sw x10, 0(x2)
lw x11, 0(x2)
sub x12, x11, x10
beq x12, x0, dep_taken
addi x13, x0, 99
dep_taken:
addi x14, x11, -6
jal x0, test_done
.org 0x180
mret
.org 0x200
test_done:
lui x30, 0x10
li x31, 0x53544737
sw x31, -4(x30)
jal x0, 0

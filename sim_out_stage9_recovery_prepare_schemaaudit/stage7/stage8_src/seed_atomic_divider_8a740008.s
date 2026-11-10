li x1, 0x180
csrrw x0, 0x305, x1
li x2, 0x4000
addi x3, x0, 23
lr.w x4, (x2)
add x5, x4, x3
sc.w x6, x5, (x2)
addi x7, x6, 1
div x8, x5, x7
sw x8, 4(x2)
jal x0, test_done
.org 0x180
mret
.org 0x200
test_done:
lui x30, 0x10
li x31, 0x53544737
sw x31, -4(x30)
jal x0, 0

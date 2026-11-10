li x1, 0x80
csrrw x0, 0x305, x1
li x2, 0x4000
addi x3, x0, 85
lr.w x4, (x2)
ecall
sc.w x5, x3, (x2)
lui x6, 0x10
li x7, 0x53544737
sw x7, -4(x6)
jal x0, 0
.org 0x80
csrrs x8, 0x341, x0
addi x8, x8, 4
csrrw x0, 0x341, x8
mret

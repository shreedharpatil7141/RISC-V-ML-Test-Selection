li x1, 0x80
csrrw x0, 0x305, x1
li x2, 0x4000
addi x3, x0, 85
sw x3, 1(x2)
li x2, 0x10000
lw x4, 0(x2)
li x3, 85
amoswap.w x5, x3, (x2)
lui x6, 0x10
li x5, 0x53544737
sw x5, -4(x6)
jal x0, 0
.org 0x80
csrrs x4, 0x341, x0
addi x4, x4, 4
csrrw x0, 0x341, x4
mret

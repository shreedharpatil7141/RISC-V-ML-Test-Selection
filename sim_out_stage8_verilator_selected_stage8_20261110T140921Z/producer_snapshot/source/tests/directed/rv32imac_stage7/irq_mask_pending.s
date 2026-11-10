li x1, 0x80
csrrw x0, 0x305, x1
li x2, 0x800
csrrw x0, 0x304, x2
csrrs x3, 0x344, x0
li x4, 8
csrrs x0, 0x300, x4
addi x5, x0, 1
lui x6, 0x10
li x7, 0x53544737
sw x7, -4(x6)
jal x0, 0
.org 0x80
csrrw x0, 0x304, x0
csrrs x8, 0x342, x0
blt x8, x0, irq_return
csrrs x8, 0x341, x0
addi x8, x8, 4
csrrw x0, 0x341, x8
irq_return:
mret

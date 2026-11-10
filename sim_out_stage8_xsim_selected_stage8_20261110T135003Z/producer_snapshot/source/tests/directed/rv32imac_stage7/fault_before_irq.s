li x1, 0x80
csrrw x0, 0x305, x1
li x2, 0x800
csrrw x0, 0x304, x2
li x3, 8
csrrs x0, 0x300, x3
.word 0xffffffff
addi x10, x0, 1
lui x6, 0x10
li x7, 0x53544737
sw x7, -4(x6)
jal x0, 0
.org 0x80
csrrs x2, 0x342, x0
blt x2, x0, irq_return
csrrs x2, 0x341, x0
addi x2, x2, 4
csrrw x0, 0x341, x2
irq_return:
mret

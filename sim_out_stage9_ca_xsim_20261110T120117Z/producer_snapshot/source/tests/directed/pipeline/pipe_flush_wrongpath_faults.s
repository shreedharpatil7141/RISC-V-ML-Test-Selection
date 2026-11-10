# wrong-path instructions that WOULD fault must be squashed (generated)
li x8, 20480
li gp, 2
beq x0, x0, w1
ebreak
ebreak
w1:
li gp, 3
jal x0, w2
.word 0x00000000
.word 0xFFFFFFFF
w2:
li gp, 4
beq x0, x0, w3
lw x5, 1(x8)
sw x5, 2(x8)
w3:
li gp, 5
la x6, w4
jalr x0, 0(x6)
ecall
ebreak
w4:
li gp, 6
jal x0, w5
lw x5, 2(x8)
.word 0x0000100F
w5:
li gp, 1
ecall
fail:
ecall

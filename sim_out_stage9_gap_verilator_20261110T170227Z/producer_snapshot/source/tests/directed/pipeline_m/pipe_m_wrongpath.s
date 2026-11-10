# A taken EX redirect must squash a younger M instruction and its destination write.
li x5, 9
li x6, 9
li x7, 0x55
li x8, 0x5000
beq x0, x0, target
mul x7, x5, x6
sw x7, 0(x8)
target:
li x30, 0x55
bne x7, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

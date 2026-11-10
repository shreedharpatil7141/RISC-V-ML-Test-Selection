# EX forwarding of M results to arithmetic, branch operands, and store data.
li x5, 6
li x6, 7
li x8, 0x5000
li x9, 42
mul x7, x5, x6
add x10, x7, x6
li x30, 49
bne x10, x30, fail
beq x7, x9, branch_ok
j fail
branch_ok:
mul x11, x5, x6
sw x11, 0(x8)
lw x12, 0(x8)
bne x12, x9, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

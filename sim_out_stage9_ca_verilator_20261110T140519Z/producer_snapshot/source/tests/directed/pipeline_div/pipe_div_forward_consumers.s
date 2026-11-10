# DIV result forwarding to branch, arithmetic, store data, and JALR.
li x5, 70
li x6, 7
li x8, 0x5000
li x30, 10
div x7, x5, x6
beq x7, x30, branch_ok
j fail
branch_ok:
div x11, x5, x6
add x12, x11, x6
li x30, 17
bne x12, x30, fail
div x13, x5, x6
sw x13, 0(x8)
lw x14, 0(x8)
li x30, 10
bne x14, x30, fail
la x15, target
li x16, 1
div x17, x15, x16
jalr x0, 0(x17)
fail:
li gp, 2
ecall
target:
li gp, 1
ecall

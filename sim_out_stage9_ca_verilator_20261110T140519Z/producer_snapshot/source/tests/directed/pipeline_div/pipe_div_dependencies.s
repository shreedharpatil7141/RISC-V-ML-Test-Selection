# Divisor operands are produced in immediately preceding pipeline stages.
li x5, 9
li x6, 7
mul x7, x5, x6
li x8, 3
div x9, x7, x8
li x30, 21
bne x9, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

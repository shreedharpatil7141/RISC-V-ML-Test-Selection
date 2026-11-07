# The second adjacent load feeds DIV immediately and must cause one load-use stall.
li x8, 0x5000
li x5, 84
sw x5, 0(x8)
li x5, 7
sw x5, 4(x8)
lw x6, 0(x8)
lw x7, 4(x8)
div x9, x6, x7
li x30, 12
bne x9, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

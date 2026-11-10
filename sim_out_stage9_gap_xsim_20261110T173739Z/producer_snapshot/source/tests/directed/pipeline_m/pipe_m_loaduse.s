# Both M operands depend on adjacent loads; the second triggers the single load-use bubble.
li x8, 0x5000
li x5, 6
sw x5, 0(x8)
li x5, 7
sw x5, 4(x8)
lw x6, 0(x8)
lw x7, 4(x8)
mul x9, x6, x7
li x30, 42
bne x9, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

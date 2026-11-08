# Older misaligned load fault must suppress a younger DIV start.
li x5, 0x5000
lw x6, 1(x5)
li x7, 100
li x8, 3
div x9, x7, x8
sw x9, 0(x5)

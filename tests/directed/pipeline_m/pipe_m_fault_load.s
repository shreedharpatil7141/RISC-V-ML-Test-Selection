# Older misaligned load fault must squash younger M work.
li x5, 0x5000
lw x6, 1(x5)
li x7, 9
mul x8, x7, x7
sw x8, 0(x5)

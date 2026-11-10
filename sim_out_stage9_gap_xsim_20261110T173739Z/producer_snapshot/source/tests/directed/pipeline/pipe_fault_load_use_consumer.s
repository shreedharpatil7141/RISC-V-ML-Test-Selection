# generated pipeline fault test
li x8, 20480
la x5, T
sw x5, 0(x8)
lw x6, 0(x8)
lw x7, 1(x6)
T: ebreak

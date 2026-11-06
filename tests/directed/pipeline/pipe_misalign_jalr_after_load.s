# generated pipeline fault test
li x8, 20480
la x5, T
addi x5, x5, 2
sw x5, 0(x8)
lw x6, 0(x8)
jalr x0, 0(x6)
T: ebreak

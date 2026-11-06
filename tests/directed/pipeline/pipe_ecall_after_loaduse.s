# generated pipeline fault test
li x8, 20480
li x5, 4
sw x5, 0(x8)
lw x6, 0(x8)
add x7, x6, x6
li gp, 1
ecall

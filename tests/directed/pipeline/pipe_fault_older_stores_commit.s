# generated pipeline fault test
li x8, 20480
li x5, 0x1234
sw x5, 0(x8)
sw x5, 8(x8)
lw x6, 2(x8)
sw x5, 12(x8)

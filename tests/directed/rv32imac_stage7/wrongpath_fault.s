beq x0, x0, 8
.word 0xffffffff
lui x6, 0x10
li x5, 0x53544737
sw x5, -4(x6)
jal x0, 0

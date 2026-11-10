la x1, target
li x2, 0x00200513
sw x2, 0(x1)
fence.i
target:
addi x10, x0, 1
lui x6, 0x10
li x7, 0x53544737
sw x7, -4(x6)
jal x0, 0

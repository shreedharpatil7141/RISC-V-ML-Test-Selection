# Older illegal instruction must squash younger M work.
li x5, 9
li x6, 9
li x8, 0x5000
.word 0x00000000
mul x7, x5, x6
sw x7, 0(x8)

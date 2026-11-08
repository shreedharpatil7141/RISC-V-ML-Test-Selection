# Older illegal instruction coincides with younger DIV in ID/EX; start is suppressed.
li x5, 100
li x6, 3
.word 0x00000000
div x7, x5, x6
sw x7, 0(x8)

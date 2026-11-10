# A load immediately feeds DIV's rs1; the interlock must insert one bubble.
li x8, 0x5000
li x6, 7
li x5, 84
sw x5, 0(x8)
lw x7, 0(x8)
div x9, x7, x6
li x30, 12
bne x9, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

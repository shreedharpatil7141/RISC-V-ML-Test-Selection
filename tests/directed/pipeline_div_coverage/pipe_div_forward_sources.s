# Produce each divide source immediately before and one instruction before issue
# to exercise EX/MEM and MEM/WB forwarding independently on both operands.
li x5, 84
li x6, 7
div x7, x5, x6
li x5, 7
li x6, 84
div x8, x6, x5
li x30, 12
bne x7, x30, fail
bne x8, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

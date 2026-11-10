# A taken branch squashes a younger divide before the divider accepts it.
li x5, 100
li x6, 3
beq x0, x0, target
div x7, x5, x6
sw x7, 0(x8)
target:
li gp, 1
ecall

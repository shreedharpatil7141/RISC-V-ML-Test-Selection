j target
csrrw x1, 0xC00, x2
target:
addi gp, x0, 1
ecall

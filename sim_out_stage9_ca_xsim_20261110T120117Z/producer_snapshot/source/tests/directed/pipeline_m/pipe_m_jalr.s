# The M result is the immediately following JALR base operand.
la x5, target
li x6, 1
mul x7, x5, x6
jalr x0, 0(x7)
li gp, 2
ecall
target:
li gp, 1
ecall

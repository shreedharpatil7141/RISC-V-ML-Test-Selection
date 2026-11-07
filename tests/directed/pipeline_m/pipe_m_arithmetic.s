# All eight RV32M operations, signed/unsigned boundaries, zero divisor, and signed overflow.
li x5, -7
li x6, 2
mul x7, x5, x6
li x30, -14
bne x7, x30, fail
mulh x7, x5, x6
li x30, -1
bne x7, x30, fail
mulhsu x7, x5, x6
li x30, -1
bne x7, x30, fail
mulhu x7, x5, x6
li x30, 1
bne x7, x30, fail
div x7, x5, x6
li x30, -3
bne x7, x30, fail
divu x7, x5, x6
li x30, 0x7ffffffc
bne x7, x30, fail
rem x7, x5, x6
li x30, -1
bne x7, x30, fail
remu x7, x5, x6
li x30, 1
bne x7, x30, fail
li x5, 0x80000000
mulh x7, x5, x5
li x30, 0x40000000
bne x7, x30, fail
li x6, -1
mulhsu x7, x5, x6
li x30, 0x80000000
bne x7, x30, fail
mulhu x7, x6, x6
li x30, -2
bne x7, x30, fail
div x7, x5, x6
bne x7, x5, fail
rem x7, x5, x6
bne x7, x0, fail
li x5, 0x12345678
li x6, 0
div x7, x5, x6
li x30, -1
bne x7, x30, fail
divu x7, x5, x6
bne x7, x30, fail
rem x7, x5, x6
bne x7, x5, fail
remu x7, x5, x6
bne x7, x5, fail
# Zero dividend, +1/-1 operands, signed maximum, and unsigned maximum boundaries.
li x5, 0
li x6, -1
mul x7, x5, x6
bne x7, x0, fail
div x7, x5, x6
bne x7, x0, fail
remu x7, x5, x6
bne x7, x0, fail
li x5, 1
li x6, -1
div x7, x5, x6
li x30, -1
bne x7, x30, fail
rem x7, x5, x6
bne x7, x0, fail
li x5, 0x7fffffff
li x6, 2
mulh x7, x5, x6
bne x7, x0, fail
div x7, x5, x6
li x30, 0x3fffffff
bne x7, x30, fail
li x5, -1
li x6, 1
divu x7, x5, x6
bne x7, x5, fail
remu x7, x5, x6
bne x7, x0, fail
mulhu x7, x5, x5
li x30, -2
bne x7, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

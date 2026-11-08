# Consecutive DIV/REM operations, dependency forwarding, and rd=x0 counting.
li x5, 144
li x6, 12
div x7, x5, x6
rem x8, x5, x6
divu x9, x5, x6
remu x10, x5, x6
div x0, x5, x6
li x30, 12
bne x7, x30, fail
bne x8, x0, fail
bne x9, x30, fail
bne x10, x0, fail
add x11, x7, x9
li x30, 24
bne x11, x30, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

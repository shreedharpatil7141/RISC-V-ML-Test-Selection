# Back-to-back M dependencies and rd=x0 must preserve zero and avoid forwarding x0.
li x5, 12
li x6, 3
mul x7, x5, x6
mul x8, x7, x6
div x9, x8, x6
rem x10, x8, x6
li x30, 36
bne x7, x30, fail
li x30, 108
bne x8, x30, fail
li x30, 36
bne x9, x30, fail
bne x10, x0, fail
mul x0, x5, x6
add x11, x0, x5
bne x11, x5, fail
li gp, 1
ecall
fail:
li gp, 2
ecall

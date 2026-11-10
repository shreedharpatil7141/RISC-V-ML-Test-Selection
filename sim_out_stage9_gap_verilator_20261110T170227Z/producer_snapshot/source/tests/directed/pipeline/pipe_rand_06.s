# constrained-random pipeline stress seed=6 (generated)
li x8, 20480
li x5, 3407369726
li x6, 2464538600
li x7, 3530265750
li x9, 346043753
li x10, 2083207870
li x11, 3273696371
li x12, 1123655737
li x13, 158152503
li x28, 1940104
li x29, 625252807
sw x29, -32(x8)
sw x13, -28(x8)
sw x11, -24(x8)
sw x11, -20(x8)
sw x5, -16(x8)
sw x10, -12(x8)
sw x13, -8(x8)
sw x9, -4(x8)
sw x12, 0(x8)
sw x28, 4(x8)
sw x28, 8(x8)
sw x6, 12(x8)
sw x9, 16(x8)
sw x29, 20(x8)
sw x28, 24(x8)
sw x10, 28(x8)
bltu x0, x6, r1
sltiu x11, x12, 3
slti x12, x0, 337
r1:
xor x7, x13, x9
lb x7, 28(x8)
ori x7, x6, -1314
lb x7, 4(x8)
slt x5, x7, x29
sb x9, -24(x8)
ori x29, x10, 1020
andi x28, x13, -1608
lui x11, 201287
li x17, 3
r2:
lw x11, 48(x8)
addi x10, x28, 1445
addi x17, x17, -1
bnez x17, r2
lb x12, -16(x8)
blt x13, x13, r3
lb x6, -60(x8)
srai x12, x11, 12
xor x28, x28, x10
r3:
li x17, 3
r4:
lui x13, 995536
lbu x6, 32(x8)
xori x0, x11, 954
addi x17, x17, -1
bnez x17, r4
bltu x12, x0, r5
sra x11, x0, x7
sb x29, 48(x8)
sb x29, -36(x8)
r5:
blt x11, x13, r6
sll x7, x10, x29
sra x9, x6, x13
xor x9, x7, x0
r6:
bltu x11, x7, r7
lui x12, 221105
r7:
andi x10, x5, -1008
beq x7, x29, r8
sw x0, -60(x8)
lw x28, -16(x8)
sw x13, 48(x8)
r8:
bge x0, x29, r9
lh x28, 8(x8)
r9:
sltu x7, x10, x10
li x17, 3
r10:
addi x9, x0, -1347
slt x28, x28, x0
xor x6, x11, x5
addi x17, x17, -1
bnez x17, r10
sw x11, -48(x8)
lw x11, -32(x8)
slti x10, x6, 822
sll x9, x7, x10
bltu x29, x12, r11
sh x12, -24(x8)
r11:
jal x0, r12
lhu x12, -16(x8)
r12:
jal x1, r13
or x9, x0, x7
lw x10, 28(x8)
r13:
sll x29, x0, x0
add x5, x13, x5
lw x12, 28(x8)
beq x28, x9, r14
sltu x12, x6, x13
add x12, x7, x0
r14:
sb x0, -60(x8)
jal x1, r15
slt x10, x0, x28
lh x9, -64(x8)
r15:
lw x6, -44(x8)
bgeu x5, x11, r16
lw x10, -60(x8)
xori x6, x0, -1625
r16:
sub x6, x13, x5
and x13, x10, x9
slti x6, x0, 1096
li x17, 3
r17:
srli x0, x10, 16
slt x7, x13, x6
lb x12, -64(x8)
addi x17, x17, -1
bnez x17, r17
srl x13, x13, x13
la x16, r18
jalr x1, 0(x16)
sh x13, -64(x8)
r18:
sltu x28, x11, x29
la x16, r19
jalr x1, 0(x16)
sll x29, x6, x12
r19:
bne x0, x6, r20
slti x28, x28, -1636
r20:
lh x6, 20(x8)
la x16, r21
jalr x1, 0(x16)
lh x10, -32(x8)
and x13, x29, x0
r21:
li x17, 3
r22:
slli x11, x0, 7
sll x6, x0, x9
slt x6, x0, x7
sb x0, -32(x8)
addi x17, x17, -1
bnez x17, r22
lh x12, -28(x8)
li x17, 3
r23:
sltu x10, x5, x5
sw x0, 52(x8)
sltiu x5, x0, -1218
sltiu x29, x6, 1008
addi x17, x17, -1
bnez x17, r23
lw x9, 56(x8)
beq x28, x7, r24
sb x7, 56(x8)
r24:
andi x11, x9, -656
xor x10, x10, x28
blt x13, x28, r25
lw x7, -4(x8)
lb x29, 60(x8)
slli x12, x5, 20
r25:
slt x29, x7, x10
lbu x9, -24(x8)
beq x11, x29, r26
andi x5, x9, 1848
r26:
slli x7, x0, 5
li x17, 3
r27:
lui x29, 427390
lui x13, 459019
addi x17, x17, -1
bnez x17, r27
beq x13, x0, r28
srli x9, x28, 17
lh x9, 44(x8)
lw x12, 40(x8)
r28:
li x17, 3
r29:
sw x0, -52(x8)
add x13, x13, x12
addi x17, x17, -1
bnez x17, r29
xor x12, x5, x6
xori x10, x29, -1410
blt x13, x13, r30
slt x29, x5, x5
lw x10, 32(x8)
add x28, x6, x10
r30:
jal x0, r31
sra x12, x9, x6
r31:
bne x7, x7, r32
sw x12, 56(x8)
r32:
bge x13, x11, r33
ori x6, x6, -238
lhu x28, -8(x8)
lui x29, 576035
r33:
bltu x9, x29, r34
lbu x12, 36(x8)
r34:
li x17, 3
r35:
xor x7, x11, x13
lhu x13, 12(x8)
sltiu x13, x29, -1580
slti x13, x10, 326
addi x17, x17, -1
bnez x17, r35
bge x9, x6, r36
sw x29, 44(x8)
lw x29, 16(x8)
r36:
addi x6, x6, -1518
lui x0, 54380
la x16, r37
jalr x1, 0(x16)
sra x6, x28, x6
addi x28, x5, 792
r37:
jal x0, r38
lw x28, 0(x8)
lh x10, -64(x8)
r38:
bge x10, x7, r39
sb x5, -12(x8)
add x7, x13, x0
r39:
xori x5, x9, -363
add x9, x9, x10
slti x9, x11, 240
la x16, r40
jalr x0, 0(x16)
add x9, x0, x12
r40:
beq x0, x6, r41
slt x28, x28, x6
srli x12, x11, 11
slti x5, x11, -295
r41:
add x28, x5, x10
srai x9, x9, 26
bltu x0, x29, r42
or x28, x7, x7
lw x7, 8(x8)
r42:
lhu x7, -12(x8)
xor x13, x5, x0
li x17, 3
r43:
lhu x11, 24(x8)
slli x28, x29, 16
lhu x29, -20(x8)
addi x17, x17, -1
bnez x17, r43
beq x7, x6, r44
srai x29, x5, 13
r44:
add x11, x13, x12
ori x28, x5, 165
jal x0, r45
lui x11, 735003
sb x9, 12(x8)
r45:
bne x9, x6, r46
sw x11, -16(x8)
sw x12, -52(x8)
r46:
lbu x28, -4(x8)
xor x28, x11, x10
bne x7, x6, r47
srli x11, x5, 7
r47:
srli x7, x13, 25
lw x12, 44(x8)
lui x10, 517667
lw x13, 36(x8)
li gp, 1
ecall
fail:
ecall

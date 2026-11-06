# constrained-random pipeline stress seed=11 (generated)
li x8, 20480
li x5, 1942955373
li x6, 3718334796
li x7, 2404204071
li x9, 3680198571
li x10, 3969454221
li x11, 3355305989
li x12, 1999951809
li x13, 1940605046
li x28, 2181161661
li x29, 3672393040
sw x29, -32(x8)
sw x9, -28(x8)
sw x7, -24(x8)
sw x28, -20(x8)
sw x13, -16(x8)
sw x29, -12(x8)
sw x7, -8(x8)
sw x6, -4(x8)
sw x13, 0(x8)
sw x10, 4(x8)
sw x7, 8(x8)
sw x6, 12(x8)
sw x28, 16(x8)
sw x5, 20(x8)
sw x29, 24(x8)
sw x12, 28(x8)
li x17, 3
r1:
lw x5, -64(x8)
lb x10, -56(x8)
and x11, x5, x13
slti x13, x28, -134
addi x17, x17, -1
bnez x17, r1
bge x5, x0, r2
xori x13, x28, -1367
r2:
blt x9, x28, r3
sub x12, x12, x6
sb x5, -64(x8)
r3:
sw x12, 36(x8)
srai x7, x10, 21
addi x12, x7, -30
beq x5, x13, r4
slt x11, x13, x28
srl x28, x0, x12
r4:
addi x9, x10, 443
li x17, 3
r5:
and x11, x0, x29
slt x29, x13, x10
addi x17, x17, -1
bnez x17, r5
lui x28, 809857
slt x13, x5, x29
lui x28, 1014443
la x16, r6
jalr x0, 0(x16)
sltu x29, x9, x29
sll x7, x0, x0
r6:
li x17, 3
r7:
lhu x10, -44(x8)
addi x12, x5, 42
addi x17, x17, -1
bnez x17, r7
lhu x12, 60(x8)
sll x10, x9, x13
bltu x29, x6, r8
add x9, x6, x10
addi x11, x5, -605
r8:
slli x28, x11, 8
li x17, 3
r9:
lw x9, -32(x8)
lui x6, 995712
sb x5, -48(x8)
addi x17, x17, -1
bnez x17, r9
lbu x5, -48(x8)
srai x7, x0, 8
jal x1, r10
sub x5, x12, x5
sb x29, 32(x8)
r10:
sub x10, x6, x0
xor x12, x12, x0
bge x13, x13, r11
add x7, x10, x29
slt x6, x0, x6
andi x29, x13, 47
r11:
li x17, 3
r12:
slti x29, x28, -659
lw x6, 48(x8)
sltiu x11, x12, 4
addi x17, x17, -1
bnez x17, r12
slti x7, x12, -250
blt x9, x7, r13
andi x7, x6, 219
r13:
jal x0, r14
xori x9, x12, 1997
lhu x29, 16(x8)
r14:
add x28, x0, x0
addi x12, x0, -935
slt x13, x7, x5
li x17, 3
r15:
ori x0, x0, 972
sh x13, 0(x8)
addi x17, x17, -1
bnez x17, r15
or x5, x0, x5
or x7, x0, x28
sw x0, -8(x8)
sh x13, 52(x8)
sw x28, 20(x8)
lb x9, -36(x8)
sw x28, 16(x8)
lh x6, -44(x8)
sltiu x12, x13, -1816
sb x7, 20(x8)
bne x13, x7, r16
sw x13, -44(x8)
lw x28, 8(x8)
lw x11, -24(x8)
r16:
sw x10, 32(x8)
li x17, 3
r17:
or x29, x28, x10
srli x7, x28, 7
srli x28, x5, 2
srai x11, x29, 7
addi x17, x17, -1
bnez x17, r17
lw x10, 52(x8)
sw x9, 56(x8)
ori x5, x11, -1159
lui x12, 271500
beq x5, x9, r18
xor x28, x0, x11
r18:
andi x6, x29, -1043
la x16, r19
jalr x1, 0(x16)
lb x13, 32(x8)
r19:
bltu x29, x7, r20
or x0, x0, x9
srai x10, x29, 8
xor x0, x7, x11
r20:
bne x9, x9, r21
sll x11, x0, x6
r21:
or x12, x0, x7
lui x6, 201445
lb x9, 20(x8)
lw x7, -48(x8)
and x11, x28, x29
slt x13, x7, x7
li x17, 3
r22:
sll x9, x0, x13
xor x12, x12, x13
xori x7, x9, 1008
slt x7, x7, x12
addi x17, x17, -1
bnez x17, r22
lbu x11, -24(x8)
lb x5, 36(x8)
bne x28, x29, r23
lh x12, -36(x8)
lw x5, 36(x8)
r23:
andi x10, x11, 1488
jal x1, r24
lw x10, 20(x8)
r24:
and x7, x5, x9
sw x9, 36(x8)
bltu x6, x12, r25
sb x12, -60(x8)
slt x12, x10, x13
slti x9, x0, 1029
r25:
xor x13, x28, x28
sb x0, 48(x8)
jal x0, r26
xori x5, x13, -663
r26:
la x16, r27
jalr x0, 0(x16)
sw x28, 36(x8)
lui x9, 599262
r27:
sltu x28, x5, x5
jal x0, r28
addi x10, x11, 1210
r28:
sb x9, 44(x8)
blt x9, x5, r29
sll x29, x9, x29
lw x9, 40(x8)
addi x9, x11, -781
r29:
xori x12, x29, 99
bgeu x12, x11, r30
srli x28, x0, 8
or x13, x10, x28
lui x7, 576203
r30:
lw x12, -16(x8)
bne x9, x9, r31
sb x0, -52(x8)
srl x12, x5, x29
or x10, x10, x6
r31:
jal x0, r32
lui x9, 1015041
r32:
sra x6, x0, x7
la x16, r33
jalr x0, 0(x16)
slti x29, x13, 1428
r33:
bge x7, x11, r34
lh x28, 8(x8)
r34:
lhu x6, 28(x8)
bge x11, x6, r35
and x12, x13, x0
addi x5, x10, -301
sb x0, 12(x8)
r35:
lh x5, -28(x8)
lh x5, -36(x8)
andi x28, x10, 1540
sw x9, 36(x8)
li x17, 3
r36:
sb x11, 28(x8)
and x11, x12, x9
lw x9, 32(x8)
srai x13, x7, 11
addi x17, x17, -1
bnez x17, r36
addi x28, x9, -1576
srai x6, x12, 4
blt x28, x6, r37
xor x12, x6, x5
lui x29, 204366
r37:
bgeu x12, x9, r38
xor x9, x13, x12
andi x6, x7, 1996
andi x10, x29, -1670
r38:
lw x7, -64(x8)
jal x0, r39
sb x28, 28(x8)
lhu x13, 40(x8)
r39:
li x17, 3
r40:
lhu x0, -24(x8)
xori x10, x28, 344
addi x17, x17, -1
bnez x17, r40
sw x0, -36(x8)
add x6, x13, x5
beq x11, x6, r41
and x9, x9, x29
r41:
bltu x28, x9, r42
srl x13, x7, x10
lui x11, 1005565
r42:
la x16, r43
jalr x1, 0(x16)
sb x13, -8(x8)
slti x9, x12, 201
r43:
jal x0, r44
sw x13, -4(x8)
r44:
bltu x7, x12, r45
lh x29, -32(x8)
r45:
bltu x10, x28, r46
sll x12, x5, x9
lw x29, -32(x8)
and x13, x0, x28
r46:
addi x29, x0, 439
sub x7, x13, x9
slti x6, x10, 541
sra x29, x0, x0
sub x28, x0, x12
bgeu x6, x0, r47
sra x10, x9, x10
slli x29, x0, 13
r47:
li x17, 3
r48:
or x10, x0, x10
sb x10, -16(x8)
addi x17, x17, -1
bnez x17, r48
lh x6, 4(x8)
bgeu x0, x11, r49
lb x11, -28(x8)
lui x28, 375902
r49:
ori x29, x0, -1310
srl x13, x12, x6
lbu x7, -12(x8)
jal x1, r50
ori x12, x5, 1234
lui x5, 513909
r50:
bltu x28, x5, r51
sltiu x6, x0, 1566
slt x10, x28, x11
r51:
jal x0, r52
sltu x10, x28, x9
r52:
srai x29, x0, 12
li x17, 3
r53:
sb x0, -16(x8)
lbu x28, 56(x8)
srli x6, x6, 23
sra x13, x0, x7
addi x17, x17, -1
bnez x17, r53
srai x10, x6, 16
lw x6, -28(x8)
lw x28, 28(x8)
li gp, 1
ecall
fail:
ecall

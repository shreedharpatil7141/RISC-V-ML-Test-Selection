# constrained-random pipeline stress seed=23 (generated)
li x8, 20480
li x5, 3972265996
li x6, 3347423150
li x7, 4074230799
li x9, 1245182509
li x10, 3832972006
li x11, 3563288028
li x12, 358847448
li x13, 73343450
li x28, 2542737575
li x29, 1317455098
sw x12, -32(x8)
sw x12, -28(x8)
sw x28, -24(x8)
sw x11, -20(x8)
sw x7, -16(x8)
sw x9, -12(x8)
sw x10, -8(x8)
sw x13, -4(x8)
sw x5, 0(x8)
sw x9, 4(x8)
sw x29, 8(x8)
sw x13, 12(x8)
sw x5, 16(x8)
sw x6, 20(x8)
sw x6, 24(x8)
sw x13, 28(x8)
srli x13, x5, 13
jal x1, r1
lui x9, 773185
r1:
li x17, 3
r2:
lw x5, -44(x8)
lw x6, 56(x8)
lui x28, 343062
addi x17, x17, -1
bnez x17, r2
or x5, x9, x29
and x7, x10, x29
lui x12, 775220
li x17, 3
r3:
ori x29, x9, 68
sub x29, x0, x13
sll x10, x0, x29
sll x10, x13, x5
addi x17, x17, -1
bnez x17, r3
slti x6, x9, -1944
li x17, 3
r4:
sw x0, -44(x8)
xori x10, x9, -1745
or x29, x9, x13
sb x6, -24(x8)
addi x17, x17, -1
bnez x17, r4
bltu x9, x10, r5
xori x5, x11, 1347
r5:
jal x1, r6
lw x0, -4(x8)
r6:
ori x29, x29, -1626
jal x0, r7
lui x6, 902730
r7:
sw x28, -36(x8)
srli x5, x0, 17
andi x29, x12, -381
jal x0, r8
lb x13, 40(x8)
r8:
bge x29, x0, r9
lw x6, 12(x8)
slt x11, x5, x13
andi x6, x13, 1325
r9:
sltiu x7, x10, 747
or x5, x10, x28
sltu x9, x7, x28
lui x13, 582031
bge x5, x5, r10
lbu x13, 56(x8)
sltu x11, x9, x11
r10:
bltu x6, x7, r11
srai x29, x11, 18
sh x5, -36(x8)
sb x7, -32(x8)
r11:
li x17, 3
r12:
ori x28, x5, -1696
lui x13, 214770
sltiu x28, x6, -738
addi x17, x17, -1
bnez x17, r12
la x16, r13
jalr x0, 0(x16)
sh x28, 44(x8)
lw x10, -8(x8)
r13:
bgeu x10, x13, r14
sh x11, 32(x8)
sb x13, 36(x8)
andi x9, x28, -723
r14:
addi x9, x11, 1453
xor x12, x9, x11
srl x6, x11, x29
srl x29, x29, x7
li x17, 3
r15:
lb x13, 52(x8)
sw x10, -52(x8)
addi x17, x17, -1
bnez x17, r15
bge x12, x11, r16
lw x13, -24(x8)
and x10, x28, x13
slli x13, x12, 30
r16:
bgeu x10, x6, r17
and x9, x9, x28
lw x7, 12(x8)
srl x28, x13, x28
r17:
li x17, 3
r18:
slt x6, x0, x29
lbu x11, -48(x8)
lw x28, -36(x8)
lh x29, -36(x8)
addi x17, x17, -1
bnez x17, r18
li x17, 3
r19:
add x11, x0, x13
sb x28, 0(x8)
srl x12, x0, x0
sub x7, x0, x7
addi x17, x17, -1
bnez x17, r19
sll x9, x10, x5
bge x5, x29, r20
andi x7, x5, -907
xor x5, x0, x29
sw x5, 60(x8)
r20:
addi x29, x7, -345
sh x7, -32(x8)
jal x0, r21
lw x7, -24(x8)
srai x10, x29, 13
r21:
la x16, r22
jalr x1, 0(x16)
lb x28, 44(x8)
r22:
srl x7, x11, x6
bne x11, x0, r23
ori x5, x28, -23
ori x12, x6, -981
r23:
bne x6, x28, r24
lui x7, 936814
lh x5, 24(x8)
r24:
bge x0, x0, r25
xori x13, x6, 1259
srli x10, x0, 1
r25:
sb x5, 20(x8)
beq x0, x0, r26
lui x6, 821460
lui x29, 858766
sltu x9, x28, x28
r26:
li x17, 3
r27:
lw x12, 36(x8)
lw x6, 4(x8)
andi x6, x7, -1959
sb x13, 56(x8)
addi x17, x17, -1
bnez x17, r27
sb x10, -20(x8)
lui x10, 765823
sb x0, 0(x8)
sh x28, -28(x8)
sltiu x12, x11, -235
bgeu x5, x0, r28
sb x6, -52(x8)
sub x6, x12, x10
r28:
la x16, r29
jalr x1, 0(x16)
xor x9, x10, x29
r29:
la x16, r30
jalr x1, 0(x16)
sw x28, -56(x8)
r30:
jal x0, r31
lhu x10, -56(x8)
r31:
sra x9, x9, x28
la x16, r32
jalr x0, 0(x16)
slt x12, x6, x10
r32:
li x17, 3
r33:
sw x10, 60(x8)
srai x6, x12, 26
lw x13, -12(x8)
sw x6, 4(x8)
addi x17, x17, -1
bnez x17, r33
lbu x10, -4(x8)
lbu x7, 40(x8)
slt x7, x5, x28
li x17, 3
r34:
lbu x5, 28(x8)
add x12, x28, x12
addi x17, x17, -1
bnez x17, r34
bltu x13, x0, r35
sw x5, -32(x8)
r35:
sub x12, x9, x7
la x16, r36
jalr x1, 0(x16)
andi x7, x5, -1677
slli x5, x11, 30
r36:
la x16, r37
jalr x0, 0(x16)
and x28, x0, x5
ori x9, x0, -590
r37:
xor x28, x0, x0
blt x10, x9, r38
add x7, x6, x11
xori x12, x0, 1285
r38:
li x17, 3
r39:
slli x7, x9, 12
ori x13, x6, 1627
addi x17, x17, -1
bnez x17, r39
beq x13, x10, r40
ori x12, x9, -1785
r40:
sw x5, 0(x8)
li x17, 3
r41:
ori x28, x7, 1003
lbu x5, 36(x8)
addi x17, x17, -1
bnez x17, r41
srl x10, x9, x29
addi x29, x29, 1903
lw x10, 48(x8)
jal x1, r42
or x7, x12, x11
r42:
sll x5, x0, x10
sw x29, 52(x8)
sh x6, -24(x8)
beq x11, x6, r43
slt x11, x12, x28
r43:
sub x28, x9, x11
slli x29, x0, 19
jal x0, r44
lbu x11, 44(x8)
srai x13, x9, 11
r44:
bgeu x12, x29, r45
lui x12, 645711
sw x5, 56(x8)
r45:
lw x11, -44(x8)
sb x12, -32(x8)
li x17, 3
r46:
andi x29, x29, 768
lw x12, 24(x8)
lbu x11, 40(x8)
sh x7, -36(x8)
addi x17, x17, -1
bnez x17, r46
bge x7, x0, r47
sw x0, -48(x8)
sb x13, 4(x8)
r47:
srai x29, x29, 19
lhu x10, 4(x8)
la x16, r48
jalr x1, 0(x16)
lhu x12, 52(x8)
r48:
bne x0, x13, r49
addi x10, x9, 1336
lw x29, -48(x8)
r49:
lh x13, -60(x8)
la x16, r50
jalr x0, 0(x16)
sh x13, 16(x8)
r50:
li x17, 3
r51:
xor x10, x29, x5
add x10, x13, x0
lbu x10, -60(x8)
addi x17, x17, -1
bnez x17, r51
bltu x28, x13, r52
sw x12, 8(x8)
lw x28, -48(x8)
addi x13, x0, -1646
r52:
sra x7, x9, x9
sltu x12, x28, x10
sb x5, 48(x8)
sltiu x13, x11, -238
jal x0, r53
lhu x11, 48(x8)
r53:
li x17, 3
r54:
srl x29, x12, x5
lw x10, 52(x8)
addi x17, x17, -1
bnez x17, r54
slli x0, x0, 19
sltu x5, x5, x13
andi x6, x13, -2021
xor x10, x6, x5
beq x9, x9, r55
lbu x13, 0(x8)
xori x29, x5, -1596
sll x12, x11, x29
r55:
li x17, 3
r56:
xor x10, x11, x13
srl x28, x29, x11
lw x12, -4(x8)
addi x17, x17, -1
bnez x17, r56
addi x6, x7, 1284
ori x13, x10, -1721
sltiu x12, x9, 281
or x9, x9, x13
jal x0, r57
add x5, x9, x10
lw x12, 48(x8)
r57:
lui x5, 865435
bge x13, x11, r58
addi x11, x5, 85
sw x11, -64(x8)
r58:
bne x28, x13, r59
lui x13, 671691
and x29, x0, x28
r59:
sll x13, x7, x10
and x5, x11, x29
li x17, 3
r60:
sw x0, -12(x8)
srai x7, x28, 11
add x12, x10, x13
sw x13, 48(x8)
addi x17, x17, -1
bnez x17, r60
andi x6, x28, -1636
sb x13, -60(x8)
la x16, r61
jalr x0, 0(x16)
lui x13, 559204
r61:
sub x13, x0, x29
slt x13, x29, x7
srai x7, x0, 18
and x28, x7, x10
beq x13, x9, r62
lh x13, 56(x8)
r62:
bge x0, x11, r63
lh x28, 20(x8)
slti x10, x28, -317
srli x7, x6, 27
r63:
sra x29, x29, x29
jal x1, r64
xor x29, x10, x0
sll x5, x5, x12
r64:
lw x5, -28(x8)
beq x28, x7, r65
sll x29, x13, x9
addi x9, x0, 1509
srl x28, x13, x9
r65:
addi x28, x29, -1104
lw x5, -24(x8)
bltu x13, x0, r66
sw x9, -56(x8)
sub x9, x6, x28
r66:
la x16, r67
jalr x0, 0(x16)
lhu x28, -28(x8)
slt x6, x6, x13
r67:
beq x5, x5, r68
or x12, x5, x5
r68:
li x17, 3
r69:
andi x29, x12, -611
lw x12, 12(x8)
addi x17, x17, -1
bnez x17, r69
xor x5, x28, x10
sltiu x6, x9, 2001
li x17, 3
r70:
srli x6, x7, 30
lw x29, 20(x8)
srai x5, x29, 18
addi x17, x17, -1
bnez x17, r70
la x16, r71
jalr x1, 0(x16)
lhu x11, 40(x8)
add x12, x13, x5
r71:
beq x5, x0, r72
sra x11, x29, x11
r72:
la x16, r73
jalr x1, 0(x16)
srli x12, x5, 0
sh x6, -4(x8)
r73:
sltu x6, x13, x5
li x17, 3
r74:
ori x9, x10, -667
addi x12, x28, -1479
sub x7, x29, x28
srai x11, x11, 17
addi x17, x17, -1
bnez x17, r74
li gp, 1
ecall
fail:
ecall

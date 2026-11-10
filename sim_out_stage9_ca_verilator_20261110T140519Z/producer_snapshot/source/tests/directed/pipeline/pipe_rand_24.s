# constrained-random pipeline stress seed=24 (generated)
li x8, 20480
li x5, 3059489832
li x6, 1644374017
li x7, 3606912411
li x9, 2503015641
li x10, 784226196
li x11, 937454715
li x12, 4287591260
li x13, 718675284
li x28, 833633749
li x29, 727454603
sw x6, -32(x8)
sw x7, -28(x8)
sw x10, -24(x8)
sw x5, -20(x8)
sw x13, -16(x8)
sw x13, -12(x8)
sw x6, -8(x8)
sw x5, -4(x8)
sw x28, 0(x8)
sw x7, 4(x8)
sw x13, 8(x8)
sw x13, 12(x8)
sw x10, 16(x8)
sw x13, 20(x8)
sw x6, 24(x8)
sw x10, 28(x8)
la x16, r1
jalr x0, 0(x16)
sw x0, -56(x8)
sw x0, -48(x8)
r1:
sll x28, x13, x10
lb x7, 60(x8)
jal x0, r2
slti x28, x13, 76
sh x6, -32(x8)
r2:
lhu x10, -12(x8)
jal x1, r3
sltiu x5, x7, 1512
r3:
sb x5, 48(x8)
bge x13, x6, r4
srl x5, x12, x28
r4:
slli x11, x10, 19
and x10, x0, x5
li x17, 3
r5:
srl x12, x0, x12
sw x12, 28(x8)
xori x5, x5, 1895
slti x10, x9, -1016
addi x17, x17, -1
bnez x17, r5
sw x7, -20(x8)
jal x0, r6
or x6, x0, x13
r6:
sb x7, -36(x8)
srai x11, x28, 31
xori x29, x0, 1052
sw x6, -16(x8)
xor x28, x10, x9
bne x9, x6, r7
sh x10, 52(x8)
srl x9, x29, x29
r7:
jal x1, r8
lw x29, -56(x8)
sh x0, -8(x8)
r8:
and x5, x0, x29
sltiu x11, x13, 267
li x17, 3
r9:
ori x28, x10, -255
ori x10, x12, 677
addi x17, x17, -1
bnez x17, r9
sltiu x28, x13, 1812
bne x5, x6, r10
srai x29, x28, 4
r10:
blt x9, x0, r11
lui x7, 296480
sh x28, 0(x8)
lui x9, 328982
r11:
sh x10, -28(x8)
slt x10, x13, x5
lbu x6, -8(x8)
la x16, r12
jalr x1, 0(x16)
lui x13, 719999
r12:
bne x0, x29, r13
sw x7, 40(x8)
r13:
lhu x5, -52(x8)
xori x7, x0, -43
li x17, 3
r14:
srli x5, x0, 8
srai x7, x28, 15
addi x17, x17, -1
bnez x17, r14
bge x0, x11, r15
xor x5, x29, x13
lui x28, 336402
xori x13, x9, -1027
r15:
sw x0, -16(x8)
srl x13, x7, x28
bltu x9, x0, r16
add x13, x7, x11
lbu x12, -64(x8)
slti x0, x12, 327
r16:
blt x6, x9, r17
lbu x29, 16(x8)
r17:
bne x12, x9, r18
lui x6, 240391
r18:
beq x29, x10, r19
addi x5, x10, 928
lw x28, 44(x8)
r19:
sw x6, 56(x8)
lb x29, 48(x8)
beq x10, x6, r20
srl x28, x7, x11
sw x6, 24(x8)
lw x5, 0(x8)
r20:
bgeu x29, x0, r21
slti x6, x0, -105
sh x12, 32(x8)
addi x12, x12, 58
r21:
slt x11, x12, x6
li x17, 3
r22:
xor x0, x7, x0
srai x9, x7, 20
addi x17, x17, -1
bnez x17, r22
bgeu x7, x6, r23
sh x0, -8(x8)
or x7, x29, x13
slt x28, x13, x10
r23:
bne x28, x12, r24
sll x5, x7, x9
r24:
li x17, 3
r25:
sw x6, 12(x8)
sltiu x5, x11, -1382
lb x6, 40(x8)
addi x17, x17, -1
bnez x17, r25
slti x5, x28, -877
jal x0, r26
srl x10, x6, x7
sltu x6, x10, x7
r26:
sll x10, x10, x5
jal x0, r27
lui x0, 484991
sh x0, 4(x8)
r27:
addi x13, x5, -832
blt x7, x13, r28
lb x0, 28(x8)
sll x6, x10, x11
r28:
jal x1, r29
lui x11, 200149
r29:
sub x12, x0, x13
bne x0, x9, r30
sh x29, -32(x8)
add x28, x13, x6
lui x12, 779197
r30:
bltu x5, x9, r31
sub x0, x29, x5
r31:
addi x9, x11, -755
la x16, r32
jalr x0, 0(x16)
lui x13, 23116
r32:
andi x5, x28, -850
slt x7, x9, x10
slt x10, x12, x29
lw x10, 60(x8)
li x17, 3
r33:
xori x12, x0, -629
srl x5, x0, x29
addi x17, x17, -1
bnez x17, r33
lui x29, 618154
sw x11, -28(x8)
lhu x13, -44(x8)
beq x13, x29, r34
sltiu x29, x6, 1351
sltiu x28, x6, 371
lw x9, -24(x8)
r34:
sw x5, -48(x8)
and x7, x29, x0
li x17, 3
r35:
sb x0, 16(x8)
srai x5, x7, 2
addi x17, x17, -1
bnez x17, r35
li x17, 3
r36:
lw x5, 0(x8)
srai x29, x7, 30
lw x13, -44(x8)
addi x17, x17, -1
bnez x17, r36
bge x9, x9, r37
ori x11, x10, -1271
andi x7, x11, 1219
r37:
sub x13, x12, x29
slt x5, x10, x28
srl x11, x11, x29
jal x1, r38
xori x11, x10, -1397
r38:
beq x13, x0, r39
srl x28, x0, x10
r39:
li x17, 3
r40:
lh x7, -52(x8)
sll x6, x10, x7
sb x5, -20(x8)
sw x7, -28(x8)
addi x17, x17, -1
bnez x17, r40
li x17, 3
r41:
lui x9, 918932
andi x29, x29, 1848
xori x11, x5, -1092
addi x17, x17, -1
bnez x17, r41
lbu x11, 60(x8)
jal x0, r42
sw x10, 0(x8)
r42:
jal x0, r43
xor x6, x12, x0
r43:
blt x0, x0, r44
srli x29, x0, 29
sh x5, -60(x8)
sw x10, 0(x8)
r44:
blt x6, x13, r45
sh x12, 36(x8)
slti x6, x28, -1739
lw x5, 4(x8)
r45:
ori x12, x0, 917
sltu x13, x28, x12
slti x9, x6, -800
andi x7, x28, 1238
lhu x7, -60(x8)
li x17, 3
r46:
slli x11, x0, 0
addi x9, x5, 1921
and x7, x0, x13
addi x17, x17, -1
bnez x17, r46
sh x9, -48(x8)
bge x0, x13, r47
sll x29, x6, x13
r47:
slti x6, x0, 406
jal x1, r48
ori x13, x6, -497
r48:
slli x29, x9, 29
ori x6, x11, 1236
jal x0, r49
sw x6, 4(x8)
sltiu x12, x7, 2006
r49:
ori x29, x5, 111
sb x28, 0(x8)
jal x1, r50
lb x11, 4(x8)
sb x7, 44(x8)
r50:
slti x9, x10, -661
lui x12, 301400
slti x29, x9, 253
sltu x11, x13, x5
lui x5, 165788
sw x5, 12(x8)
jal x1, r51
andi x28, x9, -1984
slt x12, x28, x13
r51:
sll x5, x0, x12
sw x12, -16(x8)
li x17, 3
r52:
addi x12, x29, -610
sltiu x28, x5, -1627
addi x17, x17, -1
bnez x17, r52
lui x28, 470977
bge x5, x9, r53
xori x9, x12, 1254
sltu x13, x28, x5
r53:
sltu x11, x28, x0
sub x9, x10, x0
slt x9, x12, x0
lhu x5, -44(x8)
or x28, x11, x10
la x16, r54
jalr x1, 0(x16)
lbu x11, 4(x8)
srai x9, x0, 10
r54:
la x16, r55
jalr x0, 0(x16)
srai x7, x9, 25
addi x28, x6, -530
r55:
sb x13, 48(x8)
la x16, r56
jalr x1, 0(x16)
sw x12, -8(x8)
r56:
bltu x12, x0, r57
sw x10, -16(x8)
r57:
lw x13, -44(x8)
sb x29, -44(x8)
la x16, r58
jalr x0, 0(x16)
srl x10, x0, x0
add x28, x0, x11
r58:
blt x12, x7, r59
sh x10, -16(x8)
lw x29, -28(x8)
andi x11, x13, 1240
r59:
ori x10, x10, -1675
and x13, x5, x13
sw x7, 12(x8)
sw x10, 8(x8)
sh x0, 8(x8)
addi x13, x9, -483
lui x5, 306575
li x17, 3
r60:
xori x12, x6, -1001
andi x28, x10, 1666
addi x17, x17, -1
bnez x17, r60
li x17, 3
r61:
lbu x28, -52(x8)
sb x6, 48(x8)
addi x17, x17, -1
bnez x17, r61
la x16, r62
jalr x1, 0(x16)
lw x11, 48(x8)
r62:
jal x0, r63
srai x11, x28, 24
slt x13, x12, x0
r63:
blt x13, x10, r64
lbu x5, 12(x8)
r64:
lh x12, 60(x8)
la x16, r65
jalr x1, 0(x16)
add x10, x6, x28
addi x10, x0, 1380
r65:
or x12, x5, x13
srai x10, x0, 26
add x11, x0, x13
sh x11, -16(x8)
sltu x13, x10, x6
bne x11, x7, r66
sub x13, x29, x28
r66:
bne x0, x5, r67
xori x13, x6, -1552
srai x12, x0, 9
r67:
sw x0, -8(x8)
bge x0, x29, r68
lui x10, 580593
add x10, x28, x12
srl x10, x29, x5
r68:
li x17, 3
r69:
and x11, x28, x13
xor x12, x10, x10
addi x17, x17, -1
bnez x17, r69
xori x11, x9, -1849
and x29, x28, x28
srai x7, x7, 31
sw x0, 20(x8)
sra x10, x28, x12
bgeu x0, x0, r70
andi x9, x12, 263
r70:
sub x9, x28, x11
lw x6, 24(x8)
bne x29, x0, r71
sb x9, -12(x8)
lui x12, 174418
add x12, x12, x6
r71:
li x17, 3
r72:
lw x6, 56(x8)
lh x11, -28(x8)
sltu x5, x11, x12
addi x17, x17, -1
bnez x17, r72
slt x28, x0, x28
sub x11, x7, x0
slt x10, x13, x10
beq x11, x5, r73
srli x5, x9, 30
sltiu x29, x11, -1625
r73:
bne x12, x5, r74
xori x13, x6, 13
xor x7, x11, x7
sb x7, -8(x8)
r74:
lbu x29, -52(x8)
ori x6, x11, 861
bltu x9, x28, r75
lhu x29, -48(x8)
srli x12, x6, 23
sltiu x12, x12, -1020
r75:
blt x13, x29, r76
and x11, x10, x5
r76:
li x17, 3
r77:
lb x5, -52(x8)
lb x9, -56(x8)
lw x9, 44(x8)
lbu x28, 36(x8)
addi x17, x17, -1
bnez x17, r77
li gp, 1
ecall
fail:
ecall

# constrained-random pipeline stress seed=13 (generated)
li x8, 20480
li x5, 1112433019
li x6, 1248794762
li x7, 2943160652
li x9, 3906445129
li x10, 2938109453
li x11, 3444583746
li x12, 3647871021
li x13, 3822511289
li x28, 797679261
li x29, 2800360461
sw x9, -32(x8)
sw x7, -28(x8)
sw x9, -24(x8)
sw x7, -20(x8)
sw x7, -16(x8)
sw x6, -12(x8)
sw x28, -8(x8)
sw x9, -4(x8)
sw x10, 0(x8)
sw x5, 4(x8)
sw x12, 8(x8)
sw x7, 12(x8)
sw x29, 16(x8)
sw x5, 20(x8)
sw x10, 24(x8)
sw x7, 28(x8)
lw x12, 48(x8)
bne x10, x11, r1
ori x11, x12, 935
r1:
la x16, r2
jalr x1, 0(x16)
andi x28, x10, 1625
r2:
bgeu x7, x13, r3
lbu x10, 8(x8)
xor x9, x10, x11
sltiu x28, x12, -977
r3:
bltu x9, x29, r4
sh x6, 44(x8)
r4:
bge x12, x5, r5
slti x7, x7, 2031
lw x28, 0(x8)
sltu x12, x11, x9
r5:
bgeu x11, x28, r6
lbu x28, 60(x8)
add x29, x29, x0
lui x7, 715829
r6:
sub x11, x9, x7
lw x11, -56(x8)
li x17, 3
r7:
lb x9, -32(x8)
sw x10, 4(x8)
srli x10, x28, 23
addi x17, x17, -1
bnez x17, r7
la x16, r8
jalr x0, 0(x16)
xori x29, x28, 1836
r8:
srl x7, x28, x0
li x17, 3
r9:
slt x13, x10, x12
lui x7, 512246
lui x13, 427498
lb x13, 16(x8)
addi x17, x17, -1
bnez x17, r9
and x7, x5, x0
jal x0, r10
xori x11, x11, -1546
sll x13, x7, x5
r10:
lh x9, 12(x8)
blt x5, x11, r11
sra x6, x29, x29
r11:
li x17, 3
r12:
slti x28, x5, 595
sll x10, x5, x9
addi x17, x17, -1
bnez x17, r12
li x17, 3
r13:
xor x5, x6, x11
add x9, x0, x9
lw x11, 48(x8)
and x11, x5, x28
addi x17, x17, -1
bnez x17, r13
li x17, 3
r14:
lui x10, 777514
slli x29, x28, 19
addi x17, x17, -1
bnez x17, r14
slti x6, x0, -1921
lh x11, 44(x8)
sb x6, -40(x8)
sw x10, -28(x8)
jal x1, r15
or x6, x10, x10
sltiu x11, x12, -766
r15:
li x17, 3
r16:
xori x29, x29, 1746
sra x10, x9, x5
srli x7, x28, 11
addi x17, x17, -1
bnez x17, r16
sltu x28, x6, x13
bgeu x5, x9, r17
lb x13, -60(x8)
lh x29, -28(x8)
lhu x7, 0(x8)
r17:
slt x12, x11, x28
srai x6, x9, 3
sb x6, 28(x8)
li x17, 3
r18:
lw x28, 24(x8)
lw x28, -44(x8)
sll x28, x0, x7
addi x17, x17, -1
bnez x17, r18
beq x28, x0, r19
lui x7, 54627
r19:
jal x1, r20
srli x12, x29, 26
or x28, x10, x11
r20:
xor x9, x12, x29
sltiu x12, x5, 1619
addi x9, x10, -283
srai x29, x9, 27
li x17, 3
r21:
sub x0, x0, x6
lw x10, 32(x8)
lui x5, 333666
addi x17, x17, -1
bnez x17, r21
li x17, 3
r22:
lb x9, -8(x8)
andi x6, x0, 1305
addi x17, x17, -1
bnez x17, r22
bge x28, x7, r23
add x29, x28, x28
r23:
jal x0, r24
lh x13, 40(x8)
r24:
or x13, x12, x10
lw x12, -44(x8)
sh x9, 12(x8)
addi x28, x5, 1393
sltiu x5, x11, -1025
sb x10, 48(x8)
sh x9, 24(x8)
sw x11, 20(x8)
jal x0, r25
and x5, x7, x0
r25:
srl x28, x6, x13
and x29, x12, x5
xori x13, x10, -1390
bge x7, x29, r26
sra x29, x6, x28
sw x0, -28(x8)
sb x28, -16(x8)
r26:
sw x10, 44(x8)
xori x29, x29, -739
srl x12, x5, x12
lw x7, 44(x8)
sra x6, x28, x0
bge x12, x28, r27
sb x13, 60(x8)
r27:
bge x6, x28, r28
lb x5, 60(x8)
lui x11, 238395
slt x11, x13, x13
r28:
lh x7, 60(x8)
add x29, x7, x29
slt x5, x0, x13
lhu x10, -36(x8)
lui x10, 376508
sw x29, -12(x8)
bge x0, x11, r29
andi x28, x7, -903
r29:
la x16, r30
jalr x0, 0(x16)
srli x5, x29, 26
sltu x29, x13, x5
r30:
andi x11, x0, -530
lbu x29, 4(x8)
bgeu x29, x5, r31
lbu x13, 44(x8)
addi x28, x0, 1226
add x28, x11, x13
r31:
sb x11, -44(x8)
bgeu x7, x0, r32
xori x12, x29, -2043
ori x6, x11, 777
srl x12, x6, x29
r32:
ori x13, x7, -1440
sltu x6, x0, x0
sub x7, x29, x28
sra x29, x9, x13
sub x9, x13, x29
lw x28, 16(x8)
sh x28, 20(x8)
add x13, x12, x7
bge x5, x11, r33
srl x9, x9, x10
r33:
la x16, r34
jalr x1, 0(x16)
sll x5, x5, x9
r34:
xori x28, x28, 300
lw x7, 0(x8)
li x17, 3
r35:
slli x11, x6, 26
sw x11, 0(x8)
addi x17, x17, -1
bnez x17, r35
xori x10, x6, 1900
li x17, 3
r36:
xor x13, x9, x7
lhu x7, -4(x8)
addi x17, x17, -1
bnez x17, r36
slli x13, x0, 20
li x17, 3
r37:
lhu x10, -48(x8)
ori x12, x7, 94
sra x10, x28, x6
addi x17, x17, -1
bnez x17, r37
sw x0, -64(x8)
blt x12, x29, r38
lbu x10, -40(x8)
lw x11, -40(x8)
r38:
bne x6, x0, r39
andi x6, x28, -363
sltiu x10, x13, 1547
sltu x7, x13, x10
r39:
li x17, 3
r40:
lw x6, 0(x8)
lh x7, -44(x8)
lw x10, 0(x8)
addi x17, x17, -1
bnez x17, r40
li x17, 3
r41:
addi x5, x7, 1064
xori x7, x6, -1888
sh x6, -64(x8)
slt x12, x7, x9
addi x17, x17, -1
bnez x17, r41
lw x6, 20(x8)
lb x9, -36(x8)
lui x11, 113565
and x0, x10, x10
sub x28, x13, x5
la x16, r42
jalr x1, 0(x16)
ori x7, x10, 1789
r42:
sltiu x5, x12, -794
lui x7, 175053
lw x10, 8(x8)
lui x9, 812886
beq x13, x12, r43
sb x0, 20(x8)
sub x29, x29, x12
sltu x9, x0, x9
r43:
bgeu x9, x6, r44
xori x28, x13, -332
sll x12, x5, x28
add x29, x0, x29
r44:
bgeu x13, x6, r45
addi x7, x13, 200
lw x5, -20(x8)
r45:
or x6, x28, x5
sw x0, 32(x8)
slt x11, x11, x11
sll x7, x28, x9
li x17, 3
r46:
lui x5, 535030
and x9, x0, x0
sra x13, x6, x13
lh x29, 0(x8)
addi x17, x17, -1
bnez x17, r46
lui x13, 266671
srli x6, x12, 16
slti x11, x9, -1530
xori x9, x7, -850
sub x6, x0, x28
li x17, 3
r47:
srai x6, x29, 23
and x5, x28, x0
xori x29, x7, 10
slli x7, x29, 26
addi x17, x17, -1
bnez x17, r47
blt x7, x6, r48
sll x5, x0, x7
r48:
la x16, r49
jalr x1, 0(x16)
andi x12, x9, -2001
r49:
slt x29, x13, x10
blt x9, x0, r50
sltu x12, x28, x6
lw x5, 48(x8)
r50:
sltiu x28, x0, -180
bne x11, x12, r51
xori x6, x0, -1744
r51:
la x16, r52
jalr x1, 0(x16)
sb x29, 60(x8)
or x12, x28, x0
r52:
li gp, 1
ecall
fail:
ecall

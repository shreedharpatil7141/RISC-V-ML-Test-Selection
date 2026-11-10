# constrained-random pipeline stress seed=19 (generated)
li x8, 20480
li x5, 2908233303
li x6, 185773678
li x7, 3371168582
li x9, 3845760907
li x10, 2235385135
li x11, 518352914
li x12, 2196840128
li x13, 856834473
li x28, 1690218514
li x29, 1491078796
sw x28, -32(x8)
sw x10, -28(x8)
sw x29, -24(x8)
sw x7, -20(x8)
sw x29, -16(x8)
sw x10, -12(x8)
sw x6, -8(x8)
sw x10, -4(x8)
sw x12, 0(x8)
sw x11, 4(x8)
sw x10, 8(x8)
sw x6, 12(x8)
sw x11, 16(x8)
sw x10, 20(x8)
sw x5, 24(x8)
sw x29, 28(x8)
beq x9, x6, r1
addi x10, x12, -1911
srl x13, x13, x0
sh x0, 40(x8)
r1:
slli x12, x12, 12
lui x12, 960641
ori x5, x6, 1885
jal x1, r2
slti x10, x5, -42
srl x29, x13, x6
r2:
bgeu x10, x7, r3
sltu x11, x0, x7
sltiu x29, x0, -1677
r3:
addi x12, x13, -1504
slti x6, x12, 203
sltu x13, x13, x6
xori x10, x0, -794
andi x28, x5, 873
li x17, 3
r4:
add x5, x5, x10
lb x9, -16(x8)
addi x17, x17, -1
bnez x17, r4
slti x7, x11, 91
bgeu x0, x0, r5
lh x9, 44(x8)
lw x9, -8(x8)
r5:
ori x13, x29, -1221
andi x10, x11, 652
andi x6, x6, 1636
sub x9, x11, x12
lui x9, 94261
srl x10, x5, x7
lb x11, -44(x8)
la x16, r6
jalr x1, 0(x16)
lw x28, 16(x8)
r6:
lh x7, -16(x8)
sra x13, x7, x6
blt x28, x12, r7
slt x12, x10, x7
slti x11, x28, 1617
sw x6, -16(x8)
r7:
bge x7, x12, r8
sra x7, x5, x28
slti x12, x0, 486
srli x12, x12, 8
r8:
bne x7, x13, r9
lb x5, 4(x8)
r9:
jal x1, r10
srai x5, x9, 5
r10:
xori x9, x10, 1759
sll x12, x12, x5
lw x6, 20(x8)
or x10, x10, x5
or x11, x13, x6
li x17, 3
r11:
lh x6, 28(x8)
sh x6, -52(x8)
addi x17, x17, -1
bnez x17, r11
sw x13, 24(x8)
lui x12, 437791
srl x12, x11, x5
addi x10, x0, 1928
lui x6, 388521
addi x10, x9, 10
lw x9, 40(x8)
or x28, x12, x11
blt x28, x7, r12
lb x7, -56(x8)
lw x29, 44(x8)
addi x10, x0, 1270
r12:
and x12, x0, x0
sltu x12, x13, x12
jal x1, r13
ori x10, x12, -829
r13:
lbu x28, -4(x8)
li x17, 3
r14:
lw x7, -28(x8)
andi x9, x6, 1907
addi x17, x17, -1
bnez x17, r14
sw x7, 20(x8)
slti x13, x10, 644
ori x28, x12, 1120
bne x28, x0, r15
addi x7, x7, -1768
r15:
beq x11, x28, r16
andi x5, x11, 1257
addi x5, x6, 845
lbu x29, 8(x8)
r16:
ori x13, x12, 1997
ori x13, x5, 1436
sub x7, x13, x6
and x28, x29, x9
srli x11, x10, 20
sh x13, -60(x8)
lw x29, -12(x8)
li x17, 3
r17:
sw x5, 28(x8)
ori x5, x7, -606
sw x0, -56(x8)
addi x17, x17, -1
bnez x17, r17
sltu x29, x10, x0
or x29, x11, x5
jal x1, r18
lbu x28, 56(x8)
xori x6, x10, -1580
r18:
xor x13, x13, x6
bge x13, x0, r19
sltu x12, x0, x12
ori x13, x7, -1123
slt x13, x11, x28
r19:
lw x29, 32(x8)
li x17, 3
r20:
slti x6, x0, -770
andi x6, x5, -1137
lui x28, 867717
sb x28, -44(x8)
addi x17, x17, -1
bnez x17, r20
li x17, 3
r21:
srai x5, x28, 21
lw x13, 24(x8)
addi x17, x17, -1
bnez x17, r21
li x17, 3
r22:
sh x0, -20(x8)
slti x28, x29, 1864
xori x28, x13, -194
addi x17, x17, -1
bnez x17, r22
bge x6, x0, r23
slti x9, x0, 971
r23:
sll x29, x13, x29
la x16, r24
jalr x1, 0(x16)
sb x9, 48(x8)
r24:
sw x11, 24(x8)
and x13, x13, x9
lw x5, -16(x8)
li x17, 3
r25:
sltiu x5, x7, -1338
lh x9, -8(x8)
lui x11, 763651
addi x17, x17, -1
bnez x17, r25
xor x9, x6, x0
la x16, r26
jalr x1, 0(x16)
sltiu x12, x0, 427
slt x12, x10, x0
r26:
sltu x6, x28, x28
li x17, 3
r27:
add x5, x13, x5
sub x28, x9, x0
lw x28, 12(x8)
andi x6, x6, -1611
addi x17, x17, -1
bnez x17, r27
beq x9, x28, r28
sltu x29, x13, x11
lh x28, 4(x8)
srl x10, x13, x12
r28:
beq x9, x29, r29
lui x7, 918808
sltiu x29, x5, 1328
r29:
lh x13, -20(x8)
sltiu x7, x13, -982
jal x0, r30
sltiu x6, x13, 67
r30:
andi x10, x28, -231
li x17, 3
r31:
lw x10, -8(x8)
andi x5, x11, 973
slti x12, x29, -1155
lbu x28, 12(x8)
addi x17, x17, -1
bnez x17, r31
jal x1, r32
lw x12, -12(x8)
r32:
ori x13, x9, 601
or x5, x29, x28
sll x6, x0, x7
lbu x29, 20(x8)
jal x0, r33
lw x7, -32(x8)
sw x10, -64(x8)
r33:
sw x28, -36(x8)
or x9, x28, x13
slti x0, x9, 813
li x17, 3
r34:
sub x29, x11, x28
add x10, x13, x13
addi x17, x17, -1
bnez x17, r34
bne x13, x7, r35
sll x7, x0, x29
sltiu x10, x28, -334
r35:
jal x1, r36
sll x9, x10, x13
r36:
srli x28, x10, 5
blt x0, x12, r37
slti x9, x28, 1158
slli x7, x28, 25
sll x6, x9, x10
r37:
jal x0, r38
sub x29, x28, x11
slti x6, x0, 65
r38:
jal x0, r39
or x7, x9, x0
sw x0, -64(x8)
r39:
xori x28, x10, -1702
lw x12, -28(x8)
bge x11, x0, r40
addi x13, x13, 286
lbu x13, 24(x8)
xori x12, x6, 1705
r40:
li x17, 3
r41:
or x6, x9, x28
sub x12, x5, x13
sw x12, -48(x8)
sll x13, x0, x13
addi x17, x17, -1
bnez x17, r41
sltiu x10, x10, 1593
bgeu x9, x11, r42
slli x29, x9, 1
r42:
li x17, 3
r43:
sw x7, -8(x8)
lui x6, 941236
lh x12, 44(x8)
slli x9, x13, 24
addi x17, x17, -1
bnez x17, r43
jal x1, r44
and x6, x29, x11
slti x29, x7, 1952
r44:
lw x11, -56(x8)
la x16, r45
jalr x1, 0(x16)
addi x11, x10, -1108
r45:
sltiu x5, x7, 397
lw x6, -4(x8)
lb x5, 20(x8)
lh x6, -60(x8)
addi x28, x12, 1747
la x16, r46
jalr x0, 0(x16)
slti x11, x10, 533
r46:
jal x0, r47
srli x5, x13, 0
r47:
lui x9, 706247
beq x11, x5, r48
srai x10, x12, 7
lw x11, -20(x8)
r48:
lw x28, -12(x8)
xori x12, x9, -708
srli x9, x13, 17
sltu x10, x10, x28
li x17, 3
r49:
lw x13, 16(x8)
lw x29, -16(x8)
addi x17, x17, -1
bnez x17, r49
lw x5, 32(x8)
sh x13, 28(x8)
slli x12, x0, 27
lui x9, 156637
or x28, x6, x13
lhu x5, 52(x8)
bge x0, x28, r50
andi x9, x10, 869
r50:
jal x1, r51
lh x13, -52(x8)
lh x7, -44(x8)
r51:
sub x28, x12, x0
srli x12, x0, 19
bgeu x12, x12, r52
or x13, x5, x9
r52:
bgeu x7, x11, r53
slti x5, x0, -964
r53:
bgeu x11, x29, r54
sh x0, 24(x8)
sb x6, 52(x8)
r54:
jal x1, r55
sw x0, 40(x8)
r55:
srli x29, x10, 4
bltu x13, x7, r56
lw x13, 44(x8)
sb x12, 44(x8)
r56:
and x10, x11, x0
bltu x28, x7, r57
sltu x29, x7, x7
and x12, x0, x0
r57:
bge x5, x13, r58
slt x6, x5, x10
lw x6, 8(x8)
sh x9, 12(x8)
r58:
bgeu x0, x12, r59
slti x13, x5, -2033
lw x12, 0(x8)
sh x0, -4(x8)
r59:
bgeu x7, x6, r60
sh x12, -64(x8)
sll x13, x0, x29
lui x10, 511476
r60:
bltu x0, x0, r61
lh x29, -12(x8)
and x13, x29, x28
lhu x9, 48(x8)
r61:
bge x7, x9, r62
sw x0, 28(x8)
or x13, x29, x29
r62:
add x28, x29, x29
jal x1, r63
lh x13, 0(x8)
lw x29, -28(x8)
r63:
lui x12, 507036
sra x29, x0, x10
sh x11, -40(x8)
li x17, 3
r64:
lbu x10, 32(x8)
slt x7, x10, x5
sltiu x13, x5, -419
addi x13, x29, -1924
addi x17, x17, -1
bnez x17, r64
jal x1, r65
lw x12, 36(x8)
r65:
la x16, r66
jalr x1, 0(x16)
srli x13, x5, 21
r66:
lui x6, 551731
jal x0, r67
slti x6, x28, -1749
lui x12, 787520
r67:
li gp, 1
ecall
fail:
ecall

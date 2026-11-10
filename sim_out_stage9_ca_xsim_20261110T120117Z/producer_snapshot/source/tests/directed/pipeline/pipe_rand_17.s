# constrained-random pipeline stress seed=17 (generated)
li x8, 20480
li x5, 2241903809
li x6, 1778837931
li x7, 3464710496
li x9, 1303193990
li x10, 4125293655
li x11, 1570340887
li x12, 1243931546
li x13, 750280511
li x28, 3290406397
li x29, 3028564149
sw x28, -32(x8)
sw x10, -28(x8)
sw x6, -24(x8)
sw x5, -20(x8)
sw x9, -16(x8)
sw x12, -12(x8)
sw x12, -8(x8)
sw x10, -4(x8)
sw x28, 0(x8)
sw x11, 4(x8)
sw x12, 8(x8)
sw x7, 12(x8)
sw x28, 16(x8)
sw x5, 20(x8)
sw x7, 24(x8)
sw x9, 28(x8)
lw x11, -12(x8)
sub x0, x10, x12
sh x0, 40(x8)
jal x1, r1
addi x12, x0, 857
r1:
addi x13, x12, -91
or x11, x11, x5
lw x7, -32(x8)
sltiu x7, x7, 672
srli x13, x5, 3
jal x1, r2
xori x13, x0, -1606
r2:
blt x10, x6, r3
sb x29, -32(x8)
xori x13, x7, -446
sb x9, -52(x8)
r3:
la x16, r4
jalr x1, 0(x16)
lbu x9, 40(x8)
sltu x29, x0, x12
r4:
srai x10, x9, 14
sltu x5, x5, x0
la x16, r5
jalr x1, 0(x16)
or x12, x0, x13
slt x29, x9, x13
r5:
and x9, x5, x0
bltu x12, x5, r6
sh x29, 16(x8)
sltiu x9, x12, 864
r6:
or x12, x5, x9
li x17, 3
r7:
srli x6, x13, 28
sw x13, -64(x8)
add x6, x13, x11
lb x9, 4(x8)
addi x17, x17, -1
bnez x17, r7
lb x5, -36(x8)
sh x6, -60(x8)
lw x10, -60(x8)
la x16, r8
jalr x0, 0(x16)
sb x9, 0(x8)
or x7, x29, x12
r8:
sub x6, x0, x5
blt x11, x11, r9
slti x10, x13, 272
r9:
srl x10, x10, x0
ori x9, x29, -806
jal x0, r10
ori x10, x29, -786
lbu x29, 16(x8)
r10:
sw x6, -4(x8)
lhu x11, 16(x8)
slti x7, x10, -61
slli x9, x0, 7
or x11, x12, x9
sw x11, 52(x8)
sw x12, 16(x8)
li x17, 3
r11:
lui x13, 218287
sw x9, -12(x8)
srl x9, x12, x10
sw x0, -12(x8)
addi x17, x17, -1
bnez x17, r11
la x16, r12
jalr x0, 0(x16)
sb x11, 60(x8)
r12:
lui x29, 942314
li x17, 3
r13:
lbu x9, -12(x8)
sh x0, 32(x8)
addi x17, x17, -1
bnez x17, r13
lw x7, -32(x8)
li x17, 3
r14:
lbu x11, -4(x8)
sh x0, 36(x8)
andi x6, x9, 628
addi x17, x17, -1
bnez x17, r14
li x17, 3
r15:
sb x13, -40(x8)
addi x5, x7, 2021
addi x17, x17, -1
bnez x17, r15
slti x7, x10, -847
add x28, x6, x10
la x16, r16
jalr x1, 0(x16)
lh x9, -56(x8)
lw x6, 8(x8)
r16:
sw x10, 24(x8)
li x17, 3
r17:
lb x12, 28(x8)
sltiu x28, x13, 957
addi x17, x17, -1
bnez x17, r17
li x17, 3
r18:
lui x13, 730477
srli x29, x6, 5
addi x17, x17, -1
bnez x17, r18
andi x13, x0, 1728
add x28, x0, x10
lui x12, 294578
sltiu x29, x29, 661
bge x6, x12, r19
lui x12, 684424
r19:
addi x29, x13, -1286
addi x28, x0, -787
jal x0, r20
lw x29, -16(x8)
sb x6, 32(x8)
r20:
jal x1, r21
ori x12, x9, 1268
lui x10, 695021
r21:
la x16, r22
jalr x1, 0(x16)
ori x9, x6, -369
lbu x29, 48(x8)
r22:
lb x29, -16(x8)
li x17, 3
r23:
sltu x9, x0, x11
lw x10, -56(x8)
addi x17, x17, -1
bnez x17, r23
slli x5, x0, 20
blt x0, x7, r24
lui x5, 500581
lhu x12, 48(x8)
r24:
sra x28, x28, x7
bltu x5, x5, r25
addi x11, x10, -480
r25:
lhu x28, 16(x8)
xor x13, x10, x0
bge x13, x6, r26
slt x6, x10, x6
r26:
lh x12, 48(x8)
sltiu x28, x0, -724
li x17, 3
r27:
xor x7, x6, x0
xor x7, x9, x9
addi x17, x17, -1
bnez x17, r27
and x12, x29, x5
sw x12, 20(x8)
addi x9, x6, -1528
blt x29, x12, r28
sll x28, x11, x0
xor x6, x13, x9
srai x28, x0, 26
r28:
srli x13, x13, 19
bgeu x28, x0, r29
add x5, x5, x0
sb x11, -36(x8)
r29:
sw x7, 60(x8)
la x16, r30
jalr x1, 0(x16)
sw x9, -8(x8)
lb x12, -4(x8)
r30:
jal x0, r31
xori x11, x10, 346
r31:
andi x29, x11, 123
sw x13, 32(x8)
jal x0, r32
addi x6, x9, -1580
r32:
xor x0, x10, x28
addi x10, x9, -1843
lhu x7, 24(x8)
la x16, r33
jalr x0, 0(x16)
sltu x7, x29, x28
lh x5, 28(x8)
r33:
lui x10, 278017
beq x11, x6, r34
lb x9, -16(x8)
or x12, x0, x9
srli x9, x6, 16
r34:
jal x1, r35
srai x9, x7, 19
sra x5, x29, x0
r35:
la x16, r36
jalr x0, 0(x16)
slt x7, x9, x11
r36:
sub x5, x12, x28
lb x5, 20(x8)
lw x5, 40(x8)
lui x6, 243629
slti x7, x0, -419
lw x13, 4(x8)
la x16, r37
jalr x0, 0(x16)
xor x28, x28, x0
r37:
slli x11, x0, 30
li x17, 3
r38:
srli x12, x29, 12
sh x10, 4(x8)
sh x9, 36(x8)
lui x6, 466995
addi x17, x17, -1
bnez x17, r38
or x6, x11, x0
la x16, r39
jalr x1, 0(x16)
xori x9, x10, -728
sltu x29, x29, x29
r39:
or x5, x13, x5
sub x9, x6, x28
lbu x9, -32(x8)
li x17, 3
r40:
slti x6, x11, 1355
slli x0, x0, 16
addi x17, x17, -1
bnez x17, r40
sltiu x7, x9, -302
lb x13, -52(x8)
addi x9, x29, -1506
lw x5, 28(x8)
sw x13, -20(x8)
sh x7, -44(x8)
srli x9, x13, 15
add x6, x0, x5
li x17, 3
r41:
xor x11, x0, x9
andi x10, x5, -1567
sh x7, -28(x8)
sb x28, -52(x8)
addi x17, x17, -1
bnez x17, r41
blt x9, x11, r42
sra x12, x0, x28
r42:
bne x28, x0, r43
sll x28, x12, x13
r43:
li x17, 3
r44:
srl x12, x7, x0
lh x13, -36(x8)
lw x7, -24(x8)
addi x17, x17, -1
bnez x17, r44
li x17, 3
r45:
sh x7, -24(x8)
sltiu x9, x12, 93
addi x17, x17, -1
bnez x17, r45
lui x12, 1032497
or x11, x6, x5
bltu x10, x11, r46
slti x12, x5, -43
lhu x7, 0(x8)
or x28, x28, x12
r46:
sb x6, 52(x8)
la x16, r47
jalr x0, 0(x16)
sb x11, 24(x8)
sb x10, 44(x8)
r47:
lbu x13, 0(x8)
bltu x9, x9, r48
slli x28, x11, 5
sw x7, -28(x8)
r48:
slt x28, x0, x9
lw x12, 36(x8)
sltiu x11, x0, 1243
li x17, 3
r49:
lhu x29, 16(x8)
sh x9, -52(x8)
addi x17, x17, -1
bnez x17, r49
sltiu x12, x28, -426
jal x1, r50
slti x10, x29, 1392
r50:
sh x0, 52(x8)
la x16, r51
jalr x0, 0(x16)
lw x6, 12(x8)
lw x28, 20(x8)
r51:
slti x7, x29, 1145
slt x29, x28, x11
addi x7, x10, 1027
la x16, r52
jalr x1, 0(x16)
sltiu x28, x9, 870
r52:
la x16, r53
jalr x0, 0(x16)
lh x28, 52(x8)
r53:
lw x7, 40(x8)
sub x28, x11, x6
lb x29, -4(x8)
sra x5, x13, x6
bne x5, x6, r54
lw x12, 52(x8)
r54:
sw x10, 4(x8)
sw x12, 40(x8)
sw x28, -64(x8)
xori x5, x13, -1985
bltu x9, x9, r55
srli x13, x29, 14
sltiu x5, x12, -704
r55:
sb x12, 60(x8)
li x17, 3
r56:
lh x13, 48(x8)
lhu x10, 0(x8)
sw x6, -12(x8)
lbu x10, -16(x8)
addi x17, x17, -1
bnez x17, r56
srai x13, x10, 6
li x17, 3
r57:
srai x10, x12, 3
ori x6, x0, -1070
sltiu x5, x0, 1562
lui x5, 55259
addi x17, x17, -1
bnez x17, r57
li gp, 1
ecall
fail:
ecall

# constrained-random pipeline stress seed=14 (generated)
li x8, 20480
li x5, 458825077
li x6, 2645178341
li x7, 3017581834
li x9, 3243581873
li x10, 2800499137
li x11, 2263928366
li x12, 4038782778
li x13, 1060578839
li x28, 1164431025
li x29, 3157367188
sw x10, -32(x8)
sw x10, -28(x8)
sw x6, -24(x8)
sw x13, -20(x8)
sw x10, -16(x8)
sw x13, -12(x8)
sw x12, -8(x8)
sw x12, -4(x8)
sw x6, 0(x8)
sw x10, 4(x8)
sw x9, 8(x8)
sw x11, 12(x8)
sw x11, 16(x8)
sw x10, 20(x8)
sw x11, 24(x8)
sw x28, 28(x8)
slli x13, x5, 4
sltiu x11, x9, 1080
sb x0, -36(x8)
bgeu x0, x11, r1
sh x10, 48(x8)
r1:
bge x10, x28, r2
sltu x11, x10, x6
sub x12, x0, x28
r2:
bge x13, x0, r3
srli x29, x13, 29
r3:
lui x12, 537664
sra x29, x6, x29
lhu x12, -60(x8)
jal x1, r4
xor x12, x13, x10
slti x9, x5, 1796
r4:
jal x0, r5
sltu x7, x5, x5
lui x28, 751358
r5:
li x17, 3
r6:
slt x29, x5, x9
sltu x7, x7, x9
addi x17, x17, -1
bnez x17, r6
lh x6, 28(x8)
sh x11, 60(x8)
sw x13, -56(x8)
sw x6, 0(x8)
jal x0, r7
slt x29, x10, x13
r7:
slli x10, x6, 16
bltu x12, x12, r8
slti x11, x0, -640
r8:
lw x10, 24(x8)
li x17, 3
r9:
lw x11, -56(x8)
srli x29, x13, 20
sb x0, -40(x8)
sw x6, -52(x8)
addi x17, x17, -1
bnez x17, r9
jal x0, r10
add x29, x7, x12
r10:
la x16, r11
jalr x0, 0(x16)
sw x0, -60(x8)
r11:
sw x0, -64(x8)
lh x5, -36(x8)
la x16, r12
jalr x1, 0(x16)
andi x7, x11, -1809
and x28, x0, x10
r12:
li x17, 3
r13:
lui x28, 53554
sw x11, 32(x8)
lh x13, 40(x8)
sw x0, 56(x8)
addi x17, x17, -1
bnez x17, r13
lw x13, -8(x8)
jal x0, r14
sh x6, 52(x8)
sb x5, -16(x8)
r14:
bgeu x29, x0, r15
lhu x13, -8(x8)
sb x0, -20(x8)
r15:
bge x0, x9, r16
sra x9, x9, x0
ori x6, x10, -1640
r16:
lui x28, 576643
slti x9, x5, -1799
bge x11, x0, r17
slti x6, x5, -333
slli x10, x29, 14
r17:
li x17, 3
r18:
sw x29, 24(x8)
or x11, x0, x11
xori x9, x6, -1924
addi x17, x17, -1
bnez x17, r18
sh x10, -16(x8)
jal x0, r19
srli x10, x10, 28
r19:
lw x28, -48(x8)
bltu x9, x5, r20
srai x10, x29, 24
sll x11, x11, x0
addi x13, x0, -1308
r20:
la x16, r21
jalr x0, 0(x16)
sh x13, 56(x8)
r21:
slli x9, x28, 21
la x16, r22
jalr x0, 0(x16)
andi x12, x11, -1724
slli x5, x5, 24
r22:
srai x7, x0, 10
li x17, 3
r23:
srl x10, x0, x11
ori x7, x0, 1520
or x11, x0, x12
addi x17, x17, -1
bnez x17, r23
slt x28, x7, x0
li x17, 3
r24:
add x7, x9, x7
sub x12, x9, x9
addi x17, x17, -1
bnez x17, r24
lb x29, 4(x8)
bne x11, x7, r25
sll x13, x5, x28
r25:
la x16, r26
jalr x1, 0(x16)
sh x0, -52(x8)
xori x29, x9, 83
r26:
li x17, 3
r27:
slli x29, x13, 25
xor x10, x12, x11
addi x17, x17, -1
bnez x17, r27
addi x10, x0, -1931
li x17, 3
r28:
sra x7, x10, x13
xori x10, x5, 1222
addi x17, x17, -1
bnez x17, r28
bgeu x6, x10, r29
slli x12, x0, 30
r29:
li x17, 3
r30:
lh x29, 28(x8)
xori x12, x0, 125
slti x9, x5, -1009
addi x17, x17, -1
bnez x17, r30
blt x6, x13, r31
sb x9, 56(x8)
sh x12, -20(x8)
lui x6, 807195
r31:
xor x7, x11, x6
sub x6, x0, x6
beq x9, x28, r32
xor x9, x11, x29
lui x12, 869789
r32:
la x16, r33
jalr x0, 0(x16)
add x9, x6, x0
ori x29, x5, -1020
r33:
ori x7, x0, -474
la x16, r34
jalr x1, 0(x16)
sra x13, x12, x9
r34:
la x16, r35
jalr x0, 0(x16)
lbu x6, 4(x8)
r35:
li x17, 3
r36:
xor x10, x13, x7
or x13, x12, x11
addi x17, x17, -1
bnez x17, r36
blt x12, x28, r37
add x7, x28, x28
lb x11, -60(x8)
r37:
li x17, 3
r38:
xor x5, x29, x13
ori x10, x7, 656
slti x13, x28, 1045
addi x17, x17, -1
bnez x17, r38
xor x13, x0, x6
bgeu x28, x10, r39
slli x28, x5, 28
srl x13, x12, x11
sub x6, x10, x0
r39:
blt x9, x6, r40
addi x29, x10, 343
slli x11, x11, 19
r40:
xori x12, x13, 178
lh x10, 16(x8)
bne x7, x6, r41
lui x9, 351259
sh x0, 36(x8)
r41:
addi x12, x28, 1874
srl x5, x13, x5
li x17, 3
r42:
lw x12, 24(x8)
lui x29, 988141
sltiu x11, x10, 1769
lbu x11, 8(x8)
addi x17, x17, -1
bnez x17, r42
bne x13, x12, r43
ori x11, x13, 205
sra x7, x10, x7
sh x5, -60(x8)
r43:
li x17, 3
r44:
srai x13, x7, 7
srai x6, x9, 10
addi x17, x17, -1
bnez x17, r44
bne x5, x13, r45
and x6, x0, x12
slti x13, x6, 2001
r45:
lh x7, 56(x8)
jal x0, r46
sw x10, -8(x8)
r46:
sltu x11, x11, x28
sb x9, 48(x8)
srai x10, x5, 1
bgeu x13, x13, r47
slti x10, x6, 1001
andi x9, x5, -1016
sltiu x11, x29, 366
r47:
jal x0, r48
add x7, x13, x9
r48:
and x9, x10, x13
or x13, x6, x11
jal x1, r49
srl x12, x28, x13
r49:
srli x12, x0, 6
bltu x10, x6, r50
xor x29, x0, x0
lui x28, 228181
lw x12, -48(x8)
r50:
lui x12, 134554
bltu x0, x6, r51
sw x28, -4(x8)
r51:
slt x10, x9, x0
and x28, x13, x9
beq x5, x0, r52
sra x13, x6, x12
addi x5, x11, -102
r52:
lh x28, 16(x8)
add x11, x28, x10
sub x11, x6, x28
lh x13, 48(x8)
lui x9, 921358
addi x13, x0, 745
add x5, x0, x5
xori x6, x0, -2013
jal x0, r53
sw x0, -24(x8)
sltiu x13, x28, 36
r53:
jal x0, r54
lw x12, 16(x8)
srai x9, x9, 27
r54:
srli x7, x12, 13
lhu x6, -64(x8)
slli x9, x29, 23
slli x12, x7, 19
lb x11, -4(x8)
blt x7, x13, r55
sh x13, -52(x8)
sh x29, -32(x8)
r55:
la x16, r56
jalr x0, 0(x16)
lui x28, 873814
sll x10, x0, x0
r56:
bgeu x0, x0, r57
xori x7, x28, -776
sltiu x10, x29, 1042
r57:
bne x29, x7, r58
lw x9, 32(x8)
r58:
jal x1, r59
sh x7, -48(x8)
r59:
srai x10, x11, 26
slt x13, x7, x13
jal x0, r60
and x9, x7, x0
lhu x9, -24(x8)
r60:
jal x1, r61
sub x28, x10, x11
r61:
beq x7, x29, r62
srai x29, x10, 7
lw x7, 0(x8)
r62:
andi x5, x10, -1352
li x17, 3
r63:
ori x7, x9, -1999
lbu x28, -48(x8)
sw x0, -56(x8)
addi x17, x17, -1
bnez x17, r63
li gp, 1
ecall
fail:
ecall

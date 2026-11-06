# constrained-random pipeline stress seed=18 (generated)
li x8, 20480
li x5, 778526663
li x6, 527488476
li x7, 2840822562
li x9, 1927690951
li x10, 1436922981
li x11, 1028628612
li x12, 850144098
li x13, 4088434537
li x28, 2102452370
li x29, 2698045876
sw x13, -32(x8)
sw x7, -28(x8)
sw x13, -24(x8)
sw x10, -20(x8)
sw x13, -16(x8)
sw x10, -12(x8)
sw x9, -8(x8)
sw x10, -4(x8)
sw x6, 0(x8)
sw x11, 4(x8)
sw x28, 8(x8)
sw x7, 12(x8)
sw x9, 16(x8)
sw x7, 20(x8)
sw x9, 24(x8)
sw x9, 28(x8)
bltu x28, x9, r1
sh x0, 12(x8)
srl x6, x9, x0
ori x7, x29, 181
r1:
jal x1, r2
or x12, x7, x13
r2:
bgeu x7, x9, r3
lbu x13, 40(x8)
r3:
srai x7, x10, 21
jal x1, r4
slti x5, x13, -1403
r4:
slt x7, x0, x12
jal x0, r5
lhu x11, 36(x8)
r5:
jal x0, r6
andi x13, x12, 906
and x6, x10, x7
r6:
lw x6, 44(x8)
add x13, x28, x28
bge x28, x6, r7
lhu x12, 36(x8)
r7:
slli x12, x9, 11
la x16, r8
jalr x0, 0(x16)
lhu x29, -52(x8)
lh x11, -20(x8)
r8:
li x17, 3
r9:
sltu x9, x6, x7
lbu x10, 12(x8)
sub x9, x11, x11
xor x13, x0, x7
addi x17, x17, -1
bnez x17, r9
xori x7, x0, -1958
ori x7, x10, 1247
xor x5, x7, x0
bge x6, x6, r10
lw x12, 52(x8)
slli x11, x0, 4
r10:
la x16, r11
jalr x1, 0(x16)
lbu x11, 28(x8)
r11:
la x16, r12
jalr x1, 0(x16)
sw x5, -16(x8)
lb x9, -44(x8)
r12:
lw x10, -64(x8)
xor x28, x5, x7
lb x13, 44(x8)
bgeu x28, x7, r13
ori x6, x9, 204
ori x9, x0, 822
r13:
lui x28, 601573
bltu x5, x9, r14
lui x9, 452988
slt x29, x9, x12
sll x11, x5, x13
r14:
sra x11, x13, x9
sltiu x0, x12, 399
sltiu x0, x0, 100
li x17, 3
r15:
and x10, x7, x12
sltu x6, x11, x9
sltiu x10, x7, 741
addi x17, x17, -1
bnez x17, r15
addi x7, x10, -331
jal x0, r16
slti x0, x5, -1760
r16:
lbu x5, -52(x8)
lh x5, 12(x8)
blt x29, x11, r17
lw x6, 0(x8)
slt x7, x13, x11
ori x9, x6, 197
r17:
lhu x9, 28(x8)
sra x7, x7, x10
sltiu x7, x13, 482
srai x10, x9, 25
lui x7, 115445
jal x1, r18
lhu x10, 24(x8)
slti x11, x0, 1454
r18:
jal x1, r19
lb x9, -8(x8)
r19:
lhu x7, 20(x8)
jal x1, r20
lh x10, 24(x8)
lh x6, -20(x8)
r20:
srl x7, x9, x11
bge x6, x13, r21
lw x29, -44(x8)
slt x13, x0, x12
r21:
xor x12, x11, x11
jal x0, r22
sh x7, -64(x8)
r22:
or x10, x6, x29
srli x9, x12, 14
lhu x10, -52(x8)
sw x13, 52(x8)
and x9, x10, x7
lw x13, -32(x8)
blt x0, x6, r23
lb x9, -36(x8)
r23:
sra x29, x28, x7
la x16, r24
jalr x1, 0(x16)
lbu x10, 40(x8)
sw x0, 16(x8)
r24:
and x7, x13, x0
ori x10, x12, -1074
xor x9, x5, x28
slti x7, x0, 1825
slli x9, x28, 22
li x17, 3
r25:
sh x29, 32(x8)
sh x11, -4(x8)
lhu x28, 32(x8)
addi x17, x17, -1
bnez x17, r25
sw x7, 56(x8)
slt x11, x13, x13
sw x0, -64(x8)
lbu x5, 44(x8)
addi x9, x28, 343
la x16, r26
jalr x1, 0(x16)
ori x11, x6, -1001
r26:
li x17, 3
r27:
lui x5, 503172
srl x7, x29, x10
slti x6, x0, 962
sltu x11, x12, x29
addi x17, x17, -1
bnez x17, r27
ori x12, x12, -1591
or x5, x28, x10
li x17, 3
r28:
xori x29, x13, -621
sw x0, 24(x8)
srai x6, x29, 11
addi x17, x17, -1
bnez x17, r28
blt x0, x28, r29
lbu x7, -52(x8)
r29:
li x17, 3
r30:
lw x11, 4(x8)
xor x6, x9, x0
addi x17, x17, -1
bnez x17, r30
la x16, r31
jalr x1, 0(x16)
lbu x5, -28(x8)
r31:
jal x1, r32
sw x12, -56(x8)
r32:
la x16, r33
jalr x0, 0(x16)
lw x11, 8(x8)
ori x9, x10, 134
r33:
la x16, r34
jalr x1, 0(x16)
lb x6, -56(x8)
srl x11, x5, x28
r34:
bltu x0, x7, r35
sub x12, x5, x5
lhu x12, 52(x8)
r35:
lb x29, 44(x8)
srl x29, x29, x0
bge x11, x9, r36
add x29, x7, x28
slli x7, x13, 26
lui x5, 404188
r36:
srli x9, x10, 28
jal x1, r37
slli x6, x6, 20
r37:
lb x12, 52(x8)
lw x13, -4(x8)
li x17, 3
r38:
addi x11, x7, -1533
lw x0, 52(x8)
xori x28, x28, -1125
srai x11, x29, 5
addi x17, x17, -1
bnez x17, r38
or x9, x28, x12
or x10, x5, x5
sltiu x29, x11, -1717
sra x7, x7, x29
li x17, 3
r39:
sw x6, 60(x8)
sltiu x28, x0, 675
sw x29, 12(x8)
or x10, x6, x6
addi x17, x17, -1
bnez x17, r39
blt x5, x11, r40
sltiu x29, x5, 365
r40:
sub x11, x13, x13
sltu x6, x0, x9
andi x11, x5, -1713
addi x28, x5, 1906
beq x0, x12, r41
lw x6, 4(x8)
lbu x11, -44(x8)
r41:
sub x10, x5, x10
jal x0, r42
sw x13, 16(x8)
sltiu x13, x0, 955
r42:
sll x9, x11, x11
la x16, r43
jalr x0, 0(x16)
lh x29, -32(x8)
slli x29, x0, 27
r43:
slti x9, x6, 267
la x16, r44
jalr x0, 0(x16)
sub x12, x28, x11
andi x7, x10, -584
r44:
bne x13, x10, r45
ori x11, x0, -1755
r45:
andi x13, x0, -382
la x16, r46
jalr x0, 0(x16)
lui x9, 230053
r46:
jal x0, r47
sw x9, 28(x8)
r47:
bltu x0, x13, r48
xori x12, x29, -261
r48:
bne x10, x13, r49
sb x6, -24(x8)
r49:
li x17, 3
r50:
add x5, x5, x28
lw x11, -28(x8)
sw x10, 44(x8)
lhu x28, 12(x8)
addi x17, x17, -1
bnez x17, r50
lw x11, 24(x8)
la x16, r51
jalr x1, 0(x16)
sw x13, 48(x8)
sh x5, 56(x8)
r51:
xori x13, x0, 695
sub x29, x7, x9
blt x12, x5, r52
lw x29, 44(x8)
r52:
lui x12, 236051
la x16, r53
jalr x0, 0(x16)
add x28, x0, x12
r53:
jal x1, r54
sw x13, 48(x8)
andi x6, x11, -856
r54:
or x7, x13, x12
lb x6, -48(x8)
li x17, 3
r55:
sub x29, x28, x12
sltu x9, x10, x9
addi x17, x17, -1
bnez x17, r55
la x16, r56
jalr x1, 0(x16)
sll x7, x10, x6
lbu x12, -52(x8)
r56:
beq x0, x9, r57
xori x7, x5, 125
or x9, x6, x12
and x9, x29, x11
r57:
addi x9, x10, 1089
ori x5, x28, -1121
srli x10, x6, 21
bgeu x0, x9, r58
lw x12, -52(x8)
sra x7, x13, x12
andi x12, x11, -1422
r58:
jal x1, r59
sltiu x28, x13, 318
sll x9, x28, x9
r59:
lw x13, 0(x8)
jal x0, r60
xor x6, x12, x6
r60:
li x17, 3
r61:
sw x10, -64(x8)
slt x12, x5, x9
sll x7, x0, x9
srai x28, x6, 9
addi x17, x17, -1
bnez x17, r61
beq x10, x11, r62
sra x12, x0, x0
srai x7, x0, 31
r62:
sw x5, -56(x8)
addi x12, x9, 1301
sw x5, -4(x8)
xor x29, x0, x29
srl x10, x0, x6
jal x1, r63
sltu x0, x5, x13
r63:
sw x0, -24(x8)
bne x13, x13, r64
and x6, x28, x10
r64:
bgeu x29, x5, r65
and x29, x10, x28
xor x7, x6, x13
r65:
bne x12, x10, r66
sub x28, x0, x0
slti x10, x6, 1273
or x28, x9, x10
r66:
jal x1, r67
slt x7, x12, x28
lw x12, 36(x8)
r67:
and x5, x0, x6
and x7, x0, x12
la x16, r68
jalr x0, 0(x16)
srai x10, x29, 25
addi x13, x7, 933
r68:
bne x10, x29, r69
lbu x11, -12(x8)
r69:
xori x13, x0, -1430
xor x7, x7, x0
la x16, r70
jalr x0, 0(x16)
lw x10, 52(x8)
srli x11, x6, 3
r70:
li gp, 1
ecall
fail:
ecall

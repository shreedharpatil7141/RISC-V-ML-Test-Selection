# constrained-random pipeline stress seed=21 (generated)
li x8, 20480
li x5, 708452615
li x6, 1795269057
li x7, 2962526392
li x9, 1795425522
li x10, 2727303991
li x11, 1207989654
li x12, 2057720845
li x13, 3621853979
li x28, 927774550
li x29, 4250820323
sw x13, -32(x8)
sw x28, -28(x8)
sw x7, -24(x8)
sw x28, -20(x8)
sw x28, -16(x8)
sw x9, -12(x8)
sw x5, -8(x8)
sw x5, -4(x8)
sw x11, 0(x8)
sw x29, 4(x8)
sw x12, 8(x8)
sw x6, 12(x8)
sw x7, 16(x8)
sw x9, 20(x8)
sw x9, 24(x8)
sw x5, 28(x8)
sw x5, 20(x8)
lb x9, -28(x8)
beq x6, x5, r1
srl x6, x13, x7
sra x7, x9, x6
r1:
jal x0, r2
or x5, x12, x9
r2:
srl x10, x10, x11
li x17, 3
r3:
xori x6, x10, -1829
lw x5, 60(x8)
or x10, x29, x0
srai x12, x11, 7
addi x17, x17, -1
bnez x17, r3
xor x7, x11, x29
li x17, 3
r4:
sll x10, x12, x11
or x7, x0, x9
addi x17, x17, -1
bnez x17, r4
sb x11, 60(x8)
lbu x11, -48(x8)
addi x5, x10, -1621
la x16, r5
jalr x1, 0(x16)
xori x5, x6, 721
r5:
bne x7, x0, r6
slti x12, x0, 1876
xor x9, x7, x11
lui x13, 1015983
r6:
bge x10, x7, r7
lui x28, 21461
andi x28, x5, 118
lui x11, 883110
r7:
slti x28, x7, -1272
sll x28, x6, x6
bne x10, x28, r8
ori x10, x7, -561
slt x10, x0, x0
r8:
beq x29, x0, r9
sb x12, 52(x8)
sh x0, -8(x8)
xor x28, x0, x5
r9:
or x28, x28, x13
li x17, 3
r10:
srai x9, x29, 20
sw x0, -16(x8)
addi x17, x17, -1
bnez x17, r10
lh x7, -48(x8)
sb x0, -48(x8)
bge x28, x29, r11
lhu x28, 32(x8)
r11:
la x16, r12
jalr x0, 0(x16)
add x13, x9, x10
r12:
bge x0, x12, r13
lhu x11, 16(x8)
andi x0, x6, -1742
r13:
slti x28, x13, 99
sw x29, 32(x8)
jal x0, r14
xori x29, x0, -857
r14:
sltu x9, x29, x12
bge x6, x7, r15
sltiu x6, x0, -502
xor x6, x28, x10
sh x9, 4(x8)
r15:
bne x12, x13, r16
andi x29, x10, -620
lh x29, -40(x8)
r16:
sw x0, 28(x8)
srli x7, x29, 28
bne x5, x28, r17
slt x29, x13, x11
r17:
li x17, 3
r18:
srl x12, x28, x5
xori x12, x28, -47
sra x13, x5, x0
addi x17, x17, -1
bnez x17, r18
beq x12, x0, r19
sra x9, x28, x29
srli x6, x0, 21
xor x29, x10, x10
r19:
beq x6, x0, r20
slt x12, x11, x10
r20:
sra x13, x10, x0
jal x1, r21
xor x10, x28, x10
r21:
lhu x9, -44(x8)
add x7, x0, x11
bgeu x0, x0, r22
sra x9, x13, x7
r22:
la x16, r23
jalr x1, 0(x16)
sh x0, -36(x8)
r23:
li x17, 3
r24:
xor x29, x5, x11
and x12, x5, x12
lbu x5, 40(x8)
addi x17, x17, -1
bnez x17, r24
sw x13, 28(x8)
li x17, 3
r25:
sltiu x6, x28, 919
srli x6, x29, 1
addi x17, x17, -1
bnez x17, r25
li x17, 3
r26:
slt x12, x28, x28
sltiu x7, x6, -729
and x13, x0, x13
lw x7, -12(x8)
addi x17, x17, -1
bnez x17, r26
slti x10, x13, 1861
slli x29, x5, 21
blt x0, x7, r27
srl x5, x7, x12
sltu x13, x29, x13
or x10, x13, x0
r27:
xori x28, x11, 1732
srai x28, x0, 4
la x16, r28
jalr x0, 0(x16)
lw x29, -36(x8)
sw x6, 12(x8)
r28:
sub x12, x0, x29
sll x9, x13, x0
or x6, x11, x5
sltu x9, x0, x12
lw x28, -60(x8)
li x17, 3
r29:
lui x28, 1023247
srli x11, x12, 1
addi x17, x17, -1
bnez x17, r29
blt x7, x11, r30
lw x0, 52(x8)
lbu x13, 48(x8)
r30:
jal x0, r31
sb x11, 60(x8)
sltu x5, x11, x0
r31:
sra x9, x7, x9
lui x29, 463504
bne x28, x0, r32
lui x13, 259928
r32:
lb x10, -44(x8)
jal x0, r33
and x13, x28, x0
r33:
beq x12, x10, r34
lw x7, 40(x8)
add x6, x12, x29
r34:
sub x0, x10, x13
bltu x7, x10, r35
andi x6, x10, 1141
sb x6, 8(x8)
r35:
bge x11, x7, r36
srl x29, x6, x10
lbu x28, -52(x8)
ori x13, x0, -1178
r36:
bge x9, x28, r37
lhu x7, 12(x8)
lui x13, 391211
r37:
jal x0, r38
slli x5, x9, 13
add x6, x0, x9
r38:
la x16, r39
jalr x1, 0(x16)
lw x9, 32(x8)
r39:
lw x6, 28(x8)
sltiu x29, x0, -1405
la x16, r40
jalr x0, 0(x16)
slti x10, x0, 1191
sltu x12, x10, x9
r40:
jal x0, r41
sw x9, 60(x8)
r41:
bgeu x28, x9, r42
lhu x13, 8(x8)
r42:
jal x1, r43
sub x5, x7, x13
r43:
andi x10, x11, -1137
lui x28, 610982
addi x11, x10, 810
xori x12, x0, 512
la x16, r44
jalr x1, 0(x16)
xor x7, x9, x0
sltu x11, x7, x5
r44:
li x17, 3
r45:
slt x7, x28, x5
sll x6, x11, x29
addi x17, x17, -1
bnez x17, r45
bne x7, x11, r46
lw x28, -16(x8)
srl x29, x10, x11
srl x11, x10, x0
r46:
li x17, 3
r47:
slt x5, x10, x12
lb x7, 52(x8)
addi x17, x17, -1
bnez x17, r47
lbu x6, 48(x8)
li x17, 3
r48:
sw x7, -36(x8)
lui x5, 65322
sh x0, -64(x8)
addi x17, x17, -1
bnez x17, r48
beq x13, x6, r49
xori x28, x13, 1953
lw x6, 12(x8)
lui x10, 632986
r49:
sw x0, 16(x8)
blt x12, x28, r50
or x10, x5, x6
lhu x11, 20(x8)
slti x7, x0, 1828
r50:
xor x12, x11, x29
bge x28, x12, r51
lui x12, 426978
r51:
bltu x28, x7, r52
sw x13, 44(x8)
r52:
blt x9, x28, r53
sub x28, x10, x29
sh x0, -64(x8)
r53:
slli x0, x0, 27
bgeu x0, x12, r54
lui x6, 904387
srl x28, x12, x9
r54:
li x17, 3
r55:
sw x13, 8(x8)
lui x10, 125144
lh x12, 20(x8)
slli x7, x10, 10
addi x17, x17, -1
bnez x17, r55
li x17, 3
r56:
sw x0, -8(x8)
sll x13, x11, x29
addi x17, x17, -1
bnez x17, r56
sb x5, -52(x8)
la x16, r57
jalr x1, 0(x16)
srl x11, x10, x13
r57:
jal x0, r58
srl x13, x0, x0
r58:
sltiu x10, x6, -373
bne x6, x6, r59
xor x10, x28, x12
lh x5, -44(x8)
r59:
jal x1, r60
lw x9, 0(x8)
r60:
srli x11, x6, 29
lw x5, 8(x8)
la x16, r61
jalr x0, 0(x16)
and x9, x10, x9
ori x13, x28, 1447
r61:
sw x11, -16(x8)
sw x0, 48(x8)
lui x13, 146198
bge x0, x13, r62
lh x13, 32(x8)
sub x12, x7, x7
r62:
sw x0, 36(x8)
sw x13, -40(x8)
li x17, 3
r63:
srl x29, x0, x13
slt x10, x10, x9
addi x17, x17, -1
bnez x17, r63
lb x7, 20(x8)
bltu x0, x0, r64
srli x11, x6, 17
r64:
la x16, r65
jalr x0, 0(x16)
sw x11, -52(x8)
r65:
addi x13, x5, -1001
xori x13, x11, 1752
beq x29, x10, r66
lw x12, 16(x8)
slti x7, x29, -664
srai x12, x7, 24
r66:
bne x5, x6, r67
addi x0, x28, 792
sltiu x5, x6, 1931
r67:
li x17, 3
r68:
sw x9, -64(x8)
srl x5, x29, x7
sra x5, x10, x6
add x12, x7, x0
addi x17, x17, -1
bnez x17, r68
li x17, 3
r69:
slt x0, x9, x11
sb x7, -32(x8)
lhu x28, 4(x8)
xor x10, x9, x29
addi x17, x17, -1
bnez x17, r69
sb x10, -4(x8)
lui x12, 854312
lui x6, 325158
bgeu x29, x5, r70
sll x29, x13, x0
slti x9, x28, 1526
slti x10, x28, -1701
r70:
or x11, x12, x11
sb x10, -4(x8)
lb x6, 20(x8)
lhu x7, -20(x8)
li x17, 3
r71:
slti x5, x0, -514
sw x29, -44(x8)
sltiu x10, x7, 1602
addi x17, x17, -1
bnez x17, r71
jal x1, r72
addi x5, x9, 1051
slti x29, x28, -1581
r72:
jal x1, r73
lw x5, -60(x8)
srl x5, x10, x13
r73:
lw x5, -48(x8)
sub x13, x29, x0
lui x10, 929587
srl x6, x29, x5
lbu x13, -32(x8)
jal x0, r74
slli x7, x9, 19
r74:
jal x0, r75
srl x7, x6, x0
lui x11, 948120
r75:
li gp, 1
ecall
fail:
ecall

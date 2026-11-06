# constrained-random pipeline stress seed=15 (generated)
li x8, 20480
li x5, 4145683452
li x6, 897563738
li x7, 50056527
li x9, 2239039009
li x10, 3161059941
li x11, 155376646
li x12, 678659458
li x13, 3921364586
li x28, 4236295699
li x29, 1026282353
sw x5, -32(x8)
sw x5, -28(x8)
sw x7, -24(x8)
sw x11, -20(x8)
sw x9, -16(x8)
sw x6, -12(x8)
sw x11, -8(x8)
sw x13, -4(x8)
sw x11, 0(x8)
sw x10, 4(x8)
sw x12, 8(x8)
sw x10, 12(x8)
sw x11, 16(x8)
sw x9, 20(x8)
sw x9, 24(x8)
sw x11, 28(x8)
jal x0, r1
sw x9, 52(x8)
sb x13, 28(x8)
r1:
xori x28, x6, 1968
li x17, 3
r2:
sll x10, x29, x0
sw x28, 60(x8)
addi x17, x17, -1
bnez x17, r2
sw x5, -48(x8)
sw x12, -8(x8)
sb x9, 12(x8)
lhu x5, 56(x8)
sltiu x10, x13, -884
addi x10, x10, -1292
sltu x9, x7, x13
bge x5, x28, r3
ori x11, x13, -150
r3:
jal x1, r4
lb x29, -52(x8)
xori x10, x11, -1590
r4:
bgeu x10, x29, r5
xori x6, x12, -1925
sw x28, -64(x8)
r5:
xor x7, x11, x9
blt x13, x11, r6
lui x10, 713106
r6:
li x17, 3
r7:
lw x7, -40(x8)
sw x11, -32(x8)
addi x17, x17, -1
bnez x17, r7
andi x29, x29, 1918
beq x12, x29, r8
sra x29, x7, x0
r8:
srli x29, x11, 25
srai x9, x6, 29
bgeu x0, x11, r9
sw x5, 4(x8)
sltiu x13, x7, -1554
r9:
sh x6, -48(x8)
bne x0, x0, r10
lw x28, -24(x8)
r10:
la x16, r11
jalr x0, 0(x16)
xor x9, x12, x9
sltiu x5, x29, -847
r11:
xori x5, x13, -647
andi x28, x9, -1853
addi x5, x0, -2018
bge x13, x5, r12
ori x29, x10, 1149
xori x28, x0, -1027
r12:
sw x11, 52(x8)
sll x10, x28, x28
xor x11, x11, x13
sw x6, 12(x8)
la x16, r13
jalr x0, 0(x16)
sltu x12, x7, x13
lbu x11, 56(x8)
r13:
li x17, 3
r14:
lhu x9, 44(x8)
srl x28, x0, x0
addi x17, x17, -1
bnez x17, r14
lui x11, 986393
jal x1, r15
xori x6, x11, 691
sra x28, x9, x0
r15:
bltu x0, x6, r16
lh x29, -12(x8)
r16:
sll x6, x9, x13
li x17, 3
r17:
sw x29, -36(x8)
lh x7, -52(x8)
addi x17, x17, -1
bnez x17, r17
sltiu x11, x28, 378
bltu x11, x11, r18
andi x11, x12, -1983
sh x12, -48(x8)
r18:
bne x12, x7, r19
add x11, x0, x12
r19:
bltu x12, x11, r20
sub x7, x7, x5
r20:
sb x13, -60(x8)
lui x5, 464395
bgeu x7, x28, r21
andi x11, x9, 1445
sb x6, -20(x8)
sltiu x12, x11, -1160
r21:
la x16, r22
jalr x0, 0(x16)
sll x28, x12, x10
r22:
bltu x28, x12, r23
lw x9, 60(x8)
r23:
bne x7, x9, r24
sll x9, x9, x7
r24:
la x16, r25
jalr x1, 0(x16)
sw x9, -60(x8)
xor x7, x12, x6
r25:
lui x9, 115308
bge x5, x13, r26
slti x28, x9, 1277
lw x28, 36(x8)
lhu x9, -48(x8)
r26:
lbu x29, -36(x8)
slt x11, x11, x6
slt x10, x12, x28
beq x29, x0, r27
lb x29, -40(x8)
r27:
li x17, 3
r28:
sw x0, 52(x8)
lb x7, -40(x8)
slti x6, x13, 280
addi x17, x17, -1
bnez x17, r28
xori x9, x29, -32
li x17, 3
r29:
ori x6, x13, 1444
sltu x6, x13, x10
addi x17, x17, -1
bnez x17, r29
xori x10, x11, 32
xor x10, x5, x0
slli x29, x5, 11
jal x0, r30
lw x29, 16(x8)
r30:
jal x1, r31
lw x13, -28(x8)
r31:
jal x0, r32
lui x6, 367203
r32:
slt x9, x12, x10
li x17, 3
r33:
add x29, x0, x11
sb x7, -64(x8)
slli x29, x28, 20
srai x28, x9, 23
addi x17, x17, -1
bnez x17, r33
bge x7, x6, r34
slli x5, x10, 11
r34:
bne x11, x7, r35
sb x12, -36(x8)
lw x10, 60(x8)
sra x13, x9, x0
r35:
sll x10, x10, x10
blt x10, x29, r36
lw x11, 60(x8)
xori x7, x28, 1857
lui x6, 940909
r36:
and x6, x13, x11
srli x10, x12, 26
lui x29, 969127
srl x6, x11, x0
jal x1, r37
lw x11, 56(x8)
r37:
bge x9, x13, r38
sll x11, x0, x0
lh x29, 20(x8)
r38:
sub x5, x13, x29
lw x6, 52(x8)
sh x10, 40(x8)
li x17, 3
r39:
sltu x11, x0, x0
lbu x10, -32(x8)
ori x12, x5, 1026
addi x11, x5, 1712
addi x17, x17, -1
bnez x17, r39
li x17, 3
r40:
sb x12, 52(x8)
and x7, x10, x10
slli x13, x6, 2
slt x11, x6, x28
addi x17, x17, -1
bnez x17, r40
li x17, 3
r41:
sw x13, -20(x8)
sw x0, -24(x8)
xori x11, x28, -922
addi x17, x17, -1
bnez x17, r41
lui x12, 732039
lui x9, 208003
jal x1, r42
sltu x9, x6, x12
lbu x13, -12(x8)
r42:
sltu x28, x11, x12
la x16, r43
jalr x1, 0(x16)
lbu x11, 4(x8)
r43:
bgeu x13, x28, r44
slli x28, x5, 29
lhu x10, -4(x8)
lb x6, -28(x8)
r44:
or x13, x29, x0
lbu x5, -12(x8)
slt x13, x5, x5
bge x7, x7, r45
sh x28, 4(x8)
r45:
bltu x13, x28, r46
add x10, x5, x10
r46:
li x17, 3
r47:
sb x6, 60(x8)
ori x13, x28, 933
slli x7, x13, 24
addi x17, x17, -1
bnez x17, r47
bne x13, x13, r48
lui x11, 480079
or x28, x9, x9
sh x28, -20(x8)
r48:
lui x12, 1023888
li x17, 3
r49:
lw x29, -8(x8)
lhu x9, 56(x8)
add x28, x29, x12
srl x6, x12, x0
addi x17, x17, -1
bnez x17, r49
srai x7, x5, 19
lhu x7, -20(x8)
slt x7, x13, x11
beq x0, x13, r50
sh x10, -32(x8)
sltiu x11, x10, -344
r50:
li x17, 3
r51:
sra x5, x10, x5
lb x11, -8(x8)
sltu x0, x11, x0
sw x5, 12(x8)
addi x17, x17, -1
bnez x17, r51
bge x7, x10, r52
or x7, x0, x6
r52:
lh x9, 32(x8)
sh x5, 16(x8)
la x16, r53
jalr x0, 0(x16)
slli x28, x11, 8
r53:
sll x11, x0, x6
sw x29, 8(x8)
srli x0, x13, 2
lbu x12, 12(x8)
lui x0, 949958
lui x28, 727037
addi x13, x9, 2039
li x17, 3
r54:
slt x11, x5, x0
lw x13, -32(x8)
addi x17, x17, -1
bnez x17, r54
sw x7, -60(x8)
jal x0, r55
lbu x9, -8(x8)
sra x5, x13, x0
r55:
sltu x6, x10, x9
beq x9, x0, r56
xori x28, x10, 100
lb x6, -28(x8)
r56:
slli x13, x13, 24
jal x0, r57
xor x5, x9, x6
sltu x12, x28, x6
r57:
bgeu x28, x12, r58
lh x5, -56(x8)
lui x5, 383048
lhu x7, 4(x8)
r58:
li x17, 3
r59:
lhu x13, 40(x8)
lw x5, -12(x8)
lb x13, -24(x8)
andi x11, x5, 147
addi x17, x17, -1
bnez x17, r59
jal x0, r60
ori x11, x0, 189
lui x12, 610525
r60:
bge x9, x9, r61
sh x13, 4(x8)
slt x0, x10, x9
lui x29, 607778
r61:
lbu x10, 0(x8)
lw x12, -16(x8)
jal x0, r62
sw x0, -16(x8)
r62:
or x13, x29, x7
li x17, 3
r63:
lui x29, 11776
sh x11, -8(x8)
xori x7, x9, 138
sub x11, x5, x0
addi x17, x17, -1
bnez x17, r63
li gp, 1
ecall
fail:
ecall

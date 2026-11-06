# constrained-random pipeline stress seed=16 (generated)
li x8, 20480
li x5, 1552728491
li x6, 2015295599
li x7, 2063648756
li x9, 1223779797
li x10, 1790797914
li x11, 973431509
li x12, 1918816413
li x13, 25140966
li x28, 1758856660
li x29, 3668488870
sw x10, -32(x8)
sw x9, -28(x8)
sw x9, -24(x8)
sw x5, -20(x8)
sw x10, -16(x8)
sw x10, -12(x8)
sw x11, -8(x8)
sw x7, -4(x8)
sw x29, 0(x8)
sw x10, 4(x8)
sw x5, 8(x8)
sw x9, 12(x8)
sw x29, 16(x8)
sw x10, 20(x8)
sw x5, 24(x8)
sw x7, 28(x8)
jal x0, r1
andi x0, x10, -211
lh x9, 40(x8)
r1:
jal x1, r2
ori x6, x10, -1688
add x11, x28, x11
r2:
xor x29, x13, x13
lhu x5, 60(x8)
lhu x13, -44(x8)
slt x29, x12, x11
and x11, x11, x13
sh x11, -40(x8)
bltu x6, x9, r3
addi x7, x0, -1653
r3:
li x17, 3
r4:
sltu x0, x9, x7
lui x11, 512633
sh x10, 32(x8)
addi x17, x17, -1
bnez x17, r4
xori x29, x10, -1729
lw x13, 0(x8)
li x17, 3
r5:
addi x9, x12, -1162
srl x29, x7, x12
srl x28, x12, x28
xor x6, x0, x13
addi x17, x17, -1
bnez x17, r5
jal x1, r6
lhu x6, 12(x8)
r6:
beq x6, x10, r7
andi x10, x13, -335
lui x7, 280036
andi x11, x0, -1169
r7:
blt x5, x13, r8
lw x9, 20(x8)
r8:
srl x9, x10, x12
add x9, x0, x5
slti x29, x5, 157
li x17, 3
r9:
slti x9, x0, -225
or x0, x0, x0
addi x17, x17, -1
bnez x17, r9
blt x28, x5, r10
lui x7, 458571
sltiu x5, x7, 1726
lb x6, -16(x8)
r10:
sb x7, -56(x8)
lui x13, 482046
slli x11, x6, 29
sll x29, x0, x0
jal x0, r11
sub x7, x0, x12
ori x13, x12, -463
r11:
addi x13, x11, -471
jal x0, r12
ori x9, x9, 1330
lh x11, -56(x8)
r12:
andi x6, x7, 1367
addi x11, x12, -1700
la x16, r13
jalr x1, 0(x16)
sll x5, x0, x9
r13:
blt x29, x0, r14
addi x6, x6, -2040
sb x29, 12(x8)
xori x28, x10, 1298
r14:
sb x10, 0(x8)
sw x6, 0(x8)
sw x5, -36(x8)
sw x13, 8(x8)
la x16, r15
jalr x0, 0(x16)
sb x0, -16(x8)
sh x29, -8(x8)
r15:
li x17, 3
r16:
srai x12, x10, 0
sltiu x5, x12, 333
slti x9, x0, -388
addi x17, x17, -1
bnez x17, r16
jal x0, r17
or x6, x6, x0
r17:
la x16, r18
jalr x0, 0(x16)
xor x6, x5, x5
r18:
la x16, r19
jalr x1, 0(x16)
sw x29, 56(x8)
ori x11, x9, 448
r19:
lhu x6, 24(x8)
li x17, 3
r20:
sll x9, x0, x12
sltu x12, x12, x11
addi x17, x17, -1
bnez x17, r20
blt x12, x9, r21
or x6, x5, x11
srl x10, x28, x12
r21:
li x17, 3
r22:
srai x11, x9, 1
sltu x5, x9, x11
addi x17, x17, -1
bnez x17, r22
slt x28, x11, x13
lui x6, 511338
lb x12, -12(x8)
li x17, 3
r23:
addi x29, x9, -932
or x12, x9, x29
sltu x11, x5, x13
sltu x5, x11, x0
addi x17, x17, -1
bnez x17, r23
or x7, x10, x7
blt x11, x6, r24
sltu x9, x0, x9
r24:
la x16, r25
jalr x1, 0(x16)
lb x7, 24(x8)
r25:
xor x11, x11, x11
addi x28, x9, -1291
bge x28, x7, r26
sh x9, -24(x8)
lhu x28, -4(x8)
and x13, x10, x5
r26:
sw x9, -52(x8)
beq x6, x0, r27
add x29, x12, x12
ori x10, x7, -578
andi x7, x29, 1191
r27:
jal x1, r28
srai x12, x7, 22
r28:
bge x12, x13, r29
srl x11, x29, x12
slli x6, x12, 4
r29:
jal x1, r30
and x9, x9, x13
lw x7, 52(x8)
r30:
lui x11, 382012
xor x9, x29, x28
la x16, r31
jalr x0, 0(x16)
xori x13, x9, 599
r31:
ori x11, x11, 211
addi x7, x9, 721
bne x6, x29, r32
sltiu x9, x7, 1007
lw x11, 32(x8)
xori x29, x7, -783
r32:
blt x0, x28, r33
lw x28, -16(x8)
sltu x6, x29, x10
r33:
srai x29, x10, 8
sltiu x5, x0, 479
la x16, r34
jalr x1, 0(x16)
lw x29, 20(x8)
sltiu x13, x5, 1765
r34:
srli x7, x9, 1
addi x13, x0, 1947
jal x1, r35
sltiu x12, x0, 1266
lh x10, 20(x8)
r35:
xor x7, x10, x7
srli x12, x0, 31
sll x12, x12, x10
blt x13, x9, r36
sltiu x9, x0, -58
ori x9, x12, -1570
lui x7, 698672
r36:
sra x28, x13, x6
bge x6, x5, r37
xor x29, x10, x0
sw x10, -44(x8)
sh x7, 60(x8)
r37:
and x0, x5, x7
srli x6, x12, 8
sh x6, -64(x8)
sb x5, 52(x8)
li x17, 3
r38:
addi x9, x13, -272
lw x13, -12(x8)
addi x17, x17, -1
bnez x17, r38
addi x13, x7, -2009
bgeu x10, x6, r39
ori x5, x0, -1611
sh x7, -4(x8)
ori x12, x0, 1567
r39:
jal x1, r40
slti x5, x9, 570
andi x12, x10, -951
r40:
sra x6, x0, x12
slli x11, x6, 17
blt x7, x0, r41
sltiu x9, x28, 954
lui x5, 722405
r41:
add x10, x10, x10
blt x9, x13, r42
xor x7, x0, x0
sw x11, -32(x8)
lui x28, 452730
r42:
jal x0, r43
sra x5, x7, x11
r43:
li x17, 3
r44:
sltu x10, x6, x13
lh x7, 60(x8)
addi x17, x17, -1
bnez x17, r44
blt x9, x9, r45
slti x7, x5, -104
srai x6, x29, 27
lw x12, -16(x8)
r45:
xor x12, x0, x13
lui x28, 373746
blt x0, x11, r46
lbu x29, -36(x8)
r46:
bge x0, x11, r47
lw x11, 28(x8)
sltiu x0, x29, -606
r47:
sra x28, x0, x6
lw x29, -36(x8)
li x17, 3
r48:
add x29, x6, x0
sltu x5, x28, x12
lb x28, 60(x8)
lui x29, 204755
addi x17, x17, -1
bnez x17, r48
sltiu x13, x5, -880
la x16, r49
jalr x0, 0(x16)
sb x29, 40(x8)
sb x10, -28(x8)
r49:
xori x13, x0, 1257
lw x5, 44(x8)
slt x12, x13, x0
li x17, 3
r50:
sltiu x9, x13, 1991
lhu x11, -4(x8)
addi x17, x17, -1
bnez x17, r50
lhu x29, -44(x8)
li x17, 3
r51:
addi x5, x28, 319
lw x10, 40(x8)
sll x9, x28, x13
addi x17, x17, -1
bnez x17, r51
lw x9, 48(x8)
slli x9, x7, 11
sw x10, -60(x8)
xor x9, x0, x0
li x17, 3
r52:
srli x13, x7, 29
sw x6, -60(x8)
sltu x10, x10, x10
srl x12, x28, x13
addi x17, x17, -1
bnez x17, r52
sll x11, x29, x13
beq x12, x0, r53
slli x11, x5, 10
or x10, x5, x9
r53:
slt x13, x5, x0
sh x6, 24(x8)
sw x13, 24(x8)
jal x0, r54
andi x13, x29, -1579
r54:
sub x9, x12, x7
slti x9, x13, 1321
bltu x13, x28, r55
lb x11, 32(x8)
lhu x12, 12(x8)
sll x10, x6, x29
r55:
lui x10, 852544
li x17, 3
r56:
slli x5, x9, 1
addi x12, x7, -607
addi x17, x17, -1
bnez x17, r56
bne x5, x10, r57
addi x11, x28, 1956
lw x9, 0(x8)
r57:
ori x5, x29, 926
bltu x0, x11, r58
slti x11, x13, 1972
srli x13, x28, 16
lui x29, 927941
r58:
sra x13, x0, x7
bgeu x5, x11, r59
sb x29, 48(x8)
r59:
sh x13, -32(x8)
ori x13, x9, 1789
beq x0, x9, r60
and x6, x13, x11
lb x11, 20(x8)
r60:
lw x12, 36(x8)
srai x13, x28, 19
li x17, 3
r61:
sw x9, -4(x8)
sh x11, 32(x8)
sll x28, x29, x0
srai x28, x13, 24
addi x17, x17, -1
bnez x17, r61
li x17, 3
r62:
sub x6, x28, x9
sh x13, 8(x8)
addi x17, x17, -1
bnez x17, r62
li gp, 1
ecall
fail:
ecall

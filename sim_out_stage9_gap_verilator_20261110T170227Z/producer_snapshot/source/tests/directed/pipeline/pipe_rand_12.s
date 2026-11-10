# constrained-random pipeline stress seed=12 (generated)
li x8, 20480
li x5, 2038265566
li x6, 1155324522
li x7, 2823822892
li x9, 2272599372
li x10, 2862211193
li x11, 1502316763
li x12, 612463845
li x13, 1639135743
li x28, 46645234
li x29, 4280459899
sw x11, -32(x8)
sw x13, -28(x8)
sw x10, -24(x8)
sw x13, -20(x8)
sw x29, -16(x8)
sw x9, -12(x8)
sw x28, -8(x8)
sw x5, -4(x8)
sw x29, 0(x8)
sw x7, 4(x8)
sw x13, 8(x8)
sw x11, 12(x8)
sw x7, 16(x8)
sw x11, 20(x8)
sw x9, 24(x8)
sw x5, 28(x8)
bne x6, x28, r1
lw x11, -44(x8)
or x9, x9, x6
sw x6, 44(x8)
r1:
li x17, 3
r2:
ori x29, x7, -1628
slli x7, x12, 26
lhu x5, 32(x8)
slli x11, x0, 16
addi x17, x17, -1
bnez x17, r2
andi x10, x10, -1116
ori x9, x29, -579
lb x13, -60(x8)
slti x10, x29, -1208
jal x0, r3
add x13, x12, x10
r3:
lui x9, 963142
xori x29, x0, 1892
sw x7, -16(x8)
jal x0, r4
sh x9, -64(x8)
r4:
xor x13, x28, x28
sb x9, 56(x8)
andi x28, x7, 1628
sw x28, 48(x8)
bne x0, x10, r5
add x5, x7, x28
sh x9, -16(x8)
ori x9, x29, 64
r5:
jal x1, r6
lui x11, 417315
lui x7, 772737
r6:
bge x29, x7, r7
lb x29, -56(x8)
r7:
li x17, 3
r8:
slli x10, x0, 22
or x13, x13, x29
lui x9, 826607
addi x17, x17, -1
bnez x17, r8
beq x12, x11, r9
sll x6, x0, x6
lw x29, -20(x8)
r9:
jal x1, r10
sra x9, x29, x13
andi x9, x29, 747
r10:
sh x5, 28(x8)
sw x9, -28(x8)
lw x5, 52(x8)
srli x11, x13, 3
la x16, r11
jalr x0, 0(x16)
srai x11, x0, 28
lw x12, 12(x8)
r11:
lw x5, 60(x8)
li x17, 3
r12:
xori x28, x9, -947
srl x7, x11, x10
ori x0, x10, 1139
lh x28, -28(x8)
addi x17, x17, -1
bnez x17, r12
lw x28, 32(x8)
lui x12, 712700
xori x10, x7, -657
jal x1, r13
sb x0, 24(x8)
r13:
li x17, 3
r14:
lw x29, -12(x8)
lw x6, 12(x8)
slt x5, x7, x9
addi x17, x17, -1
bnez x17, r14
blt x9, x7, r15
srai x6, x6, 23
lbu x10, 48(x8)
r15:
srl x28, x28, x13
bge x11, x0, r16
sb x0, 4(x8)
sra x29, x11, x0
r16:
sw x29, 28(x8)
jal x0, r17
srl x12, x6, x5
lb x11, -36(x8)
r17:
bltu x29, x0, r18
lw x6, -8(x8)
lui x5, 433252
xori x6, x0, 540
r18:
jal x1, r19
lb x6, 28(x8)
r19:
and x6, x7, x0
sra x13, x12, x0
sltiu x5, x29, 1078
jal x1, r20
or x29, x29, x11
srl x6, x10, x29
r20:
bltu x0, x13, r21
srl x6, x6, x6
lhu x0, -20(x8)
ori x29, x29, 214
r21:
sltiu x7, x28, 1719
lui x9, 675987
bltu x11, x7, r22
addi x11, x28, 643
lw x10, -40(x8)
r22:
la x16, r23
jalr x0, 0(x16)
sh x13, -8(x8)
slt x10, x9, x10
r23:
bgeu x9, x29, r24
xori x29, x7, 1913
r24:
sltiu x9, x0, -439
srai x6, x0, 21
addi x6, x0, 344
sh x0, 40(x8)
bne x10, x12, r25
lb x29, 48(x8)
slt x29, x7, x9
r25:
lw x10, 60(x8)
sll x7, x9, x12
la x16, r26
jalr x1, 0(x16)
lbu x28, -40(x8)
lb x12, 48(x8)
r26:
lui x6, 121295
srl x6, x11, x12
srli x9, x28, 25
sw x7, -60(x8)
sltu x29, x10, x9
srl x7, x28, x6
jal x0, r27
lw x9, 8(x8)
addi x13, x6, -896
r27:
or x7, x7, x7
sh x12, -60(x8)
blt x13, x29, r28
lw x5, 0(x8)
lhu x28, 44(x8)
r28:
sw x11, 8(x8)
sltiu x12, x11, -1720
bltu x28, x29, r29
sw x7, -52(x8)
sh x6, -44(x8)
sh x0, 44(x8)
r29:
li x17, 3
r30:
addi x13, x12, -255
sw x5, 16(x8)
lbu x5, -8(x8)
lui x12, 1004728
addi x17, x17, -1
bnez x17, r30
lw x5, -16(x8)
bge x28, x12, r31
andi x7, x7, -667
slli x28, x6, 12
lbu x9, 0(x8)
r31:
blt x13, x0, r32
srai x13, x12, 12
sll x12, x0, x29
r32:
srai x5, x11, 10
andi x6, x7, -744
li x17, 3
r33:
lui x11, 481445
sll x6, x10, x28
srai x11, x0, 16
addi x17, x17, -1
bnez x17, r33
sltiu x11, x28, -1806
sll x9, x9, x0
sb x0, -60(x8)
lhu x29, 12(x8)
beq x13, x0, r34
lw x10, -44(x8)
slli x28, x7, 25
add x6, x7, x6
r34:
sltu x9, x10, x0
sh x13, -40(x8)
la x16, r35
jalr x1, 0(x16)
sltiu x13, x6, -1181
andi x10, x11, 55
r35:
jal x1, r36
addi x13, x12, -1989
sra x28, x0, x28
r36:
la x16, r37
jalr x1, 0(x16)
lbu x11, 48(x8)
sltu x28, x28, x10
r37:
li x17, 3
r38:
xor x7, x13, x12
slli x6, x6, 26
addi x17, x17, -1
bnez x17, r38
lui x10, 12352
sltu x10, x11, x11
sltiu x11, x9, -1560
add x29, x0, x9
add x29, x11, x28
la x16, r39
jalr x1, 0(x16)
and x13, x6, x6
r39:
la x16, r40
jalr x1, 0(x16)
sll x0, x0, x13
slti x12, x0, -815
r40:
lb x9, 56(x8)
srli x11, x0, 0
li x17, 3
r41:
srli x0, x6, 21
sw x0, -40(x8)
addi x17, x17, -1
bnez x17, r41
li x17, 3
r42:
ori x13, x10, 1898
ori x13, x9, 1852
addi x17, x17, -1
bnez x17, r42
lui x13, 15766
li x17, 3
r43:
sra x10, x10, x28
lui x10, 434599
and x6, x5, x7
addi x17, x17, -1
bnez x17, r43
lw x13, -8(x8)
li x17, 3
r44:
slti x13, x7, 778
sw x11, -20(x8)
sb x28, -40(x8)
sw x0, 40(x8)
addi x17, x17, -1
bnez x17, r44
bge x11, x0, r45
andi x10, x29, -2003
sub x9, x28, x28
r45:
or x7, x5, x5
li x17, 3
r46:
ori x28, x5, 1613
sb x7, 24(x8)
addi x17, x17, -1
bnez x17, r46
sw x0, 4(x8)
slt x11, x11, x9
and x6, x13, x9
jal x0, r47
sll x12, x12, x12
r47:
srai x28, x13, 27
sra x13, x13, x6
blt x10, x5, r48
srl x7, x29, x29
r48:
jal x0, r49
sw x10, -8(x8)
r49:
and x28, x29, x13
addi x0, x7, 225
bltu x29, x13, r50
xor x6, x29, x29
r50:
jal x0, r51
slti x11, x29, 1385
sb x9, 8(x8)
r51:
sw x0, -28(x8)
lw x10, -16(x8)
bltu x12, x6, r52
sb x10, 44(x8)
andi x29, x9, 602
r52:
li x17, 3
r53:
sh x0, -20(x8)
sh x10, 12(x8)
addi x17, x17, -1
bnez x17, r53
sw x7, 4(x8)
sh x28, -8(x8)
lui x5, 23204
bltu x28, x0, r54
sll x29, x11, x13
lw x28, -36(x8)
ori x28, x12, 1267
r54:
srli x5, x13, 19
bgeu x29, x11, r55
sw x7, 4(x8)
ori x7, x28, -978
sltiu x10, x7, -868
r55:
li gp, 1
ecall
fail:
ecall

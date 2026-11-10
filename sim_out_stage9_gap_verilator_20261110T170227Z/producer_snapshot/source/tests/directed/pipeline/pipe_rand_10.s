# constrained-random pipeline stress seed=10 (generated)
li x8, 20480
li x5, 2454155475
li x6, 139951793
li x7, 1842064464
li x9, 2072586604
li x10, 2482883256
li x11, 63704871
li x12, 885185152
li x13, 1986768135
li x28, 3493188185
li x29, 2110102074
sw x10, -32(x8)
sw x7, -28(x8)
sw x5, -24(x8)
sw x28, -20(x8)
sw x13, -16(x8)
sw x11, -12(x8)
sw x6, -8(x8)
sw x9, -4(x8)
sw x11, 0(x8)
sw x5, 4(x8)
sw x12, 8(x8)
sw x7, 12(x8)
sw x29, 16(x8)
sw x11, 20(x8)
sw x12, 24(x8)
sw x12, 28(x8)
lbu x29, 12(x8)
bne x13, x9, r1
lui x7, 8504
sltu x7, x28, x11
r1:
jal x0, r2
lhu x28, 56(x8)
xor x13, x28, x7
r2:
la x16, r3
jalr x1, 0(x16)
sltu x6, x29, x0
r3:
sh x12, 28(x8)
li x17, 3
r4:
sra x12, x7, x9
sw x13, -4(x8)
addi x17, x17, -1
bnez x17, r4
bne x29, x28, r5
sw x10, -24(x8)
r5:
bne x7, x13, r6
addi x10, x28, -1691
slti x5, x6, 96
r6:
lui x10, 1039684
bne x0, x28, r7
srli x28, x6, 10
xori x29, x7, 1396
r7:
xori x10, x0, -690
beq x12, x5, r8
addi x10, x11, -1289
r8:
lui x6, 292132
xori x7, x11, 74
li x17, 3
r9:
andi x6, x28, -790
lw x5, -56(x8)
lw x13, 56(x8)
sltu x13, x12, x9
addi x17, x17, -1
bnez x17, r9
beq x5, x29, r10
lw x12, 8(x8)
sll x5, x11, x29
sltiu x7, x7, -1395
r10:
bge x9, x6, r11
sw x13, -12(x8)
sub x9, x0, x0
and x13, x12, x12
r11:
la x16, r12
jalr x0, 0(x16)
lw x11, -52(x8)
r12:
slti x13, x0, 266
or x6, x10, x12
xori x13, x13, 1859
beq x0, x28, r13
slti x11, x29, 1357
lw x10, 12(x8)
xor x5, x6, x0
r13:
slti x28, x9, -668
slli x9, x29, 4
li x17, 3
r14:
srai x28, x5, 25
slt x12, x28, x29
addi x17, x17, -1
bnez x17, r14
jal x1, r15
lb x13, -56(x8)
r15:
bge x11, x29, r16
sub x5, x29, x11
sw x6, 36(x8)
addi x7, x7, 1595
r16:
bltu x13, x0, r17
sw x12, 20(x8)
sw x12, -16(x8)
r17:
lw x7, -20(x8)
bne x29, x12, r18
srai x9, x5, 10
addi x10, x29, -601
r18:
srli x6, x5, 25
bge x6, x11, r19
xori x5, x13, 641
r19:
la x16, r20
jalr x0, 0(x16)
lui x12, 321147
r20:
sb x12, -36(x8)
sltiu x0, x0, 327
sw x28, 56(x8)
bltu x10, x5, r21
slt x10, x6, x28
lui x5, 209139
srai x11, x9, 18
r21:
sb x6, 36(x8)
jal x0, r22
andi x6, x5, 888
slti x5, x5, -364
r22:
sh x9, 32(x8)
bltu x29, x12, r23
lb x28, -36(x8)
sll x9, x6, x0
andi x5, x12, -551
r23:
beq x28, x7, r24
lhu x13, 52(x8)
r24:
sra x0, x13, x0
bgeu x6, x7, r25
sra x11, x5, x7
sltu x9, x7, x6
r25:
xor x29, x5, x29
sw x28, -28(x8)
bgeu x5, x29, r26
lb x10, -12(x8)
r26:
sh x5, 28(x8)
lh x5, 52(x8)
la x16, r27
jalr x0, 0(x16)
sll x28, x13, x0
r27:
li x17, 3
r28:
slti x5, x5, 1964
lui x5, 984947
addi x17, x17, -1
bnez x17, r28
bne x13, x28, r29
lw x12, 32(x8)
xor x5, x7, x5
r29:
lw x9, -52(x8)
lw x11, -56(x8)
sw x9, 56(x8)
la x16, r30
jalr x0, 0(x16)
sra x9, x12, x10
r30:
srl x0, x28, x0
lw x11, -28(x8)
la x16, r31
jalr x0, 0(x16)
lw x10, -16(x8)
sh x29, -32(x8)
r31:
slti x11, x5, 1672
slt x10, x9, x11
sra x9, x12, x11
ori x28, x0, -1655
sub x5, x12, x12
li x17, 3
r32:
xori x10, x28, -1392
sw x29, 56(x8)
addi x17, x17, -1
bnez x17, r32
li x17, 3
r33:
xori x13, x13, -240
xori x6, x13, 1991
addi x17, x17, -1
bnez x17, r33
blt x28, x0, r34
xori x10, x13, 1783
r34:
sw x29, -60(x8)
sltiu x29, x7, -128
lui x9, 56846
lb x7, -24(x8)
lw x5, -16(x8)
ori x7, x9, -1757
lw x29, 24(x8)
lui x7, 542908
slt x29, x6, x28
bge x10, x11, r35
srai x6, x10, 27
xor x5, x13, x0
r35:
ori x5, x9, 587
srl x13, x0, x5
jal x0, r36
lhu x9, -36(x8)
r36:
lw x7, -48(x8)
sw x13, -44(x8)
li x17, 3
r37:
sb x9, -20(x8)
or x11, x9, x0
xori x10, x12, -492
sra x9, x0, x7
addi x17, x17, -1
bnez x17, r37
jal x0, r38
lw x9, -20(x8)
r38:
lw x0, -64(x8)
bne x0, x0, r39
sw x13, -20(x8)
lbu x5, 32(x8)
addi x7, x12, -1289
r39:
sltu x10, x9, x10
blt x10, x28, r40
lw x7, -32(x8)
lw x5, 48(x8)
r40:
bge x29, x29, r41
srl x28, x9, x13
r41:
sltu x6, x7, x0
la x16, r42
jalr x0, 0(x16)
lb x9, -52(x8)
srl x9, x28, x28
r42:
lui x9, 612606
bge x0, x11, r43
sltu x12, x0, x11
lb x11, 0(x8)
r43:
blt x13, x12, r44
sll x13, x28, x29
sra x5, x11, x12
r44:
la x16, r45
jalr x0, 0(x16)
sh x5, -52(x8)
lw x5, -28(x8)
r45:
xor x29, x10, x10
lw x7, -48(x8)
bgeu x29, x9, r46
lw x11, 4(x8)
slli x28, x28, 27
r46:
blt x13, x29, r47
sra x6, x13, x10
lhu x10, -64(x8)
ori x13, x0, 1804
r47:
li x17, 3
r48:
andi x5, x10, -1183
addi x11, x10, 1525
addi x17, x17, -1
bnez x17, r48
slli x6, x28, 18
blt x29, x9, r49
lbu x13, 16(x8)
slt x5, x13, x5
lui x5, 281662
r49:
slli x7, x28, 6
lui x29, 630247
sw x0, -64(x8)
sb x5, -24(x8)
li x17, 3
r50:
ori x13, x29, 1917
ori x6, x9, 898
slli x13, x29, 0
addi x17, x17, -1
bnez x17, r50
jal x0, r51
sub x11, x13, x12
r51:
bge x11, x0, r52
lui x6, 428051
r52:
blt x5, x10, r53
sw x12, -44(x8)
r53:
jal x1, r54
xori x6, x0, 1845
r54:
sw x5, 28(x8)
addi x13, x6, -652
lb x12, -48(x8)
li x17, 3
r55:
sw x11, 20(x8)
sw x12, 0(x8)
sb x13, -8(x8)
addi x17, x17, -1
bnez x17, r55
li gp, 1
ecall
fail:
ecall

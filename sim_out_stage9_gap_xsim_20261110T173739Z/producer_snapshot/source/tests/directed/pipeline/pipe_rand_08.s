# constrained-random pipeline stress seed=8 (generated)
li x8, 20480
li x5, 973694259
li x6, 1590906853
li x7, 4133025703
li x9, 1612199532
li x10, 542587089
li x11, 829429670
li x12, 3027165658
li x13, 188027056
li x28, 365867937
li x29, 587736274
sw x9, -32(x8)
sw x28, -28(x8)
sw x9, -24(x8)
sw x12, -20(x8)
sw x5, -16(x8)
sw x13, -12(x8)
sw x13, -8(x8)
sw x13, -4(x8)
sw x12, 0(x8)
sw x13, 4(x8)
sw x29, 8(x8)
sw x9, 12(x8)
sw x12, 16(x8)
sw x6, 20(x8)
sw x13, 24(x8)
sw x9, 28(x8)
jal x1, r1
andi x10, x6, 68
srl x10, x29, x12
r1:
sub x11, x13, x0
and x29, x6, x28
li x17, 3
r2:
lw x29, 52(x8)
lh x28, 24(x8)
sh x7, -40(x8)
addi x17, x17, -1
bnez x17, r2
andi x7, x13, -429
ori x28, x0, -1463
jal x0, r3
sltu x5, x11, x9
sltu x13, x12, x10
r3:
la x16, r4
jalr x1, 0(x16)
lbu x13, -60(x8)
r4:
lb x29, -64(x8)
jal x1, r5
lhu x12, -8(x8)
sra x12, x12, x12
r5:
add x12, x6, x0
slli x9, x28, 31
bltu x6, x9, r6
sw x0, -36(x8)
r6:
blt x11, x11, r7
lbu x6, -52(x8)
r7:
la x16, r8
jalr x0, 0(x16)
sra x13, x6, x6
r8:
sll x5, x12, x6
lw x28, 48(x8)
and x5, x12, x11
sra x9, x6, x6
and x28, x5, x0
andi x11, x29, -405
andi x10, x28, -441
lui x11, 673248
li x17, 3
r9:
sub x28, x28, x12
sw x28, 12(x8)
lui x7, 620394
addi x17, x17, -1
bnez x17, r9
beq x9, x13, r10
sltiu x13, x9, 331
andi x10, x28, 866
r10:
jal x1, r11
or x9, x6, x10
sltu x6, x12, x6
r11:
blt x10, x10, r12
srl x0, x9, x11
or x11, x0, x13
or x28, x9, x11
r12:
srl x13, x6, x0
slli x13, x7, 1
bgeu x10, x6, r13
ori x28, x6, -1014
r13:
bgeu x6, x11, r14
lw x11, -32(x8)
r14:
blt x6, x9, r15
slt x5, x10, x0
addi x5, x28, -1115
sw x12, -24(x8)
r15:
sw x0, -48(x8)
sll x28, x11, x0
sh x7, 16(x8)
sra x7, x6, x29
beq x7, x0, r16
srl x9, x7, x7
r16:
ori x28, x0, 305
sw x0, 60(x8)
la x16, r17
jalr x0, 0(x16)
sll x5, x10, x13
lui x7, 606370
r17:
jal x1, r18
lb x5, 8(x8)
r18:
or x9, x10, x11
add x29, x6, x7
sb x11, -56(x8)
li x17, 3
r19:
lb x7, 16(x8)
lw x5, -24(x8)
lh x5, 24(x8)
sw x0, -56(x8)
addi x17, x17, -1
bnez x17, r19
bgeu x0, x0, r20
or x10, x11, x13
slti x11, x10, -906
r20:
beq x13, x0, r21
lui x12, 952733
sw x13, 48(x8)
r21:
beq x13, x0, r22
andi x13, x6, 912
lh x29, 56(x8)
r22:
bne x28, x28, r23
lui x29, 72350
slt x29, x7, x0
addi x7, x5, -1749
r23:
lh x5, -60(x8)
li x17, 3
r24:
and x28, x10, x0
slti x7, x11, 546
sh x5, -40(x8)
srli x7, x0, 26
addi x17, x17, -1
bnez x17, r24
li x17, 3
r25:
slli x10, x0, 22
sb x10, 40(x8)
lb x7, 8(x8)
addi x17, x17, -1
bnez x17, r25
slti x5, x5, 1203
jal x1, r26
ori x13, x5, 1278
lbu x9, -36(x8)
r26:
jal x1, r27
lbu x5, -44(x8)
r27:
sw x13, 28(x8)
bltu x7, x13, r28
and x6, x7, x28
r28:
slt x28, x11, x0
lhu x10, 16(x8)
li x17, 3
r29:
lhu x28, -60(x8)
sw x10, -36(x8)
addi x17, x17, -1
bnez x17, r29
lhu x28, -64(x8)
slli x7, x5, 20
addi x13, x29, -613
sb x28, -60(x8)
lui x10, 125540
xori x5, x29, -752
li x17, 3
r30:
lb x0, 56(x8)
lw x13, -4(x8)
sb x28, 36(x8)
sw x0, -24(x8)
addi x17, x17, -1
bnez x17, r30
li x17, 3
r31:
sh x11, 8(x8)
srai x11, x6, 28
slli x29, x0, 22
andi x9, x12, 207
addi x17, x17, -1
bnez x17, r31
sra x5, x10, x0
li x17, 3
r32:
srai x10, x10, 4
or x12, x6, x7
xor x6, x29, x9
addi x17, x17, -1
bnez x17, r32
bge x9, x12, r33
slli x29, x28, 31
r33:
bltu x6, x13, r34
addi x6, x6, -465
sw x6, -32(x8)
srl x28, x13, x11
r34:
bgeu x12, x29, r35
lw x5, 40(x8)
r35:
la x16, r36
jalr x0, 0(x16)
sltu x7, x29, x28
r36:
la x16, r37
jalr x0, 0(x16)
sw x11, -44(x8)
r37:
jal x1, r38
sh x9, 32(x8)
sb x7, -8(x8)
r38:
lhu x29, 8(x8)
la x16, r39
jalr x1, 0(x16)
addi x28, x12, 1570
r39:
li x17, 3
r40:
sltiu x10, x5, -1216
xor x29, x0, x0
andi x12, x11, -1712
addi x17, x17, -1
bnez x17, r40
bne x29, x6, r41
ori x9, x5, -1618
lh x12, -32(x8)
xor x9, x28, x0
r41:
lw x11, -16(x8)
srl x0, x5, x9
lbu x5, 4(x8)
xor x5, x28, x12
jal x0, r42
sw x7, -60(x8)
lw x6, -56(x8)
r42:
blt x28, x7, r43
sh x5, -32(x8)
lw x9, -32(x8)
r43:
sltiu x12, x0, 427
bgeu x7, x11, r44
andi x29, x9, 570
lh x10, -64(x8)
r44:
la x16, r45
jalr x1, 0(x16)
and x5, x13, x0
r45:
sh x5, -64(x8)
lui x9, 702899
la x16, r46
jalr x0, 0(x16)
srli x9, x13, 18
ori x9, x12, 1974
r46:
la x16, r47
jalr x0, 0(x16)
srli x13, x28, 24
lui x9, 416176
r47:
jal x0, r48
sltiu x11, x28, 712
lw x5, 12(x8)
r48:
xori x12, x11, -1549
sll x12, x11, x7
la x16, r49
jalr x0, 0(x16)
srl x9, x29, x28
r49:
sh x0, 0(x8)
sub x5, x11, x6
bltu x28, x10, r50
sll x13, x0, x0
xor x13, x10, x11
lw x28, -52(x8)
r50:
la x16, r51
jalr x0, 0(x16)
sra x28, x11, x12
xor x9, x29, x0
r51:
xori x11, x7, 156
li x17, 3
r52:
slt x6, x0, x28
sltiu x28, x9, 478
addi x17, x17, -1
bnez x17, r52
li gp, 1
ecall
fail:
ecall

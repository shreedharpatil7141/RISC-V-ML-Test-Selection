# constrained-random pipeline stress seed=5 (generated)
li x8, 20480
li x5, 2675342405
li x6, 1097127993
li x7, 3185950873
li x9, 1539898300
li x10, 3415330359
li x11, 2965446622
li x12, 4047793130
li x13, 3614262064
li x28, 3177840169
li x29, 2800454814
sw x28, -32(x8)
sw x5, -28(x8)
sw x13, -24(x8)
sw x9, -20(x8)
sw x5, -16(x8)
sw x7, -12(x8)
sw x6, -8(x8)
sw x11, -4(x8)
sw x13, 0(x8)
sw x9, 4(x8)
sw x12, 8(x8)
sw x28, 12(x8)
sw x6, 16(x8)
sw x29, 20(x8)
sw x9, 24(x8)
sw x5, 28(x8)
bge x10, x7, r1
sll x10, x29, x29
addi x28, x5, -333
r1:
jal x0, r2
or x7, x0, x0
r2:
sw x10, -60(x8)
sltu x29, x6, x11
lui x5, 708621
xori x29, x0, 538
addi x6, x10, -1861
li x17, 3
r3:
sw x11, 32(x8)
srli x5, x5, 11
lui x7, 249604
addi x17, x17, -1
bnez x17, r3
jal x1, r4
srli x9, x13, 6
lui x9, 620471
r4:
sh x11, 28(x8)
li x17, 3
r5:
sub x10, x10, x0
addi x6, x0, -829
lhu x29, -24(x8)
addi x17, x17, -1
bnez x17, r5
beq x29, x28, r6
xor x28, x10, x13
lb x29, -56(x8)
r6:
jal x1, r7
sll x12, x0, x12
r7:
addi x29, x12, 367
sh x28, 52(x8)
li x17, 3
r8:
lh x5, 8(x8)
addi x29, x12, -579
lui x6, 709841
sltu x6, x28, x28
addi x17, x17, -1
bnez x17, r8
la x16, r9
jalr x1, 0(x16)
lw x7, -56(x8)
r9:
jal x1, r10
lw x12, 8(x8)
sh x29, -64(x8)
r10:
lw x5, 4(x8)
lh x7, 4(x8)
bgeu x12, x11, r11
sw x11, -28(x8)
r11:
sra x9, x10, x0
lbu x12, 40(x8)
srli x0, x0, 1
lui x29, 379045
lw x0, -56(x8)
li x17, 3
r12:
sub x28, x11, x7
addi x11, x12, 1763
addi x17, x17, -1
bnez x17, r12
lw x10, -12(x8)
sw x12, 4(x8)
la x16, r13
jalr x0, 0(x16)
sw x6, 8(x8)
srai x6, x10, 22
r13:
jal x1, r14
lh x10, 52(x8)
srl x28, x29, x13
r14:
li x17, 3
r15:
lui x7, 1987
ori x5, x29, -896
addi x17, x17, -1
bnez x17, r15
sw x12, 44(x8)
li x17, 3
r16:
srl x10, x7, x29
lui x29, 1040828
xor x6, x10, x13
addi x17, x17, -1
bnez x17, r16
li x17, 3
r17:
andi x13, x29, 1584
sll x7, x12, x5
addi x17, x17, -1
bnez x17, r17
srli x11, x5, 15
sw x13, 56(x8)
sb x7, 12(x8)
lh x29, -60(x8)
slti x13, x5, -2025
andi x12, x28, -482
lw x13, 56(x8)
la x16, r18
jalr x1, 0(x16)
sltiu x7, x13, -1507
andi x5, x12, 297
r18:
bge x10, x7, r19
xori x11, x11, -791
r19:
slli x9, x0, 14
add x10, x11, x0
sra x11, x5, x6
la x16, r20
jalr x0, 0(x16)
lh x28, 48(x8)
r20:
lui x12, 338018
sub x11, x0, x12
blt x5, x29, r21
and x11, x7, x5
andi x5, x29, 1961
addi x9, x7, 366
r21:
lui x7, 608670
li x17, 3
r22:
srli x10, x6, 15
or x28, x7, x9
sw x7, -32(x8)
lb x6, -56(x8)
addi x17, x17, -1
bnez x17, r22
sra x28, x9, x12
la x16, r23
jalr x1, 0(x16)
add x9, x28, x0
xori x29, x0, -221
r23:
beq x0, x13, r24
srl x29, x11, x9
r24:
sw x12, -32(x8)
blt x0, x10, r25
ori x9, x5, -288
lb x11, -40(x8)
slt x6, x9, x5
r25:
sb x12, 56(x8)
sw x13, 52(x8)
sub x5, x11, x12
la x16, r26
jalr x1, 0(x16)
srli x13, x7, 18
r26:
beq x13, x5, r27
sw x5, -60(x8)
lw x5, -28(x8)
r27:
lhu x28, -4(x8)
bne x5, x9, r28
sub x10, x29, x12
sw x7, 52(x8)
andi x10, x0, 1786
r28:
add x9, x0, x29
sw x5, 48(x8)
jal x1, r29
or x11, x29, x11
r29:
li x17, 3
r30:
sub x6, x13, x5
lhu x9, 36(x8)
lh x9, 40(x8)
addi x0, x5, -455
addi x17, x17, -1
bnez x17, r30
slli x11, x28, 14
addi x12, x28, -722
bgeu x9, x29, r31
xori x7, x12, 1037
r31:
sltu x5, x0, x13
li x17, 3
r32:
srli x28, x13, 5
lw x12, 36(x8)
addi x17, x17, -1
bnez x17, r32
sra x11, x9, x0
andi x12, x9, 211
lw x9, -16(x8)
jal x1, r33
srl x5, x28, x5
r33:
li x17, 3
r34:
sb x13, -28(x8)
lw x6, -52(x8)
lb x13, 32(x8)
slli x5, x10, 10
addi x17, x17, -1
bnez x17, r34
sltiu x5, x5, -1528
lb x6, -36(x8)
srl x7, x10, x29
srli x28, x9, 21
sll x29, x0, x6
lui x0, 302059
sb x11, 16(x8)
srl x28, x7, x13
lw x5, 56(x8)
li x17, 3
r35:
srl x28, x0, x5
add x5, x29, x9
xori x7, x13, -282
sltu x7, x28, x28
addi x17, x17, -1
bnez x17, r35
lh x11, 24(x8)
jal x0, r36
slti x29, x9, 1967
slti x12, x12, -1240
r36:
jal x1, r37
lhu x5, 56(x8)
r37:
la x16, r38
jalr x0, 0(x16)
addi x5, x28, -535
r38:
jal x0, r39
lh x29, 32(x8)
srai x10, x0, 25
r39:
lw x13, -52(x8)
lw x9, -60(x8)
bltu x9, x10, r40
xor x11, x29, x29
sw x5, 4(x8)
r40:
li x17, 3
r41:
sltu x11, x11, x0
lw x28, -12(x8)
addi x17, x17, -1
bnez x17, r41
li gp, 1
ecall
fail:
ecall

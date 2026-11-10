# constrained-random pipeline stress seed=1 (generated)
li x8, 20480
li x5, 577090037
li x6, 2444712010
li x7, 3639700191
li x9, 3445702192
li x10, 3280387012
li x11, 271041745
li x12, 1095513148
li x13, 506456969
li x28, 2127877499
li x29, 3268308804
sw x13, -32(x8)
sw x13, -28(x8)
sw x12, -24(x8)
sw x9, -20(x8)
sw x6, -16(x8)
sw x13, -12(x8)
sw x5, -8(x8)
sw x12, -4(x8)
sw x12, 0(x8)
sw x29, 4(x8)
sw x5, 8(x8)
sw x13, 12(x8)
sw x10, 16(x8)
sw x9, 20(x8)
sw x29, 24(x8)
sw x6, 28(x8)
li x17, 3
r1:
add x10, x12, x0
add x13, x28, x9
addi x17, x17, -1
bnez x17, r1
jal x1, r2
xori x10, x10, -1872
r2:
sh x0, 8(x8)
xori x7, x28, -493
lui x6, 824922
beq x13, x9, r3
lw x12, -20(x8)
addi x9, x13, -1164
lw x9, 36(x8)
r3:
lb x5, 12(x8)
bltu x29, x29, r4
lw x5, -8(x8)
sh x12, 24(x8)
r4:
li x17, 3
r5:
andi x13, x28, -2002
slti x7, x28, -365
xori x9, x11, -411
sw x11, 40(x8)
addi x17, x17, -1
bnez x17, r5
srai x29, x11, 29
bne x0, x7, r6
lui x11, 535390
sub x10, x5, x13
slt x13, x10, x6
r6:
jal x0, r7
sll x5, x10, x28
sw x13, 16(x8)
r7:
srl x29, x11, x12
jal x1, r8
slt x7, x29, x12
r8:
jal x0, r9
add x29, x0, x7
r9:
srai x13, x9, 28
lw x11, 16(x8)
bge x5, x0, r10
add x9, x10, x6
sw x0, -24(x8)
r10:
or x5, x5, x29
jal x1, r11
lw x29, -56(x8)
r11:
ori x9, x0, 1498
bge x6, x0, r12
add x6, x11, x29
sb x7, -16(x8)
r12:
la x16, r13
jalr x0, 0(x16)
andi x13, x6, 1058
sw x28, -4(x8)
r13:
sll x28, x7, x28
lw x28, 0(x8)
slti x28, x29, 1956
srli x12, x5, 26
sh x11, -36(x8)
bge x6, x29, r14
sltu x11, x11, x10
srli x13, x10, 6
lb x28, -64(x8)
r14:
slt x7, x9, x29
slt x5, x7, x0
la x16, r15
jalr x1, 0(x16)
lw x10, 8(x8)
srli x5, x6, 13
r15:
beq x5, x5, r16
lhu x5, 36(x8)
addi x10, x11, 1686
r16:
or x29, x0, x13
blt x7, x28, r17
sltiu x11, x6, 252
r17:
lw x11, 20(x8)
li x17, 3
r18:
sw x7, 16(x8)
lh x13, -4(x8)
ori x10, x29, -1294
addi x17, x17, -1
bnez x17, r18
srl x11, x6, x10
beq x0, x6, r19
lui x28, 753278
r19:
sb x28, 16(x8)
sh x7, -28(x8)
jal x1, r20
and x7, x10, x7
sb x11, -12(x8)
r20:
addi x5, x0, -23
srl x28, x28, x10
sb x12, 20(x8)
ori x12, x5, -1538
bltu x7, x29, r21
srl x13, x29, x12
r21:
add x6, x7, x28
sh x9, 16(x8)
andi x10, x12, 712
bgeu x0, x10, r22
or x10, x0, x11
sltu x9, x10, x0
xor x11, x7, x0
r22:
bge x29, x6, r23
sw x7, -28(x8)
r23:
add x12, x13, x0
lui x10, 345606
sb x10, -40(x8)
sb x13, -4(x8)
li x17, 3
r24:
sw x7, 16(x8)
xori x29, x9, -1072
xori x10, x6, 372
addi x17, x17, -1
bnez x17, r24
addi x11, x9, 1546
beq x0, x29, r25
lbu x9, 8(x8)
r25:
and x29, x10, x0
sw x13, 40(x8)
la x16, r26
jalr x0, 0(x16)
add x12, x6, x29
lh x10, -32(x8)
r26:
xori x29, x28, 875
jal x1, r27
xor x28, x10, x28
r27:
lhu x12, -36(x8)
bge x12, x9, r28
and x13, x0, x0
lbu x7, 52(x8)
lui x9, 857662
r28:
li x17, 3
r29:
sh x13, -16(x8)
andi x5, x12, 1440
sb x13, -4(x8)
lw x28, -60(x8)
addi x17, x17, -1
bnez x17, r29
lui x0, 833235
jal x0, r30
lb x28, 24(x8)
r30:
li x17, 3
r31:
sltiu x10, x7, 1737
lbu x6, 52(x8)
srai x13, x6, 27
sra x10, x5, x7
addi x17, x17, -1
bnez x17, r31
sw x0, 4(x8)
bne x28, x9, r32
sb x6, 28(x8)
r32:
slli x9, x10, 17
lw x11, 36(x8)
lh x29, -8(x8)
lui x11, 64035
la x16, r33
jalr x1, 0(x16)
sw x9, -48(x8)
lui x5, 930247
r33:
bgeu x7, x29, r34
slti x5, x7, 1562
slti x11, x6, -359
r34:
blt x6, x6, r35
addi x6, x7, -1680
r35:
lui x9, 72799
srli x29, x11, 17
lbu x12, 36(x8)
slti x5, x9, 275
srli x9, x0, 16
lui x9, 165365
lh x5, 32(x8)
la x16, r36
jalr x1, 0(x16)
addi x29, x5, 1124
r36:
lw x9, 32(x8)
add x29, x5, x28
sw x6, 44(x8)
sll x0, x0, x10
bne x0, x13, r37
sltiu x13, x0, -57
and x13, x7, x11
r37:
lw x0, -52(x8)
li x17, 3
r38:
andi x7, x28, 1426
sw x0, -48(x8)
sll x12, x5, x9
sb x0, -44(x8)
addi x17, x17, -1
bnez x17, r38
li gp, 1
ecall
fail:
ecall

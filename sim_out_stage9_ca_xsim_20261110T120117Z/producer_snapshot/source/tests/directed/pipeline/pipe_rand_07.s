# constrained-random pipeline stress seed=7 (generated)
li x8, 20480
li x5, 1390851128
li x6, 4071050724
li x7, 647892279
li x9, 1695753998
li x10, 2795742288
li x11, 207388624
li x12, 311111475
li x13, 3527346212
li x28, 2301595691
li x29, 404285457
sw x11, -32(x8)
sw x29, -28(x8)
sw x5, -24(x8)
sw x28, -20(x8)
sw x9, -16(x8)
sw x5, -12(x8)
sw x6, -8(x8)
sw x12, -4(x8)
sw x12, 0(x8)
sw x6, 4(x8)
sw x9, 8(x8)
sw x6, 12(x8)
sw x28, 16(x8)
sw x12, 20(x8)
sw x5, 24(x8)
sw x29, 28(x8)
and x0, x5, x29
beq x9, x5, r1
sw x7, -36(x8)
srai x11, x7, 6
lui x0, 393994
r1:
srai x10, x5, 13
srli x5, x29, 29
slt x6, x6, x29
andi x6, x13, 310
beq x6, x28, r2
sll x6, x13, x12
or x10, x29, x11
r2:
ori x6, x13, -1485
la x16, r3
jalr x1, 0(x16)
lb x10, 12(x8)
lh x28, 32(x8)
r3:
la x16, r4
jalr x1, 0(x16)
sh x29, -36(x8)
r4:
sll x28, x0, x9
sb x7, 48(x8)
srl x28, x28, x10
blt x0, x12, r5
sll x6, x9, x0
r5:
slti x13, x10, 261
ori x9, x29, 562
li x17, 3
r6:
sb x13, 36(x8)
addi x11, x13, 1232
slt x10, x13, x7
add x28, x6, x5
addi x17, x17, -1
bnez x17, r6
bltu x6, x11, r7
and x9, x12, x7
lui x7, 763706
xori x13, x13, 1887
r7:
xor x12, x0, x10
lb x9, -12(x8)
li x17, 3
r8:
addi x10, x28, 393
sw x28, 28(x8)
sh x28, 20(x8)
lui x29, 409250
addi x17, x17, -1
bnez x17, r8
jal x1, r9
xor x6, x0, x5
r9:
li x17, 3
r10:
andi x7, x29, 772
sltiu x7, x6, -242
slt x5, x11, x9
addi x17, x17, -1
bnez x17, r10
sb x13, 24(x8)
jal x0, r11
sw x7, 44(x8)
r11:
jal x1, r12
lhu x11, 36(x8)
r12:
beq x0, x7, r13
sh x29, 52(x8)
r13:
jal x0, r14
lbu x7, -32(x8)
or x12, x0, x7
r14:
sb x10, -12(x8)
xor x13, x10, x28
sra x7, x0, x29
jal x1, r15
srai x9, x5, 28
r15:
jal x0, r16
and x5, x0, x6
r16:
blt x0, x28, r17
srai x12, x5, 15
sub x7, x28, x13
srli x10, x11, 12
r17:
bge x28, x28, r18
srai x11, x28, 16
sw x7, 40(x8)
r18:
andi x10, x9, 1460
lw x13, -28(x8)
li x17, 3
r19:
lh x29, -32(x8)
sb x12, 60(x8)
sll x10, x0, x12
sw x12, -16(x8)
addi x17, x17, -1
bnez x17, r19
add x9, x11, x28
lh x10, 8(x8)
sub x10, x6, x10
sw x7, 44(x8)
la x16, r20
jalr x1, 0(x16)
and x7, x13, x0
addi x13, x0, -547
r20:
sub x6, x10, x6
bne x6, x10, r21
ori x6, x12, 146
r21:
beq x28, x0, r22
sw x5, -20(x8)
r22:
ori x29, x9, 327
lh x13, -60(x8)
li x17, 3
r23:
or x7, x9, x28
addi x28, x0, 1492
addi x17, x17, -1
bnez x17, r23
bltu x12, x28, r24
lh x10, -16(x8)
lbu x0, 36(x8)
r24:
li x17, 3
r25:
lb x5, 0(x8)
addi x9, x0, 1072
addi x17, x17, -1
bnez x17, r25
la x16, r26
jalr x1, 0(x16)
lhu x7, -20(x8)
r26:
sltiu x12, x11, 602
sh x11, -20(x8)
sltiu x5, x28, -402
lh x11, -44(x8)
lui x11, 47173
lui x11, 325587
bgeu x29, x12, r27
lbu x6, 8(x8)
lb x29, 44(x8)
r27:
bltu x7, x28, r28
srai x6, x29, 14
sll x7, x0, x11
sw x28, -52(x8)
r28:
bgeu x28, x0, r29
xori x5, x6, -1295
r29:
beq x0, x0, r30
sltu x10, x9, x0
lw x10, 52(x8)
r30:
andi x5, x10, -1666
bgeu x9, x6, r31
sltu x12, x29, x29
add x5, x13, x10
sh x0, 60(x8)
r31:
srli x29, x13, 7
li x17, 3
r32:
sra x11, x5, x10
xori x7, x10, 1121
sub x9, x29, x6
sltu x9, x11, x7
addi x17, x17, -1
bnez x17, r32
bgeu x28, x10, r33
lhu x10, 60(x8)
r33:
sra x6, x12, x10
bge x11, x12, r34
add x6, x11, x11
lbu x13, -64(x8)
r34:
li x17, 3
r35:
srl x10, x12, x29
sltu x13, x5, x10
sll x28, x9, x10
addi x17, x17, -1
bnez x17, r35
xori x9, x5, 1229
li x17, 3
r36:
slli x11, x0, 26
andi x28, x10, 1929
sll x11, x7, x13
sltiu x28, x10, 83
addi x17, x17, -1
bnez x17, r36
or x5, x0, x12
lbu x10, 60(x8)
bge x11, x13, r37
slt x7, x6, x7
sltiu x11, x9, 969
r37:
srai x6, x12, 24
srli x10, x11, 3
slli x9, x0, 13
sw x0, 48(x8)
slti x6, x5, 1435
bge x29, x13, r38
sra x9, x13, x9
r38:
jal x0, r39
sra x12, x6, x28
r39:
jal x0, r40
sltu x7, x7, x0
r40:
lui x13, 208550
slli x13, x12, 16
lui x5, 632335
li x17, 3
r41:
sw x28, -4(x8)
srli x6, x0, 19
sra x7, x0, x0
addi x17, x17, -1
bnez x17, r41
xor x13, x9, x13
sltiu x12, x0, 1198
lb x7, -12(x8)
slt x7, x13, x9
sw x29, -20(x8)
li x17, 3
r42:
ori x9, x7, 1175
and x6, x7, x12
sll x9, x12, x13
addi x17, x17, -1
bnez x17, r42
li x17, 3
r43:
lbu x11, 20(x8)
sra x9, x5, x10
lw x10, 28(x8)
addi x17, x17, -1
bnez x17, r43
li x17, 3
r44:
sub x5, x10, x6
ori x13, x9, 1066
xori x29, x6, -1645
addi x17, x17, -1
bnez x17, r44
bne x11, x28, r45
sra x9, x5, x0
xori x0, x5, 1028
r45:
sltu x9, x9, x0
lui x9, 571085
sw x0, 16(x8)
li x17, 3
r46:
sub x28, x5, x9
srl x29, x10, x12
lhu x28, -20(x8)
addi x17, x17, -1
bnez x17, r46
li gp, 1
ecall
fail:
ecall

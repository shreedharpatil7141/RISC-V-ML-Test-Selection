# constrained-random pipeline stress seed=2 (generated)
li x8, 20480
li x5, 4106135923
li x6, 3707026329
li x7, 4070888059
li x9, 3646664648
li x10, 242886303
li x11, 393353683
li x12, 364522461
li x13, 1550730039
li x28, 3588440356
li x29, 726208580
sw x10, -32(x8)
sw x10, -28(x8)
sw x29, -24(x8)
sw x9, -20(x8)
sw x29, -16(x8)
sw x5, -12(x8)
sw x29, -8(x8)
sw x7, -4(x8)
sw x12, 0(x8)
sw x12, 4(x8)
sw x28, 8(x8)
sw x11, 12(x8)
sw x28, 16(x8)
sw x13, 20(x8)
sw x28, 24(x8)
sw x10, 28(x8)
li x17, 3
r1:
xori x5, x12, -701
slli x11, x5, 11
addi x17, x17, -1
bnez x17, r1
xor x7, x28, x0
bge x12, x0, r2
sw x11, 48(x8)
sra x11, x0, x28
sra x13, x28, x28
r2:
la x16, r3
jalr x1, 0(x16)
sw x29, 52(x8)
sltiu x10, x0, -688
r3:
la x16, r4
jalr x1, 0(x16)
ori x7, x28, 1283
xori x9, x28, 955
r4:
li x17, 3
r5:
sb x9, -40(x8)
sltu x9, x29, x9
lw x12, -32(x8)
sh x5, 44(x8)
addi x17, x17, -1
bnez x17, r5
li x17, 3
r6:
sll x9, x9, x0
sub x13, x5, x5
addi x17, x17, -1
bnez x17, r6
beq x11, x10, r7
lw x5, -20(x8)
r7:
add x13, x9, x7
li x17, 3
r8:
andi x29, x0, -1122
add x6, x10, x13
addi x17, x17, -1
bnez x17, r8
bltu x0, x5, r9
lw x29, -28(x8)
addi x10, x0, 543
r9:
la x16, r10
jalr x0, 0(x16)
lw x28, 36(x8)
slti x5, x11, 74
r10:
sh x0, -52(x8)
sub x5, x13, x0
sh x9, 48(x8)
and x10, x29, x0
lw x13, -64(x8)
addi x5, x28, -1329
slt x6, x6, x9
lh x29, 32(x8)
sw x12, -60(x8)
beq x12, x28, r11
sra x12, x11, x5
srai x13, x11, 18
lh x9, -60(x8)
r11:
la x16, r12
jalr x1, 0(x16)
add x7, x13, x5
r12:
ori x9, x29, -1444
sub x29, x9, x13
srai x11, x13, 8
jal x1, r13
sub x13, x29, x11
r13:
bne x0, x6, r14
lui x5, 90555
r14:
bge x10, x11, r15
sltu x9, x13, x28
sw x0, 8(x8)
r15:
sltu x28, x28, x12
bgeu x6, x29, r16
lb x12, 24(x8)
sll x10, x12, x6
lbu x7, 8(x8)
r16:
lhu x6, -20(x8)
srl x10, x6, x11
lbu x12, -24(x8)
lw x11, 24(x8)
jal x0, r17
ori x6, x12, -570
xori x9, x10, 1269
r17:
lw x12, 56(x8)
srai x11, x9, 12
lb x0, 16(x8)
lw x29, -20(x8)
jal x0, r18
sw x9, -40(x8)
slti x11, x10, -480
r18:
lui x5, 910998
srli x6, x0, 13
li x17, 3
r19:
ori x6, x0, -1512
lw x6, 20(x8)
addi x17, x17, -1
bnez x17, r19
sb x6, 24(x8)
lh x11, -32(x8)
andi x29, x10, -772
srli x5, x5, 24
bne x0, x10, r20
lw x5, 12(x8)
sltu x5, x11, x0
r20:
li x17, 3
r21:
lw x11, -44(x8)
srli x9, x29, 9
lb x0, 12(x8)
addi x17, x17, -1
bnez x17, r21
sh x28, 4(x8)
xor x10, x9, x11
slti x9, x13, 1572
la x16, r22
jalr x1, 0(x16)
sh x10, 16(x8)
r22:
sh x0, 28(x8)
slt x28, x10, x28
bge x0, x11, r23
sw x0, 36(x8)
lw x0, 8(x8)
r23:
lui x10, 770565
sltiu x12, x13, 1856
sw x7, -60(x8)
srl x10, x5, x28
lhu x28, 8(x8)
sw x9, 60(x8)
xor x9, x10, x7
slt x6, x9, x0
lui x6, 781795
bltu x5, x7, r24
sw x10, -32(x8)
r24:
srli x13, x0, 25
sra x5, x29, x11
lui x11, 1039579
li x17, 3
r25:
xori x12, x28, 1660
sra x12, x29, x7
sll x7, x6, x12
sltiu x5, x6, 824
addi x17, x17, -1
bnez x17, r25
sub x13, x11, x0
sh x6, 56(x8)
or x7, x5, x5
sw x0, -4(x8)
ori x28, x6, -28
and x9, x9, x0
lui x11, 341828
lw x29, -12(x8)
srl x6, x7, x12
addi x29, x28, -1230
sltu x6, x9, x12
bgeu x28, x0, r26
slt x11, x9, x9
r26:
add x28, x0, x10
bge x28, x5, r27
lw x10, -28(x8)
lui x7, 410799
sh x6, 52(x8)
r27:
bne x7, x11, r28
lw x9, -48(x8)
andi x12, x0, -1772
andi x13, x0, 182
r28:
li x17, 3
r29:
sltu x6, x28, x0
andi x9, x9, 1472
addi x17, x17, -1
bnez x17, r29
jal x0, r30
sw x13, 0(x8)
lui x13, 998465
r30:
lh x12, 12(x8)
xori x0, x9, -999
blt x9, x28, r31
slt x6, x11, x5
andi x12, x0, 760
r31:
jal x0, r32
sltiu x6, x29, -968
and x5, x12, x0
r32:
lui x13, 172514
lbu x11, 12(x8)
la x16, r33
jalr x0, 0(x16)
lui x6, 821878
r33:
or x9, x5, x10
bne x29, x0, r34
lhu x13, 36(x8)
sltiu x10, x9, -77
r34:
srai x11, x28, 0
lbu x11, 4(x8)
srli x9, x29, 4
bgeu x0, x9, r35
add x5, x7, x0
slt x5, x28, x5
r35:
bgeu x10, x6, r36
srai x11, x0, 8
addi x28, x10, 149
sltiu x11, x11, -1251
r36:
li gp, 1
ecall
fail:
ecall

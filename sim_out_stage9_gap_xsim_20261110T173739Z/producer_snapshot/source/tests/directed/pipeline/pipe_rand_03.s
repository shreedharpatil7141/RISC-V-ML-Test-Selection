# constrained-random pipeline stress seed=3 (generated)
li x8, 20480
li x5, 1022050301
li x6, 2545373330
li x7, 2337446730
li x9, 560161641
li x10, 1588945316
li x11, 3933953013
li x12, 2593816829
li x13, 2036044446
li x28, 2687448230
li x29, 2494740733
sw x6, -32(x8)
sw x29, -28(x8)
sw x5, -24(x8)
sw x13, -20(x8)
sw x10, -16(x8)
sw x28, -12(x8)
sw x9, -8(x8)
sw x9, -4(x8)
sw x13, 0(x8)
sw x28, 4(x8)
sw x28, 8(x8)
sw x13, 12(x8)
sw x12, 16(x8)
sw x7, 20(x8)
sw x9, 24(x8)
sw x7, 28(x8)
la x16, r1
jalr x1, 0(x16)
lbu x10, -56(x8)
r1:
sra x13, x29, x0
li x17, 3
r2:
lhu x13, 48(x8)
sw x6, -56(x8)
sltu x9, x0, x12
addi x17, x17, -1
bnez x17, r2
jal x1, r3
srai x10, x11, 26
lui x6, 60105
r3:
la x16, r4
jalr x0, 0(x16)
sb x0, -12(x8)
lui x12, 560117
r4:
sra x0, x6, x11
jal x1, r5
srl x13, x6, x5
r5:
beq x12, x0, r6
ori x13, x9, -1753
addi x10, x29, -1791
sw x29, 0(x8)
r6:
xor x6, x11, x7
li x17, 3
r7:
xori x9, x0, -1208
lui x7, 568958
sltiu x11, x12, 67
addi x17, x17, -1
bnez x17, r7
srli x5, x29, 20
lui x0, 279484
lui x29, 740118
blt x29, x0, r8
lw x6, -52(x8)
sw x10, 52(x8)
r8:
lui x6, 763269
lh x28, 12(x8)
jal x0, r9
sw x28, -8(x8)
r9:
blt x9, x11, r10
lb x12, 16(x8)
r10:
li x17, 3
r11:
lw x28, -24(x8)
and x9, x13, x10
add x13, x28, x9
slti x12, x10, 738
addi x17, x17, -1
bnez x17, r11
jal x0, r12
lui x12, 612248
srli x13, x11, 26
r12:
srli x7, x7, 12
sw x28, -8(x8)
sltiu x9, x28, 746
la x16, r13
jalr x0, 0(x16)
add x11, x5, x0
srli x7, x29, 3
r13:
lw x5, 12(x8)
srl x10, x5, x29
sra x10, x5, x11
sll x13, x9, x10
li x17, 3
r14:
lhu x5, 36(x8)
slt x13, x10, x29
addi x17, x17, -1
bnez x17, r14
sltiu x5, x5, -1599
jal x0, r15
add x5, x0, x6
r15:
sltiu x5, x6, 829
sltiu x29, x10, -483
li x17, 3
r16:
add x11, x0, x0
ori x11, x7, -1697
andi x28, x28, 1067
addi x17, x17, -1
bnez x17, r16
beq x29, x12, r17
andi x6, x11, 1396
r17:
li x17, 3
r18:
slti x11, x28, 164
lw x10, 44(x8)
add x28, x11, x11
addi x17, x17, -1
bnez x17, r18
li x17, 3
r19:
lb x12, 52(x8)
lw x9, 32(x8)
lw x5, -40(x8)
lhu x5, -28(x8)
addi x17, x17, -1
bnez x17, r19
addi x9, x29, -1235
bge x7, x5, r20
sb x6, 56(x8)
lw x28, 12(x8)
r20:
jal x0, r21
or x12, x5, x28
r21:
slli x10, x7, 15
lh x11, 28(x8)
blt x28, x12, r22
xori x11, x0, -733
r22:
srai x13, x28, 30
slti x29, x6, 2031
bgeu x28, x13, r23
lbu x6, 4(x8)
lw x29, 16(x8)
sw x0, 40(x8)
r23:
bltu x29, x10, r24
xori x13, x12, -405
r24:
xori x5, x7, 1379
li x17, 3
r25:
lhu x9, -60(x8)
xori x10, x0, -1673
slti x10, x0, -1481
addi x17, x17, -1
bnez x17, r25
li x17, 3
r26:
sltu x7, x7, x7
lui x7, 534790
xor x7, x7, x12
addi x17, x17, -1
bnez x17, r26
lb x13, 0(x8)
la x16, r27
jalr x1, 0(x16)
andi x13, x0, 709
r27:
xori x13, x13, -1410
lui x6, 819818
addi x13, x0, 1495
sb x28, 28(x8)
blt x13, x10, r28
lb x12, 20(x8)
lw x10, -36(x8)
lh x7, -52(x8)
r28:
bgeu x0, x29, r29
sll x0, x7, x11
sb x6, -28(x8)
sw x28, 12(x8)
r29:
bge x13, x10, r30
lw x12, -20(x8)
r30:
jal x1, r31
srl x13, x5, x7
sltu x7, x9, x0
r31:
jal x1, r32
sb x11, 60(x8)
sh x10, -40(x8)
r32:
bltu x0, x6, r33
lhu x12, 36(x8)
r33:
jal x0, r34
sh x29, -20(x8)
r34:
add x28, x13, x12
li x17, 3
r35:
sltiu x13, x0, 2030
sw x5, -16(x8)
lb x5, -8(x8)
addi x17, x17, -1
bnez x17, r35
slli x29, x9, 13
slli x28, x29, 18
li x17, 3
r36:
and x11, x5, x5
ori x10, x6, 2036
addi x17, x17, -1
bnez x17, r36
sw x11, -32(x8)
lw x7, -44(x8)
blt x9, x6, r37
xori x10, x11, -1155
r37:
jal x1, r38
sw x13, 56(x8)
r38:
bltu x12, x9, r39
xori x6, x13, 1240
addi x29, x0, 54
xori x9, x28, 913
r39:
bne x5, x9, r40
lw x29, 52(x8)
slli x5, x5, 10
r40:
bltu x7, x0, r41
sll x28, x13, x13
r41:
sw x11, 40(x8)
lhu x11, -56(x8)
slt x10, x6, x12
sub x29, x11, x6
bgeu x10, x10, r42
lhu x29, -4(x8)
srli x6, x0, 22
r42:
sub x13, x29, x29
add x11, x7, x28
xor x7, x9, x13
andi x7, x5, 1083
lui x11, 184086
li x17, 3
r43:
sw x28, 20(x8)
slli x11, x0, 24
addi x17, x17, -1
bnez x17, r43
li gp, 1
ecall
fail:
ecall

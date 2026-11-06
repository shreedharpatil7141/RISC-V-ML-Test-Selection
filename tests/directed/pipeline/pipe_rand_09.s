# constrained-random pipeline stress seed=9 (generated)
li x8, 20480
li x5, 1988601454
li x6, 2633739374
li x7, 1603362544
li x9, 1147333628
li x10, 595022250
li x11, 799486471
li x12, 3721854805
li x13, 2906162014
li x28, 27638352
li x29, 1453097014
sw x28, -32(x8)
sw x13, -28(x8)
sw x29, -24(x8)
sw x6, -20(x8)
sw x11, -16(x8)
sw x28, -12(x8)
sw x29, -8(x8)
sw x5, -4(x8)
sw x12, 0(x8)
sw x7, 4(x8)
sw x13, 8(x8)
sw x12, 12(x8)
sw x7, 16(x8)
sw x7, 20(x8)
sw x9, 24(x8)
sw x5, 28(x8)
slli x13, x0, 24
jal x0, r1
srl x10, x6, x10
sw x11, -56(x8)
r1:
sb x12, 60(x8)
and x13, x5, x6
jal x0, r2
slti x11, x28, -1905
r2:
slli x10, x12, 4
lui x11, 304836
lui x7, 113609
lw x29, 4(x8)
bltu x5, x6, r3
slti x11, x29, -1696
lw x9, -44(x8)
sw x13, -12(x8)
r3:
sb x12, 20(x8)
sra x10, x10, x11
jal x1, r4
add x9, x12, x28
lh x6, -4(x8)
r4:
beq x12, x0, r5
or x11, x11, x28
r5:
lw x5, 0(x8)
sw x7, -36(x8)
beq x5, x5, r6
sltu x10, x29, x5
sw x7, 56(x8)
r6:
bne x6, x0, r7
sub x13, x12, x13
srl x11, x29, x7
lw x13, 60(x8)
r7:
sh x7, -44(x8)
lbu x5, -20(x8)
lui x10, 814290
srli x13, x28, 4
li x17, 3
r8:
lui x13, 913832
srai x9, x28, 4
addi x17, x17, -1
bnez x17, r8
la x16, r9
jalr x1, 0(x16)
lb x28, -40(x8)
r9:
bge x5, x13, r10
lb x28, 28(x8)
slt x29, x11, x0
slli x6, x5, 5
r10:
bgeu x12, x12, r11
add x7, x29, x7
xor x6, x29, x13
slli x5, x0, 4
r11:
lhu x5, 48(x8)
bge x13, x7, r12
sw x7, -16(x8)
r12:
li x17, 3
r13:
sub x13, x0, x6
xori x6, x0, -405
addi x17, x17, -1
bnez x17, r13
lui x11, 11474
slli x7, x13, 16
li x17, 3
r14:
sw x5, 0(x8)
ori x5, x9, -1568
addi x17, x17, -1
bnez x17, r14
bne x10, x5, r15
sb x10, -40(x8)
r15:
ori x12, x11, 1980
bge x12, x9, r16
sra x29, x29, x29
r16:
xori x6, x5, 614
slti x6, x9, 938
bne x0, x6, r17
sw x9, 20(x8)
srl x11, x13, x9
r17:
la x16, r18
jalr x1, 0(x16)
sltiu x5, x28, -368
r18:
add x5, x6, x7
lw x7, 36(x8)
bge x12, x29, r19
sw x11, 4(x8)
and x10, x7, x29
lw x6, -24(x8)
r19:
lh x6, 56(x8)
lw x13, -44(x8)
sra x28, x0, x9
and x7, x5, x28
slti x13, x28, -1257
slti x10, x12, -274
lhu x12, -64(x8)
la x16, r20
jalr x0, 0(x16)
sltiu x9, x12, 1749
ori x7, x6, -688
r20:
li x17, 3
r21:
sh x13, -20(x8)
lw x5, 20(x8)
addi x17, x17, -1
bnez x17, r21
bne x5, x5, r22
sh x0, 20(x8)
xor x28, x10, x12
slt x11, x13, x13
r22:
li x17, 3
r23:
ori x29, x0, -413
lui x9, 799918
addi x17, x17, -1
bnez x17, r23
la x16, r24
jalr x0, 0(x16)
sll x11, x10, x12
andi x6, x0, -1274
r24:
sltiu x12, x11, 793
sw x10, -40(x8)
sub x29, x10, x10
srl x0, x10, x11
li x17, 3
r25:
ori x5, x0, -1809
sub x9, x5, x9
xor x28, x11, x28
addi x17, x17, -1
bnez x17, r25
jal x0, r26
lbu x13, -52(x8)
r26:
srl x12, x11, x0
bgeu x11, x0, r27
slli x12, x7, 20
sltu x28, x12, x28
addi x12, x11, -223
r27:
addi x9, x12, -550
srl x5, x13, x5
slt x12, x29, x13
add x28, x28, x6
beq x9, x13, r28
sltu x7, x0, x7
sw x7, 40(x8)
sw x13, 8(x8)
r28:
bge x28, x0, r29
sw x5, 56(x8)
lhu x11, 20(x8)
r29:
ori x13, x29, -822
li x17, 3
r30:
lhu x10, -36(x8)
srai x5, x10, 28
lw x11, 0(x8)
addi x17, x17, -1
bnez x17, r30
jal x0, r31
or x6, x0, x13
sw x7, -24(x8)
r31:
blt x0, x0, r32
sltiu x11, x0, 274
sw x10, -52(x8)
r32:
bge x6, x10, r33
srl x28, x13, x28
sll x9, x0, x6
r33:
beq x6, x0, r34
add x28, x13, x0
sltu x11, x6, x6
r34:
jal x0, r35
lui x12, 467543
sra x7, x29, x28
r35:
sw x9, 36(x8)
blt x10, x7, r36
lw x6, 32(x8)
sub x6, x29, x6
lhu x10, 20(x8)
r36:
sltiu x11, x28, -1360
sra x12, x11, x0
andi x5, x13, 54
blt x7, x11, r37
sltu x9, x29, x7
r37:
sh x29, -28(x8)
jal x0, r38
lui x0, 844110
r38:
lw x13, 56(x8)
or x12, x7, x7
sub x9, x29, x29
bgeu x6, x5, r39
lw x11, -24(x8)
r39:
sh x7, 20(x8)
bgeu x9, x6, r40
add x11, x0, x13
r40:
sh x10, 12(x8)
andi x9, x28, -371
add x5, x13, x0
srai x13, x11, 6
jal x1, r41
xor x7, x0, x6
sb x10, -4(x8)
r41:
slli x13, x0, 22
bne x9, x7, r42
lw x29, 52(x8)
xori x28, x29, 2001
sltu x5, x13, x5
r42:
sll x28, x13, x6
lhu x6, -40(x8)
bne x6, x11, r43
sw x6, 4(x8)
r43:
slt x11, x10, x0
sw x7, -16(x8)
xor x9, x0, x29
li x17, 3
r44:
sw x0, -60(x8)
lw x6, 48(x8)
sltu x9, x13, x9
addi x17, x17, -1
bnez x17, r44
sb x9, 44(x8)
sub x11, x12, x29
slli x7, x5, 30
la x16, r45
jalr x1, 0(x16)
srl x9, x12, x11
r45:
srai x6, x0, 26
sw x9, -4(x8)
andi x7, x12, -1533
sltiu x7, x12, -39
li x17, 3
r46:
sw x6, 44(x8)
lui x29, 972213
srli x7, x9, 20
addi x17, x17, -1
bnez x17, r46
slti x6, x5, -1426
jal x1, r47
sh x29, -32(x8)
sw x5, -24(x8)
r47:
slli x5, x9, 14
jal x1, r48
sb x12, -52(x8)
r48:
blt x9, x28, r49
xor x9, x10, x5
sub x29, x0, x0
r49:
beq x6, x7, r50
add x7, x13, x0
lhu x9, -40(x8)
r50:
la x16, r51
jalr x1, 0(x16)
xor x12, x0, x5
r51:
lw x9, -64(x8)
beq x0, x11, r52
addi x13, x0, -721
r52:
li x17, 3
r53:
slt x28, x29, x29
add x10, x9, x5
sra x7, x6, x28
or x9, x13, x11
addi x17, x17, -1
bnez x17, r53
li gp, 1
ecall
fail:
ecall

# constrained-random pipeline stress seed=22 (generated)
li x8, 20480
li x5, 4115477951
li x6, 3897096200
li x7, 602878526
li x9, 1042032339
li x10, 101430565
li x11, 2633188042
li x12, 4289086009
li x13, 1920423526
li x28, 791363372
li x29, 3014869100
sw x6, -32(x8)
sw x11, -28(x8)
sw x6, -24(x8)
sw x9, -20(x8)
sw x10, -16(x8)
sw x5, -12(x8)
sw x11, -8(x8)
sw x29, -4(x8)
sw x7, 0(x8)
sw x28, 4(x8)
sw x12, 8(x8)
sw x5, 12(x8)
sw x29, 16(x8)
sw x5, 20(x8)
sw x29, 24(x8)
sw x10, 28(x8)
and x13, x28, x0
jal x0, r1
lui x12, 386822
sh x10, 4(x8)
r1:
bne x12, x5, r2
srli x7, x10, 18
srli x12, x0, 11
r2:
addi x13, x10, 1503
jal x1, r3
xor x28, x6, x12
r3:
jal x0, r4
slli x11, x6, 29
r4:
li x17, 3
r5:
xor x10, x7, x11
sh x13, -56(x8)
addi x17, x17, -1
bnez x17, r5
sub x7, x5, x9
lhu x13, -56(x8)
la x16, r6
jalr x1, 0(x16)
lui x5, 998605
r6:
bgeu x0, x11, r7
lh x28, -36(x8)
r7:
slli x0, x11, 6
lw x13, 4(x8)
xor x7, x0, x6
li x17, 3
r8:
sll x10, x5, x10
lhu x13, -12(x8)
andi x13, x28, -571
and x10, x5, x9
addi x17, x17, -1
bnez x17, r8
addi x10, x0, 1387
sub x10, x10, x6
li x17, 3
r9:
add x5, x5, x13
add x13, x13, x0
slt x5, x0, x13
sw x28, 44(x8)
addi x17, x17, -1
bnez x17, r9
andi x5, x12, -1170
lw x29, 28(x8)
sh x10, 4(x8)
xori x7, x0, 2046
jal x0, r10
xori x10, x0, -451
lb x11, 32(x8)
r10:
sll x9, x9, x28
sw x5, -36(x8)
li x17, 3
r11:
sub x0, x6, x29
sltu x6, x28, x10
sw x11, -52(x8)
sw x0, 8(x8)
addi x17, x17, -1
bnez x17, r11
xor x13, x10, x5
li x17, 3
r12:
xor x28, x7, x7
xori x12, x11, -903
addi x17, x17, -1
bnez x17, r12
jal x1, r13
srli x29, x5, 29
r13:
li x17, 3
r14:
slli x11, x9, 19
slli x28, x10, 15
lw x13, 56(x8)
ori x5, x12, -1482
addi x17, x17, -1
bnez x17, r14
bne x12, x7, r15
lui x29, 909984
lui x9, 827579
lh x28, -12(x8)
r15:
sub x11, x7, x13
jal x0, r16
srli x0, x0, 8
r16:
sw x28, -4(x8)
bne x11, x0, r17
xori x6, x0, 1648
srli x13, x9, 15
r17:
srai x28, x5, 15
bne x11, x13, r18
sh x11, 40(x8)
addi x28, x28, 475
r18:
beq x7, x0, r19
lhu x10, -32(x8)
sltu x7, x5, x5
sll x6, x13, x7
r19:
sltu x12, x11, x6
or x11, x0, x10
bltu x13, x11, r20
lbu x5, -20(x8)
lb x0, -36(x8)
ori x5, x28, 1333
r20:
blt x12, x0, r21
sltu x12, x5, x29
r21:
srai x29, x11, 25
sb x7, 48(x8)
li x17, 3
r22:
xori x10, x6, 905
lui x5, 815534
addi x17, x17, -1
bnez x17, r22
sll x11, x10, x0
sltiu x7, x12, -559
sub x6, x9, x10
lw x6, 4(x8)
lh x13, 12(x8)
slti x10, x9, 1409
xor x13, x0, x5
jal x1, r23
sll x9, x0, x10
sra x6, x6, x28
r23:
xor x10, x12, x7
lw x11, 56(x8)
beq x11, x7, r24
slt x28, x0, x0
ori x13, x6, 449
r24:
bltu x9, x9, r25
xor x29, x10, x7
sb x29, 60(x8)
lb x28, -36(x8)
r25:
lw x5, -60(x8)
bltu x13, x13, r26
srai x28, x9, 11
sltiu x7, x7, -1347
r26:
srai x11, x28, 23
xor x28, x0, x0
add x6, x10, x28
or x12, x28, x6
sw x12, -12(x8)
lh x12, -52(x8)
bge x11, x10, r27
lh x13, 28(x8)
sltu x10, x0, x11
r27:
li x17, 3
r28:
andi x6, x6, 1989
sll x11, x9, x0
sltiu x11, x13, 1935
addi x17, x17, -1
bnez x17, r28
sb x11, 56(x8)
sll x13, x28, x29
bltu x10, x13, r29
sw x12, -4(x8)
lhu x9, -36(x8)
lw x29, -40(x8)
r29:
add x7, x13, x0
li x17, 3
r30:
srl x11, x11, x13
sll x10, x9, x11
sltu x9, x5, x11
addi x17, x17, -1
bnez x17, r30
and x12, x0, x28
bltu x7, x28, r31
lui x13, 651508
r31:
addi x7, x0, -1672
la x16, r32
jalr x0, 0(x16)
slli x10, x29, 10
r32:
xor x28, x5, x28
sltiu x28, x29, 1220
bne x10, x9, r33
sll x10, x0, x29
r33:
bne x12, x11, r34
lui x29, 194756
lui x28, 935186
sb x7, -60(x8)
r34:
srai x28, x28, 14
lh x11, 4(x8)
sw x13, 12(x8)
beq x11, x0, r35
lw x12, -56(x8)
r35:
ori x12, x28, 2036
beq x0, x11, r36
lui x29, 383771
lui x28, 412903
lbu x28, 56(x8)
r36:
li x17, 3
r37:
sw x29, 44(x8)
sb x9, 60(x8)
sw x28, 48(x8)
addi x17, x17, -1
bnez x17, r37
andi x9, x9, 1324
andi x13, x0, 1513
sb x29, 0(x8)
lbu x12, -44(x8)
bne x11, x28, r38
lw x29, 44(x8)
lw x9, 20(x8)
r38:
slt x7, x13, x9
li x17, 3
r39:
sll x0, x5, x9
ori x11, x6, -1310
xori x6, x11, 1876
addi x17, x17, -1
bnez x17, r39
xori x7, x28, -745
la x16, r40
jalr x0, 0(x16)
lw x7, 16(x8)
lui x28, 931093
r40:
li x17, 3
r41:
sltu x10, x13, x6
sra x9, x28, x9
addi x17, x17, -1
bnez x17, r41
sh x29, -24(x8)
li x17, 3
r42:
sw x5, 28(x8)
lb x0, -4(x8)
lbu x29, 36(x8)
addi x17, x17, -1
bnez x17, r42
la x16, r43
jalr x0, 0(x16)
lw x28, -64(x8)
lb x9, -4(x8)
r43:
andi x10, x0, -585
bne x0, x11, r44
sb x28, -64(x8)
sra x6, x10, x7
r44:
xor x9, x5, x29
blt x13, x0, r45
sb x5, -16(x8)
and x6, x11, x11
r45:
andi x9, x7, -982
jal x1, r46
sh x13, 56(x8)
r46:
bltu x13, x28, r47
slti x9, x7, 1100
sw x10, -8(x8)
r47:
or x11, x10, x29
srl x7, x6, x7
jal x1, r48
lh x28, 48(x8)
r48:
add x6, x11, x12
blt x7, x9, r49
lw x5, -36(x8)
r49:
la x16, r50
jalr x1, 0(x16)
sltiu x29, x7, -1397
sll x6, x11, x28
r50:
li x17, 3
r51:
lb x5, -48(x8)
sra x7, x29, x13
addi x17, x17, -1
bnez x17, r51
srli x13, x9, 12
jal x1, r52
andi x9, x6, -785
r52:
add x28, x9, x0
li x17, 3
r53:
sh x13, -28(x8)
xori x10, x11, -1773
addi x17, x17, -1
bnez x17, r53
jal x0, r54
srli x28, x5, 7
r54:
blt x12, x28, r55
sra x10, x5, x5
r55:
or x29, x0, x6
jal x0, r56
lhu x7, 52(x8)
r56:
li x17, 3
r57:
addi x6, x11, 936
lw x13, -52(x8)
addi x17, x17, -1
bnez x17, r57
andi x29, x5, 1037
li x17, 3
r58:
lw x28, 44(x8)
or x10, x6, x11
addi x17, x17, -1
bnez x17, r58
andi x11, x0, 602
li x17, 3
r59:
lhu x9, 36(x8)
lh x28, -52(x8)
xori x7, x28, -165
ori x6, x10, 1535
addi x17, x17, -1
bnez x17, r59
bne x0, x28, r60
lui x13, 758167
r60:
sra x12, x9, x13
li x17, 3
r61:
xor x13, x13, x7
lh x5, 4(x8)
addi x17, x17, -1
bnez x17, r61
xor x13, x6, x0
ori x5, x9, 1493
jal x1, r62
sll x5, x13, x5
r62:
lw x7, 44(x8)
bgeu x5, x28, r63
lhu x12, -36(x8)
r63:
sll x12, x0, x12
li x17, 3
r64:
slt x6, x29, x13
lui x13, 800101
addi x17, x17, -1
bnez x17, r64
lb x7, 44(x8)
lui x7, 952592
lui x5, 822229
srl x7, x10, x6
srli x10, x10, 19
bge x0, x10, r65
sw x13, -44(x8)
srai x0, x0, 11
lh x0, -56(x8)
r65:
sb x0, -16(x8)
lw x13, -36(x8)
xori x13, x12, 374
beq x5, x11, r66
sltiu x9, x0, -460
r66:
la x16, r67
jalr x1, 0(x16)
lw x28, -40(x8)
ori x29, x0, 696
r67:
li x17, 3
r68:
sltu x10, x12, x5
lui x12, 751931
addi x17, x17, -1
bnez x17, r68
la x16, r69
jalr x1, 0(x16)
srli x12, x13, 0
r69:
slt x29, x0, x0
sltiu x7, x5, 1029
xori x28, x11, -1981
bne x9, x10, r70
and x12, x29, x0
lw x10, -60(x8)
r70:
li gp, 1
ecall
fail:
ecall

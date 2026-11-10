# constrained-random pipeline stress seed=20 (generated)
li x8, 20480
li x5, 3889692776
li x6, 3104401924
li x7, 2947439163
li x9, 3378761696
li x10, 3292132170
li x11, 3779415104
li x12, 3885297172
li x13, 649421745
li x28, 1115950379
li x29, 2894850007
sw x6, -32(x8)
sw x11, -28(x8)
sw x29, -24(x8)
sw x7, -20(x8)
sw x5, -16(x8)
sw x12, -12(x8)
sw x12, -8(x8)
sw x6, -4(x8)
sw x6, 0(x8)
sw x7, 4(x8)
sw x11, 8(x8)
sw x13, 12(x8)
sw x29, 16(x8)
sw x13, 20(x8)
sw x12, 24(x8)
sw x9, 28(x8)
lui x6, 689420
lui x6, 849206
slli x7, x6, 5
lh x28, 0(x8)
sltu x6, x0, x9
la x16, r1
jalr x0, 0(x16)
sltu x29, x10, x7
r1:
blt x29, x0, r2
sw x28, 44(x8)
sub x11, x0, x7
r2:
li x17, 3
r3:
addi x10, x29, -1624
slli x13, x7, 5
add x28, x0, x11
lhu x11, -52(x8)
addi x17, x17, -1
bnez x17, r3
la x16, r4
jalr x0, 0(x16)
sw x5, -48(x8)
r4:
beq x6, x11, r5
lw x29, -56(x8)
lbu x7, -64(x8)
r5:
sh x10, -32(x8)
slt x12, x9, x9
la x16, r6
jalr x0, 0(x16)
sll x10, x0, x6
slti x5, x9, 502
r6:
sh x11, 12(x8)
lh x5, -52(x8)
la x16, r7
jalr x1, 0(x16)
addi x29, x6, 1796
or x5, x6, x28
r7:
blt x0, x5, r8
sub x28, x5, x5
r8:
and x11, x6, x29
la x16, r9
jalr x1, 0(x16)
and x28, x12, x28
addi x12, x13, -1297
r9:
bge x11, x9, r10
srl x6, x9, x29
r10:
xor x11, x5, x6
srai x28, x5, 8
blt x28, x7, r11
sra x9, x9, x12
r11:
li x17, 3
r12:
srai x28, x29, 18
lui x11, 1034644
sra x28, x0, x0
sh x11, 16(x8)
addi x17, x17, -1
bnez x17, r12
li x17, 3
r13:
sb x0, 4(x8)
lbu x9, 28(x8)
ori x10, x0, 467
lbu x0, -32(x8)
addi x17, x17, -1
bnez x17, r13
sb x7, 20(x8)
sb x7, 0(x8)
sra x10, x5, x28
andi x7, x0, -1268
bne x0, x10, r14
srli x5, x13, 30
lbu x6, -16(x8)
sra x7, x12, x13
r14:
lw x29, -36(x8)
jal x0, r15
sw x12, 56(x8)
slt x9, x0, x7
r15:
blt x10, x7, r16
slti x10, x10, -994
r16:
or x7, x5, x6
la x16, r17
jalr x1, 0(x16)
srai x28, x13, 28
r17:
lw x6, -20(x8)
jal x0, r18
lw x12, 12(x8)
slt x13, x6, x6
r18:
bltu x29, x13, r19
ori x11, x0, -677
slli x28, x28, 1
r19:
sw x10, 36(x8)
bgeu x6, x0, r20
sll x12, x7, x9
lui x28, 882430
r20:
la x16, r21
jalr x0, 0(x16)
xori x11, x6, 299
r21:
jal x1, r22
slti x28, x7, -1073
lbu x7, -16(x8)
r22:
add x13, x9, x12
li x17, 3
r23:
lui x13, 715060
lw x28, -32(x8)
addi x9, x6, 1843
slt x29, x28, x11
addi x17, x17, -1
bnez x17, r23
sb x7, 12(x8)
jal x0, r24
and x6, x7, x28
r24:
jal x1, r25
sltiu x6, x0, -1832
sltiu x5, x0, 1802
r25:
jal x1, r26
sub x7, x5, x28
r26:
la x16, r27
jalr x1, 0(x16)
addi x13, x0, 1471
sb x12, -60(x8)
r27:
and x9, x6, x0
li x17, 3
r28:
lhu x6, -40(x8)
andi x6, x5, -1088
sb x29, -8(x8)
addi x17, x17, -1
bnez x17, r28
addi x11, x0, -1088
bne x10, x29, r29
lb x6, -56(x8)
lb x29, -20(x8)
r29:
li x17, 3
r30:
srai x9, x29, 15
add x28, x7, x11
sw x0, 16(x8)
sltiu x5, x29, -1086
addi x17, x17, -1
bnez x17, r30
sll x28, x29, x29
bltu x0, x28, r31
sltu x10, x7, x28
r31:
slli x0, x9, 6
sh x5, 44(x8)
li x17, 3
r32:
lh x6, -4(x8)
andi x13, x6, -372
sra x9, x13, x0
addi x17, x17, -1
bnez x17, r32
xori x10, x6, -1842
jal x1, r33
slli x7, x13, 16
r33:
slli x7, x6, 1
sw x28, -60(x8)
sltu x11, x11, x9
bge x5, x10, r34
srai x5, x9, 28
andi x5, x11, -1388
sw x13, -20(x8)
r34:
add x29, x7, x0
lui x6, 442698
slt x6, x7, x0
la x16, r35
jalr x1, 0(x16)
slti x11, x5, 564
r35:
xori x13, x28, -1032
li x17, 3
r36:
or x0, x29, x0
or x12, x5, x9
add x7, x11, x7
sw x5, -8(x8)
addi x17, x17, -1
bnez x17, r36
sltiu x29, x6, 637
lui x29, 465306
li x17, 3
r37:
lhu x9, -36(x8)
srl x28, x13, x29
addi x17, x17, -1
bnez x17, r37
or x11, x7, x12
lw x9, -52(x8)
bne x6, x12, r38
and x11, x11, x7
slt x7, x7, x5
r38:
srl x5, x28, x29
lw x29, -20(x8)
li x17, 3
r39:
xor x9, x13, x13
sltiu x9, x11, 1095
addi x17, x17, -1
bnez x17, r39
li x17, 3
r40:
sh x6, 48(x8)
srli x7, x29, 27
addi x17, x17, -1
bnez x17, r40
bgeu x0, x0, r41
ori x11, x7, 429
r41:
bgeu x29, x10, r42
lbu x11, 32(x8)
r42:
sb x0, 56(x8)
bltu x28, x11, r43
sw x6, 56(x8)
andi x9, x28, 1546
lb x11, -40(x8)
r43:
jal x0, r44
slti x29, x29, 302
lw x28, 28(x8)
r44:
li x17, 3
r45:
xor x9, x0, x10
sw x6, -64(x8)
sh x11, 56(x8)
sw x0, 12(x8)
addi x17, x17, -1
bnez x17, r45
xori x28, x0, -1406
sh x13, -44(x8)
bgeu x10, x13, r46
addi x7, x29, 401
r46:
xor x5, x0, x0
lh x6, 44(x8)
beq x0, x0, r47
or x7, x7, x0
r47:
bne x0, x0, r48
addi x0, x9, -1584
r48:
li x17, 3
r49:
sltu x13, x7, x28
and x28, x28, x12
addi x17, x17, -1
bnez x17, r49
add x5, x12, x0
bge x5, x0, r50
andi x11, x7, -978
r50:
jal x0, r51
sb x10, 60(x8)
lw x12, 12(x8)
r51:
beq x0, x6, r52
sltu x10, x0, x13
r52:
bgeu x10, x9, r53
sub x28, x10, x29
r53:
xori x13, x6, -1391
la x16, r54
jalr x1, 0(x16)
sra x28, x0, x10
andi x10, x10, 1224
r54:
li x17, 3
r55:
andi x5, x10, 1025
sra x13, x7, x0
xori x6, x13, 1916
addi x17, x17, -1
bnez x17, r55
bge x13, x13, r56
lw x29, -52(x8)
xor x13, x5, x6
r56:
lui x7, 278089
and x28, x6, x5
sltu x28, x0, x10
xor x6, x0, x0
bltu x6, x13, r57
xori x11, x5, -1686
and x10, x0, x0
r57:
li x17, 3
r58:
sra x11, x7, x6
sltiu x29, x9, -1710
lui x13, 15216
addi x17, x17, -1
bnez x17, r58
lb x6, -56(x8)
or x6, x9, x0
addi x6, x10, 1719
sltu x9, x9, x0
lb x29, 12(x8)
li x17, 3
r59:
sltiu x10, x12, 1686
sb x11, -48(x8)
and x11, x29, x11
xor x7, x12, x10
addi x17, x17, -1
bnez x17, r59
lw x11, -16(x8)
la x16, r60
jalr x0, 0(x16)
sw x28, -52(x8)
lui x9, 357375
r60:
la x16, r61
jalr x0, 0(x16)
sub x28, x5, x7
r61:
slli x12, x5, 16
li x17, 3
r62:
lhu x5, -40(x8)
xori x28, x11, -544
xor x9, x28, x0
addi x17, x17, -1
bnez x17, r62
li x17, 3
r63:
xori x28, x0, -192
sltiu x12, x6, -1399
sb x11, 44(x8)
addi x17, x17, -1
bnez x17, r63
jal x1, r64
srl x0, x7, x12
r64:
blt x7, x10, r65
sltu x11, x0, x29
sh x28, 36(x8)
r65:
bgeu x29, x28, r66
lb x13, -20(x8)
slti x9, x9, -369
r66:
bge x0, x0, r67
lw x13, -24(x8)
r67:
sh x10, -64(x8)
bne x6, x10, r68
andi x6, x7, 1518
add x13, x11, x0
lw x28, 60(x8)
r68:
srl x10, x0, x0
lb x13, 0(x8)
slli x28, x9, 18
or x10, x10, x0
la x16, r69
jalr x0, 0(x16)
slti x28, x10, -1140
lw x11, 24(x8)
r69:
srl x13, x12, x10
srai x5, x10, 24
sll x5, x0, x0
sw x0, 32(x8)
la x16, r70
jalr x1, 0(x16)
addi x11, x6, -1674
r70:
li gp, 1
ecall
fail:
ecall

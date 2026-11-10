# constrained-random pipeline stress seed=4 (generated)
li x8, 20480
li x5, 1013818839
li x6, 1302657532
li x7, 443094727
li x9, 3097603021
li x10, 1701057193
li x11, 2056767043
li x12, 665600858
li x13, 386977619
li x28, 285680177
li x29, 85114131
sw x12, -32(x8)
sw x28, -28(x8)
sw x10, -24(x8)
sw x5, -20(x8)
sw x9, -16(x8)
sw x28, -12(x8)
sw x28, -8(x8)
sw x11, -4(x8)
sw x10, 0(x8)
sw x7, 4(x8)
sw x6, 8(x8)
sw x10, 12(x8)
sw x9, 16(x8)
sw x5, 20(x8)
sw x10, 24(x8)
sw x10, 28(x8)
andi x0, x11, -1338
la x16, r1
jalr x1, 0(x16)
slli x6, x13, 17
sltu x11, x5, x10
r1:
blt x28, x9, r2
xori x28, x13, -727
add x12, x6, x5
r2:
sw x0, 20(x8)
lhu x10, -16(x8)
bge x10, x7, r3
sltiu x13, x0, -421
sb x0, -8(x8)
r3:
lui x11, 256157
add x29, x5, x11
blt x0, x0, r4
xor x28, x7, x0
andi x29, x6, 355
r4:
bge x10, x7, r5
sltiu x5, x29, -1972
slti x29, x11, 923
r5:
li x17, 3
r6:
srl x9, x9, x6
sll x9, x29, x0
sb x28, 60(x8)
lui x5, 74603
addi x17, x17, -1
bnez x17, r6
srai x12, x9, 30
addi x6, x9, 1402
lw x13, -12(x8)
sltu x12, x9, x28
sll x12, x11, x5
li x17, 3
r7:
srli x12, x0, 2
xori x11, x9, -693
andi x5, x11, 1392
addi x17, x17, -1
bnez x17, r7
lh x13, 36(x8)
li x17, 3
r8:
sh x5, 36(x8)
sw x0, -52(x8)
addi x17, x17, -1
bnez x17, r8
la x16, r9
jalr x1, 0(x16)
lbu x10, -64(x8)
add x5, x29, x10
r9:
lbu x10, -52(x8)
la x16, r10
jalr x0, 0(x16)
lw x6, 56(x8)
r10:
li x17, 3
r11:
and x7, x6, x13
srai x12, x7, 2
addi x9, x10, 793
addi x17, x17, -1
bnez x17, r11
jal x0, r12
xori x29, x9, 1938
sb x6, -36(x8)
r12:
li x17, 3
r13:
srli x13, x0, 28
sltu x7, x13, x12
sll x11, x11, x7
addi x17, x17, -1
bnez x17, r13
xor x6, x10, x28
li x17, 3
r14:
lw x5, 12(x8)
sra x13, x0, x29
addi x17, x17, -1
bnez x17, r14
srl x11, x10, x11
add x0, x0, x5
blt x28, x13, r15
xori x7, x29, 1573
ori x12, x11, 737
and x11, x7, x0
r15:
jal x0, r16
sh x29, 24(x8)
lb x11, 36(x8)
r16:
bne x11, x0, r17
addi x29, x29, -1884
srli x11, x6, 10
r17:
sb x6, -20(x8)
bgeu x0, x9, r18
lw x29, 36(x8)
sw x0, -8(x8)
andi x10, x11, 1653
r18:
li x17, 3
r19:
srli x5, x13, 26
lui x12, 385650
sw x12, 32(x8)
addi x17, x17, -1
bnez x17, r19
bne x28, x6, r20
sw x29, 12(x8)
sw x9, 56(x8)
r20:
li x17, 3
r21:
sub x11, x10, x7
sw x29, 0(x8)
addi x17, x17, -1
bnez x17, r21
slt x12, x5, x11
and x28, x0, x0
sll x12, x0, x0
andi x5, x28, -772
sra x29, x28, x6
or x12, x12, x28
bge x11, x7, r22
sltu x6, x0, x5
addi x29, x7, -1099
r22:
la x16, r23
jalr x0, 0(x16)
sra x5, x0, x28
r23:
lh x10, -20(x8)
la x16, r24
jalr x0, 0(x16)
sltiu x7, x0, 1338
r24:
beq x0, x9, r25
srli x13, x13, 21
lbu x11, 16(x8)
r25:
la x16, r26
jalr x0, 0(x16)
slli x7, x7, 2
ori x10, x0, -2
r26:
lw x6, -32(x8)
beq x28, x28, r27
and x10, x10, x29
r27:
li x17, 3
r28:
sw x0, -28(x8)
xor x11, x10, x12
lui x11, 71390
sub x6, x28, x28
addi x17, x17, -1
bnez x17, r28
lw x9, 44(x8)
srl x5, x10, x11
jal x1, r29
slti x29, x10, 242
srli x6, x10, 18
r29:
bgeu x7, x29, r30
and x5, x6, x0
slt x12, x0, x13
r30:
jal x1, r31
slti x9, x6, -48
r31:
sltu x5, x29, x29
bgeu x6, x0, r32
sh x0, -12(x8)
r32:
lui x0, 688160
bltu x11, x7, r33
lb x9, -24(x8)
r33:
beq x0, x10, r34
sb x9, -32(x8)
ori x28, x13, 603
addi x11, x5, -564
r34:
xor x11, x29, x9
li x17, 3
r35:
ori x9, x0, -1132
sw x7, -12(x8)
slt x13, x10, x0
lhu x10, -56(x8)
addi x17, x17, -1
bnez x17, r35
li x17, 3
r36:
lbu x5, 32(x8)
lui x7, 746426
sra x28, x5, x0
lbu x12, -36(x8)
addi x17, x17, -1
bnez x17, r36
lui x9, 164408
sb x7, -4(x8)
bltu x5, x0, r37
slt x13, x29, x7
lui x28, 383697
lui x10, 912568
r37:
bltu x0, x11, r38
lw x10, 24(x8)
r38:
addi x10, x28, -802
sw x13, -36(x8)
lui x7, 333384
lw x28, -52(x8)
andi x11, x5, -826
sltu x9, x13, x10
ori x28, x0, -1537
la x16, r39
jalr x1, 0(x16)
or x7, x29, x11
sub x13, x12, x5
r39:
sh x9, -44(x8)
li x17, 3
r40:
sw x6, -44(x8)
srai x6, x7, 12
addi x17, x17, -1
bnez x17, r40
slli x9, x7, 27
li x17, 3
r41:
sw x28, 20(x8)
lw x28, -36(x8)
addi x17, x17, -1
bnez x17, r41
bltu x6, x29, r42
or x13, x0, x12
r42:
li gp, 1
ecall
fail:
ecall

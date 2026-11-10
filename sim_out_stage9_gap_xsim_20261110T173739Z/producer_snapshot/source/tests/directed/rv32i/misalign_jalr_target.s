# generated negative test
li t0, 1
la t1, T
addi t1, t1, 2
jalr x6, 0(t1)
T: ebreak

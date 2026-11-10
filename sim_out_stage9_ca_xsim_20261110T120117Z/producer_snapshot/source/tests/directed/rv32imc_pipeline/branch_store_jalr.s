lui x2, 4
la x9, done
c.beqz x9, fail
c.swsp x9, 0
c.lwsp x10, 0
jalr x11, 0(x10)
c.ebreak
done:
addi x12, x11, 0
c.ebreak
fail:
ecall

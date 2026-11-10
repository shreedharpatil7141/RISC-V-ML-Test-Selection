lui x2, 4
lui x8, 4
c.li x15, 31
c.sw x15, 124(x8)
c.lw x15, 124(x8)
c.swsp x15, 252
c.lwsp x9, 252
c.addi x15, -32
c.slli x15, 31
c.srli x15, 31
c.add x8, x15
ecall

  c.li x8, 0
  c.beqz x8, taken
  c.li x9, 1
taken:
  c.addi x8, 1
  c.j linksite
  c.li x10, 2
linksite:
  jal x11, afterjal
  c.addi x12, 1
afterjal:
  jalr x13, 6(x11)
  c.ebreak

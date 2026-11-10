  lui x2, 0x4
  c.swsp x0, 252
  c.lwsp x8, 252
  c.addi x8, -32
  c.mv x9, x8
  la x9, finish
  c.jr x9
  c.li x10, 3
finish:
  c.ebreak

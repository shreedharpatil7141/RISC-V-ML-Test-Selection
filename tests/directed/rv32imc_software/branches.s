c.li x8, 0
c.beqz x8, target
c.li x9, 1
target: c.li x9, 2
c.bnez x8, fail
c.ebreak
fail: c.li x9, 3
c.ebreak

  c.li x8, 1
  c.bnez x8, branch_target
  c.nop
branch_target:
  c.jal call_target
  c.ebreak
call_target:
  c.ebreak

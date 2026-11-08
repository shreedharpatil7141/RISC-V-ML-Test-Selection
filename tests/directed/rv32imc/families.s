# Explicit C mnemonics; test Q0/Q1/Q2 families and expanded RV32I/M operations.
  c.addi4spn x8, 16
  c.li x9, -32
  c.lui x10, 1
  c.addi x9, 31
  c.slli x10, 31
  c.srli x8, 1
  c.srai x9, 31
  c.andi x9, -32
  c.sub x8, x9
  c.xor x9, x10
  c.or x8, x9
  c.and x10, x8
  c.addi16sp -16
  c.mv x11, x10
  c.add x11, x8
  c.sw x11, 124(x8)
  c.lw x12, 124(x8)
  c.nop
  c.ebreak

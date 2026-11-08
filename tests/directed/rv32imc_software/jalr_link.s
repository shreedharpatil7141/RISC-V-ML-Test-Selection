# C.JALR target is halfword aligned; x1 receives the address after 2 bytes.
la x5, target
c.jalr x5
c.nop
target: c.ebreak

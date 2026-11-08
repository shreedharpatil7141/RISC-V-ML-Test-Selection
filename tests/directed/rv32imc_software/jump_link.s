# RV32-only C.JAL: target is halfword aligned; x1 receives PC+2.
c.jal target
c.nop
c.nop
target: c.ebreak

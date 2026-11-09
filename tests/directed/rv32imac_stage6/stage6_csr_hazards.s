li x5, 9
csrrw x5, 0x800, x5
csrrw x6, 0x800, x5
csrrw x5, 0x800, x6
csrrs x7, 0x800, x0
ecall

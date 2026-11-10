li x7, 0x123
csrrw x8, 0x800, x7
csrrs x9, 0x800, x0
csrrc x10, 0x800, x0
csrrw x14, 0x800, x0
csrrw x15, 0x800, x7
csrrwi x11, 0x801, 5
csrrsi x12, 0x801, 0
csrrci x13, 0x801, 1
ecall

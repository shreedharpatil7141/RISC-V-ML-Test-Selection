li x1, 0x5000
li x2, 0x89abcdef
sw x2, 0(x1)
lr.w x1, (x1)
li x3, 0x5000
li x4, 0x76543210
lr.w x5, (x3)
sc.w x3, x4, (x3)
li x6, 0x5000
lr.w x8, (x6)
li x9, 0x13579bdf
sc.w x9, x9, (x6)
li x7, 0x0f0f0f0f
amoswap.w x7, x7, (x6)
ecall

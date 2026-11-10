c.addi x0, 0
li x1, 100
li x2, 5
div x3, x1, x2
li x4, 0x5000
amoadd.w x5, x3, (x4)
div x6, x1, x2
ecall

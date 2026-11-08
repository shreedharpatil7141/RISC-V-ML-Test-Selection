li x1, 0x5000
li x2, 9
jal x0, target
amoadd.w x3, x2, (x1)
target:
ecall

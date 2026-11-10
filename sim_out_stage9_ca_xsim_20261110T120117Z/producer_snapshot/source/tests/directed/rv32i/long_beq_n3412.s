# long-offset b d=-3412 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 3472
S: li gp, 2
beq x0, x0, -3412
j fail

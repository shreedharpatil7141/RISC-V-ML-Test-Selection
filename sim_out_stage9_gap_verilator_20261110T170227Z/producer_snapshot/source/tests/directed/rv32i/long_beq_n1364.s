# long-offset b d=-1364 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 1424
S: li gp, 2
beq x0, x0, -1364
j fail

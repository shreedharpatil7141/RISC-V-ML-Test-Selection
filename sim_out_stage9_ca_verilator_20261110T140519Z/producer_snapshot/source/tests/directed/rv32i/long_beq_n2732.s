# long-offset b d=-2732 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 2792
S: li gp, 2
beq x0, x0, -2732
j fail

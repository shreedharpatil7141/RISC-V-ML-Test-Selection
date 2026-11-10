# long-offset b d=-1024 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 1084
S: li gp, 2
beq x0, x0, -1024
j fail

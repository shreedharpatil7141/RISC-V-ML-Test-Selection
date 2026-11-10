# long-offset b d=2048 (generated)
li gp, 2
beq x0, x0, 2048
j fail
.org 2052
li gp, 1
ecall
fail:
ecall

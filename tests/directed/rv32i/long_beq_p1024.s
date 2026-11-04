# long-offset b d=1024 (generated)
li gp, 2
beq x0, x0, 1024
j fail
.org 1028
li gp, 1
ecall
fail:
ecall

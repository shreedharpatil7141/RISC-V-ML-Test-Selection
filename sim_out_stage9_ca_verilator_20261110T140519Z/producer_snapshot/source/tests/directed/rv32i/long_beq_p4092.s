# long-offset b d=4092 (generated)
li gp, 2
beq x0, x0, 4092
j fail
.org 4096
li gp, 1
ecall
fail:
ecall

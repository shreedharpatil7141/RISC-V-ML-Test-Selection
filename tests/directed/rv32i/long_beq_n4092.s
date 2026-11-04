# long-offset b d=-4092 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 4152
S: li gp, 2
beq x0, x0, -4092
j fail

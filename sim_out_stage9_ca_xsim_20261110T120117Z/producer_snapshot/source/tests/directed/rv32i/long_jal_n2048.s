# long-offset j d=-2048 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 2108
S: li gp, 2
jal x0, -2048
j fail

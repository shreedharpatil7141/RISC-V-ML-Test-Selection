# long-offset j d=-4096 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 4156
S: li gp, 2
jal x0, -4096
j fail

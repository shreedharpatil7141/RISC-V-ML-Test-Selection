# long-offset j d=-8192 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 8252
S: li gp, 2
jal x0, -8192
j fail

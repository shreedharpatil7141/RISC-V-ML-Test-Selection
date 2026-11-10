# long-offset j d=4096 (generated)
li gp, 2
jal x0, 4096
j fail
.org 4100
li gp, 1
ecall
fail:
ecall

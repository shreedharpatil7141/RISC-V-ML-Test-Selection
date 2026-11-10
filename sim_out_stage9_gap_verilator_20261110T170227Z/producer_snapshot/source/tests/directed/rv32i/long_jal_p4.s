# long-offset j d=4 (generated)
li gp, 2
jal x0, 4
j fail
.org 8
li gp, 1
ecall
fail:
ecall

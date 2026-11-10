# long-offset j d=8 (generated)
li gp, 2
jal x0, 8
j fail
.org 12
li gp, 1
ecall
fail:
ecall

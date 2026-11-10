# long-offset j d=64 (generated)
li gp, 2
jal x0, 64
j fail
.org 68
li gp, 1
ecall
fail:
ecall

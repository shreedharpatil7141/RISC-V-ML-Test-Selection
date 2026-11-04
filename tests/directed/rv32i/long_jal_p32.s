# long-offset j d=32 (generated)
li gp, 2
jal x0, 32
j fail
.org 36
li gp, 1
ecall
fail:
ecall

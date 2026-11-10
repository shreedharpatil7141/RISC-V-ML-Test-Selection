# long-offset j d=16 (generated)
li gp, 2
jal x0, 16
j fail
.org 20
li gp, 1
ecall
fail:
ecall

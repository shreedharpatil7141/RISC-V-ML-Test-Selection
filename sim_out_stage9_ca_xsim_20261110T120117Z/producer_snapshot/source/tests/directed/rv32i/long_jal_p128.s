# long-offset j d=128 (generated)
li gp, 2
jal x0, 128
j fail
.org 132
li gp, 1
ecall
fail:
ecall

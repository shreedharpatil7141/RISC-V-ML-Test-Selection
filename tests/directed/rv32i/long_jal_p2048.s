# long-offset j d=2048 (generated)
li gp, 2
jal x0, 2048
j fail
.org 2052
li gp, 1
ecall
fail:
ecall

# long-offset j d=1024 (generated)
li gp, 2
jal x0, 1024
j fail
.org 1028
li gp, 1
ecall
fail:
ecall

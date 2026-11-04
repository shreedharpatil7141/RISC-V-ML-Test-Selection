# long-offset j d=8192 (generated)
li gp, 2
jal x0, 8192
j fail
.org 8196
li gp, 1
ecall
fail:
ecall

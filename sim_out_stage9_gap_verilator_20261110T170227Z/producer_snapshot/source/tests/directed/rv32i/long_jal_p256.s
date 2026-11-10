# long-offset j d=256 (generated)
li gp, 2
jal x0, 256
j fail
.org 260
li gp, 1
ecall
fail:
ecall

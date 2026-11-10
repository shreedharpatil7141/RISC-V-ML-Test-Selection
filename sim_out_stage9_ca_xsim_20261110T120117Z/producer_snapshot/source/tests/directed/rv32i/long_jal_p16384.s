# long-offset j d=16384 (generated)
li gp, 2
jal x0, 16384
j fail
.org 16388
li gp, 1
ecall
fail:
ecall

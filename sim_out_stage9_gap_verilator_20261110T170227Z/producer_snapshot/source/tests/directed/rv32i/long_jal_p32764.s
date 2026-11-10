# long-offset j d=32764 (generated)
li gp, 2
jal x0, 32764
j fail
.org 32768
li gp, 1
ecall
fail:
ecall

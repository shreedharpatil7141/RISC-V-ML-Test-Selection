# long-offset j d=-32764 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 32824
S: li gp, 2
jal x0, -32764
j fail

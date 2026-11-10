# long-offset j d=-21844 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 21904
S: li gp, 2
jal x0, -21844
j fail

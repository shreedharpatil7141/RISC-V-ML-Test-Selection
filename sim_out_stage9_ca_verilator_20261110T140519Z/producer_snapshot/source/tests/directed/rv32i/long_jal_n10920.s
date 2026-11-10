# long-offset j d=-10920 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 10980
S: li gp, 2
jal x0, -10920
j fail

# long-offset j d=-32768 (generated)
j S
.org 64
li gp, 1
ecall
fail:
ecall
.org 32828
S: li gp, 2
jal x0, -32768
j fail

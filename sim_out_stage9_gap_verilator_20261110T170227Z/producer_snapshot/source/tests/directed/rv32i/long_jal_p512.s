# long-offset j d=512 (generated)
li gp, 2
jal x0, 512
j fail
.org 516
li gp, 1
ecall
fail:
ecall

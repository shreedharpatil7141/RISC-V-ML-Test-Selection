# long-offset j d=32768 (generated)
li gp, 2
jal x0, 32768
j fail
.org 32772
li gp, 1
ecall
fail:
ecall

# Older DIV completes/retires before a younger illegal instruction halts the core.
li x5, 100
li x6, 9
div x7, x5, x6
add x8, x7, x0
.word 0x00000000
div x9, x5, x6

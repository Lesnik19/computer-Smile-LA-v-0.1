; Программа "BIOS". На экран выводится число 12, пользователь выбирает программу (1 или 2), после чего биос 
; переносит нас на выполнение той или ной программы. Из-за оссобенности реализации, для экономии места, 
; любая клавиша, кроме 2, будет считаться за 1.

.org 0x01

SCREEN = 0xF0

bios:
LDI 0x12
STA 0xF0
INP
CMP 2
JZ two

one:
LDI 0xEF
STA SCREEN
JMP bios

two:
INP
STA sum
INP
.byte 0b00011000    ; ADD
sum:
.byte 0
CMP 10
JC ten
ADD 0xF0
STA SCREEN
JMP bios
ten:
SUB 10
ADD 0x10
STA SCREEN
JMP bios

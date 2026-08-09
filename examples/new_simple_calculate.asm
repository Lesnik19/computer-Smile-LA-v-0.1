; Программа "Простой калькулятор", но переписанна без хардкода адресов (начало экрана на всякий то же вынону, чтобы если адрес поменяется в последующих версиях, то было чуток проще).
.org 0x01

SCREEN = 0xF0

JMP 0x10

.org 0x10
INP
STA sum
INP
.byte 0b00011000
sum:
.byte 0
CMP 10
JC ten
ADD 0xF0
STA SCREEN
HLT
ten:
SUB 10
ADD 0x10
STA SCREEN
HLT

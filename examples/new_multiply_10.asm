; Программа "Умножитель", но переписанна без хардкода адресов. 
.org 0x01

SCREEN = 0xF0

INP
STA one_multiply
.byte 0b00011000    ; ADD
one_multiply:
.byte 0
STA two_multiply
.byte 0b00011000    ; ADD
two_multiply:
.byte 0
STA three_multiply
.byte 0b00011000    ; ADD
three_multiply:
.byte 0
STA four_multiply
LDA two_multiply
.byte 0b00011000    ; ADD
four_multiply:
.byte 0
STA SCREEN
HLT

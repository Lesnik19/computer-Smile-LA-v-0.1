# Ассемблер для компьютера Smile LA, версия 0.1

import sys
from enum import IntEnum
import base64

file_name = input("Введите имя файла для компиляции: ")

# Если вам нужно запустить один и тот же файл много раз, то будет проще его просто
# указать ниже, не забыв раскомментировать строку

# file_name = "name.asm"

# ----------------------------------------------------------------------------------------
# Библиотека от kala-telo для перевода готового машинного кода в вид для Logic Arrows
# ----------------------------------------------------------------------------------------


class Direction(IntEnum):
    North = 0
    East  = 1
    South = 2
    West  = 3

class ArrowType(IntEnum):
    Empty                  = 0
    Arrow                  = 1
    Source                 = 2
    Blocker                = 3
    Delay                  = 4
    Detector               = 5
    SplitterUpDown         = 6
    SplitterUpRight        = 7
    SplitterUpRightLeft    = 8
    Pulse                  = 9
    BlueArrow              = 10
    Diagonal               = 11
    BlueSplitterUpUp       = 12
    BlueSplitterRightUp    = 13
    BlueSplitterUpDiagonal = 14
    Not                    = 15
    And                    = 16
    Xor                    = 17
    Latch                  = 18
    Flipflop               = 19
    Random                 = 20
    Button                 = 21
    LevelSource            = 22
    LevelTarget            = 23
    DirectoinalButton      = 24
    Unknown                = 25


class Arrow:
    def __init__(self, type: ArrowType = ArrowType.Empty, direction: Direction = Direction.North, flipped = False):
        self.type = type
        self.direction = direction
        self.flipped = flipped

    direction: Direction = Direction.North
    flipped: bool = False
    type: ArrowType = ArrowType.Empty

class Chunk:
    arrows: list[Arrow]
    def __init__(self):
        self.arrows = ([Arrow()] * 256).copy()

    def get(self, x: int, y: int) -> Arrow:
        return self.arrows[y*16+x]
    def set(self, x: int, y: int, arrow: Arrow):
        self.arrows[y*16+x] = arrow

class Map:
    version: int = 0
    chunks: dict[tuple[int, int], Chunk]

    def __init__(self, string: None|str = None):
        self.chunks = {}
        if string is not None:
            self.import_(string)

    def get(self, x: int, y: int) -> Arrow:
        chunk_x = x//16
        chunk_y = y//16
        arrow_x = x % 16
        arrow_y = y % 16
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk()
        return self.chunks[(chunk_x, chunk_y)].get(arrow_x, arrow_y)

    def set(self, x: int, y: int, arrow: Arrow):
        chunk_x = x//16
        chunk_y = y//16
        arrow_x = x % 16
        arrow_y = y % 16
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk()

        self.chunks[(chunk_x, chunk_y)].set(arrow_x, arrow_y, arrow)

    def import_(self, string: str):
        raw_data = base64.b64decode(string)
        def pop8() -> int:
            nonlocal raw_data
            val = raw_data[:1]
            raw_data = raw_data[1:]
            return int.from_bytes(val, byteorder='little')
        def pop16() -> int:
            nonlocal raw_data
            val = raw_data[:2]
            raw_data = raw_data[2:]
            return int.from_bytes(val, byteorder='little', signed=True)

        self.version = pop16()
        chunks_count = pop16()
        for _ in range(chunks_count):
            chunk_x = pop16()
            chunk_y = pop16()
            arrow_types = pop8()+1
            for _ in range(arrow_types):
                type = pop8()
                type_count = pop8()+1
                for _ in range(type_count):
                    position = pop8()
                    x = position & 0x0F
                    y = (position & 0xF0) >> 4
                    direction_and_flipped = pop8()
                    direction = direction_and_flipped & 0b011
                    flipped = direction_and_flipped & 0b100 != 0
                    arrow = Arrow()
                    arrow.flipped = flipped
                    arrow.type = ArrowType(type)
                    arrow.direction = Direction(direction)
                    self.set(chunk_x*16 + x, chunk_y*16 + y, arrow)

    def export(self) -> str:
        raw_data = bytearray([])
        def push8(val: int):
            nonlocal raw_data
            raw_data.extend(val.to_bytes(byteorder='little', length=1))
        def push16(val: int):
            nonlocal raw_data
            raw_data.extend(val.to_bytes(byteorder='little', length=2, signed=True))


        push16(self.version)
        push16(len(self.chunks))
        for cords, chunk in self.chunks.items():
            types: list[ArrowType] = []
            for arrow in chunk.arrows:
                if arrow.type != ArrowType.Empty and arrow.type not in types:
                    types.append(arrow.type)
            if types == []: continue
            push16(cords[0])
            push16(cords[1])
            push8(len(types)-1)
            for type in types:
                push8(type)
                push8(0)
                types_count_index = len(raw_data)-1
                types_count = 0
                for x in range(16):
                    for y in range(16):
                        arrow = chunk.get(x, y)
                        if arrow.type != type: continue
                        position = x | (y<<4)
                        rotation = arrow.direction | (arrow.flipped << 2)
                        push8(position)
                        push8(rotation)
                        types_count += 1
                raw_data[types_count_index] = types_count-1
        return base64.b64encode(raw_data).decode('utf-8')

    def paste(self, x: int, y: int, src: Self|str):
        # for typecheck
        if isinstance(src, str):
            m = Map(src)
        else:
            m = src

        for chunk_x, chunk_y in m.chunks:
            chunk = m.chunks[(chunk_x, chunk_y)]
            for i, arrow in enumerate(chunk.arrows):
                arrow_x = chunk_x * 16 + i % 16 + x
                arrow_y = chunk_y * 16 + i // 16 + y
                self.set(arrow_x, arrow_y, arrow)


# ----------------------------------------------------------------------------------------

first_word = None
address = int(0x00)
org_exist = False

lines = []
clean_lines = []
output = []

commands = {"HLT":"00000000", "LDA":"00001000", "STA":"00010000", "ADD":"00011000",
            "SUB":"00100000", "CMP":"00101000", "LDI":"00110000", "JMP":"00111000",
            "JZ":"01000000", "JC":"01001000", "INP":"01010000",}
labels = {}
const = {}


def error_mes(num, mes):
    print(f"Ошибка в строке {num}:")
    print(lines[num-1])
    print(mes)
    sys.exit(1)


def const_name(name):
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    for l in name:
        if not (l.isupper() or l.isdigit() or l == "_"):
            return False
    return True


def game_output(bytes):
    point_x = None
    point_y = None
    m = Map()
    for i in bytes:
        if type(i) == int:
            point_y = i % 16
            point_x = i // 16
        else:
            if point_y != 0:
                m.set(point_x * 30, point_y * 7, Arrow(type=ArrowType.Pulse))
                for n, j in enumerate(i[::-1], start=1):
                    if j == "0":
                        m.set(point_x * 30 + n, point_y * 7, Arrow(type=ArrowType.Unknown))
                    else:
                        m.set(point_x * 30 + n, point_y * 7, Arrow(type=ArrowType.Pulse))

            else:
                m.set(point_x * 30, point_y * 7 + 1, Arrow(type=ArrowType.Pulse))
                for n, j in enumerate(i[::-1], start=1):
                    if j == "0":
                        m.set(point_x * 30 + n, point_y * 7 + 1, Arrow(type=ArrowType.Unknown))
                    else:
                        m.set(point_x * 30 + n, point_y * 7 + 1, Arrow(type=ArrowType.Pulse))

            point_y += 1
            if point_y == 16:
                point_y = 0
                point_x += 1

    return m.export()


# ----------------------------------------------------------------------------------------

file = open(file_name, 'r')
lines = file.readlines()
file.close()

for i in lines:
    clean_lines.append(i.split(";")[0].strip())

for n, i in enumerate(clean_lines, start=1):
    try:
        if not i.strip():
            continue

        first_word = i.split()[0]
        if not org_exist:
            if first_word == ".org":
                org_exist = True
            else:
                error_mes(n, f"Код всегда должен начинаться с директивы '.org'!")
        if first_word == ".org":
            second = i.split()[1]
            try:
                if not (0 <= int(second, 16) <= 255):
                    error_mes(n, "Адрес выходит за рамки допустимых значений (0-255)!")
                address = int(second, 16)
            except ValueError:
                if second in const:
                    address = const[second]
                else:
                    error_mes(n, f"Неизвестная константа '{second}'!")

        elif ":" in i:
            labels[i.split(":")[0]] = address

        elif first_word == ".byte":
            for j in i.split()[1:]:
                address += 1
                try:
                    if j.split(",")[1] != "":
                        error_mes(n, "При использовании директивы .byte при перечислении нескольких значений, они должны разделяться запятой и пробелом!")
                except IndexError:
                    pass

        else:
            if first_word in commands:
                if first_word != "HLT" and first_word != "INP":
                    address += 2
                else:
                    address += 1
            else:
                if "=" in i and const_name(first_word):
                    const[first_word] = int(i.split()[-1], 0)
                else:
                    error_mes(n, "Неизвестная команда или неверное название константы!")

    except Exception as e:
          error_mes(n, f"Ошибка разбора строки: {e}")

print(clean_lines)
address = int(0x00)

for n, i in enumerate(clean_lines, start=1):
    try:
        if not i.strip():
            continue

        first_word = i.split()[0]
        if first_word == ".org":
            second = i.split()[1]
            try:
                addr = int(second, 16)
            except ValueError:
                if second in const:
                    addr = const[second]
                else:
                    error_mes(n, f"Неизвестная константа '{second}' в .org")
            output.append(addr)
            address = addr

        elif first_word == ".byte":
            for j in i.split()[1:]:
                if j.split(",")[0] != "$":
                    try:
                        output.append(f"{int(j.split(",")[0], 0):08b}")
                    except:
                        try:
                            output.append(f"{const[j.rstrip(",")]:08b}")
                        except:
                            error_mes(n, "Неизвестная константа!")
                else:
                    output.append(f"{address:08b}")
                address += 1

        elif first_word in commands:
            output.append(commands.get(first_word))
            if first_word == "HLT" or first_word == "INP":
                address += 1
                continue

            second_word = None
            try:
                second_word = i.split()[1]
                num = int(second_word, 0)
                if not (0 <= num <= 255):
                    error_mes(n, "Число выходит за рамки допустимых значений (0-255)!")
                output.append(f"{num:08b}")

            except (IndexError, ValueError):
                if second_word is None:
                    error_mes(n, "Отсутствует операнд у команды")
                elif second_word == "$":
                    output.append(f"{address:08b}")
                elif second_word in const:
                    output.append(f"{const[second_word]:08b}")
                elif second_word in labels:
                    output.append(f"{labels[second_word]:08b}")
                else:
                    error_mes(n, f"Неизвестная метка или константа: '{second_word}'")

            address += 2

    except Exception as e:
        error_mes(n, f"Ошибка разбора строки: {e}")

print(output)
print(game_output(output))

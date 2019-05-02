# -*- coding: utf-8 -*-
import os
from enum import IntEnum
import random
import time

#リアルタイムにキーボード入力を処理する
import readchar

#キー入力処理。
import  msvcrt

#これはキーロガーとして使える。
from pyhooked import Hook, KeyboardEvent, MouseEvent

#########################################################################
# ブロック表示用各変数

FIELD_WIDTH = 8
FIELD_HEIGHT = 8

BLOCK_TYPE_MAX = 7

class CELL_TYPE(IntEnum):
    NONE = 0
    BLOCK_0 = 1
    BLOCK_1 = 2
    BLOCK_2 = 3
    BLOCK_3 = 4
    BLOCK_4 = 5
    BLOCK_5 = 6
    BLOCK_6 = 7
    MAX = 8

cellAA = ["・", "〇", "△", "□", "●", "▲", "■", "☆"]

#これはだめ同じリストを複数持つことになるので１つ値を変更すると他の行も変更される。
#cells = [[0]*FIELD_HEIGHT]*FIELD_WIDTH
#こちらを使う。これならそれぞれが別の値を持つ。
cells = [[0 for x in range(FIELD_WIDTH)] for y in range(FIELD_HEIGHT)]
checked = [[0 for x in range(FIELD_WIDTH)] for y in range(FIELD_HEIGHT)]
#########################################################################

# 処理中止の入力用
CTRL_C = 3

#ブロック消去処理中フラグ
locked = True

try:
    from msvcrt import getch
except ImportError:
    def getch():
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


#_count 連結している数
def getConnectedBlockCount(_x, _y, _cellType, _count):
#    print("_x={}, y={}".format(_x, _y), end=" ")
    if (_x < 0 or _x >= FIELD_WIDTH or _y < 0 or _y >= FIELD_HEIGHT
        or checked[_y][_x]
        or cells[_y][_x] == CELL_TYPE.NONE
        or cells[_y][_x] != _cellType):
        return _count
    _count = _count + 1
    checked[_y][_x] = True
    _count = getConnectedBlockCount(_x, _y-1, _cellType, _count)
    _count = getConnectedBlockCount(_x-1, _y, _cellType, _count)
    _count = getConnectedBlockCount(_x, _y+1, _cellType, _count)
    _count = getConnectedBlockCount(_x+1, _y, _cellType, _count)
    return _count

def eraseConnectedBlocks(_x, _y, _cellType):
    if (_x < 0 or _x >= FIELD_WIDTH or _y < 0 or _y >= FIELD_HEIGHT
        or cells[_y][_x] == CELL_TYPE.NONE
        or cells[_y][_x] != _cellType):
        return

    cells[_y][_x] = CELL_TYPE.NONE
    eraseConnectedBlocks(_x, _y-1, _cellType)
    eraseConnectedBlocks(_x-1, _y, _cellType)
    eraseConnectedBlocks(_x, _y+1, _cellType)
    eraseConnectedBlocks(_x+1, _y, _cellType)

################################################
#接続しているブロックをすべて消去
################################################
def eraseConnectedBlocksAll():
    global locked
    #checkedを0埋めする。以下の方法では最初だけしか0埋めされない。
    #checked = [[0 for x in range(FIELD_WIDTH)] for y in range(FIELD_HEIGHT)]
    fillList(checked, 0)
    for y in range(FIELD_HEIGHT):
        for x in range(FIELD_WIDTH):
            n = getConnectedBlockCount(x, y, cells[y][x], 0)
            if n >= 3:
                eraseConnectedBlocks(x, y, cells[y][x])
                locked = True;

################################################
#引数で指定されたリストの要素すべてに_valを代入
################################################
def fillList(_list, _val):
    for y in range(FIELD_HEIGHT):
        for x in range(FIELD_WIDTH):
            _list[y][x] = _val

################################################
# cells[y][x]にしたがって画面表示
################################################
def display(_selectedX, _selectedY, _cursorX, _cursorY):
    global locked
    os.system('cls')
    for y in range(FIELD_HEIGHT):
        for x in range(FIELD_WIDTH):
            if x == _cursorX and y == _cursorY and not locked:
                print("◎", end="")
            else:
                print(cellAA[cells[y][x]], end="")
        if y == _selectedY:
            print("←", end="")
        print("")

    for x in range(FIELD_WIDTH):
        print("↑" if x == _selectedX else "　", end="")
    print("")

################################################
# キーロガー用イベントハンドラ
################################################
def handle_events(args):
    if isinstance(args, KeyboardEvent):
        print(args.key_code, args.current_key, args.event_type)

    if isinstance(args, MouseEvent):
        print(args.mouse_x, args.mouse_y)

def handle_events_key(args):
    if isinstance(args, KeyboardEvent):
        print("yes")
        return True
    else:
        print("no")
        return False

################################################
# ブロックを落とす。
################################################
def dropBlocks(_cells):
    global locked
    seed = time.time()
    rnd = random.Random(seed)
    if locked:
        locked = False
        for y in range(FIELD_HEIGHT-2, -1, -1):
            for x in range(FIELD_WIDTH):
                if (_cells[y][x] != CELL_TYPE.NONE
                    and _cells[y+1][x] == CELL_TYPE.NONE):
                    _cells[y+1][x] = _cells[y][x]
                    _cells[y][x] = CELL_TYPE.NONE
                    locked = True

        for x in range(FIELD_WIDTH):
            if (_cells[0][x] == CELL_TYPE.NONE):
                _cells[0][x] = CELL_TYPE.BLOCK_0 + rnd.randrange(FIELD_WIDTH) % BLOCK_TYPE_MAX
                locked = True
        if not locked:
            eraseConnectedBlocksAll()

################################################
#１回目に選択されたセルと２回目の選択セルとを交換
################################################
def swapCells(_cursorY, _cursorX, _selectedY, _selectedX):
    global cells

    temp = cells[_cursorY][_cursorX]
    cells[_cursorY][_cursorX] = cells[_selectedY][_selectedX]
    cells[_selectedY][_selectedX] = temp

#################################################################
# 画面に表示する記号を保持する、cells[y][x]にランダムな値を代入。
#################################################################
def InitCells():
    seed = time.time()
    rnd = random.Random(seed)

    for y in range(FIELD_HEIGHT):
        for x in range(FIELD_WIDTH):
            rr = CELL_TYPE.BLOCK_0 + rnd.randrange(FIELD_WIDTH) % BLOCK_TYPE_MAX
            cells[y][x] = rr

################################################
#Match 3 Game main
################################################
def puzdragame():
    global locked
    cursorX = 0
    cursorY = 0
    selectedX = -1
    selectedY = -1

#    hk = Hook()  # make a new instance of PyHooked
#    hk.handler = handle_events_key  # add a new shortcut ctrl+a, or triggered on mouseover of (300,400)
    InitCells()
    stt = time.gmtime()
    while(True):
        if stt < time.gmtime():
            stt = time.gmtime()
            dropBlocks(cells)
            display(selectedX, selectedY, cursorX, cursorY)
# キーロガー処理
#        if hk.hook():  # hook into the events, and listen to the presses

        #キー入力がなければ以下の処理はしない。
        if not msvcrt.kbhit():
            continue

        if locked:
            #ブロック消去中なのでキー入力は捨てる。
            chIn = readchar.readkey()
            continue

        chIn = readchar.readkey()
        print("")
        if chIn == CTRL_C:
            break
        if chIn == 'k':
            cursorY = cursorY - 1
        elif chIn == 'j':
            cursorY = cursorY + 1
        elif chIn == 'h':
            cursorX = cursorX - 1
        elif chIn == 'l':
            cursorX = cursorX + 1
        elif chIn == 'x':
            break
        else:
            if selectedX < 0:   # no selected block. i.e. first selection.
                selectedX = cursorX
                selectedY = cursorY
            else:   #second selection
                distance = abs(selectedX - cursorX) + abs(selectedY - cursorY)
                if distance == 0:
                    selectedX = selectedY = -1
                elif distance == 1:
                    swapCells(cursorY, cursorX, selectedY, selectedX)
                    eraseConnectedBlocksAll()
                    selectedX = selectedY = -1
                    locked = True
                else:
                    print("\a")
        display(selectedX, selectedY, cursorX, cursorY)

if __name__ == '__main__':
    puzdragame()

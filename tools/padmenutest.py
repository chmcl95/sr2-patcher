#!/usr/bin/env python3
"""The pad on the multiplayer screens under Unicorn.

    python3 tools/padmenutest.py

padmenu.asm's entry with the European build's addresses in place, called
as the poll's site is: ecx the level packed so far, edx the previous
level, the return address the site's. It asks the poll slot's routine
for side 0's twelve inputs with the stdcall frame the annex's page poll
expects, ORs what is down into the level as the screens' bits, makes
the edge against the previous level, stores level, edge and previous,
returns thirteen bytes past the site, and sets bit 13 of the keyboard
word on a press of Back - once per press, never with the slot empty.
The registers come back as they were.

Needs python3-unicorn; exits 0 with a note when it is missing.
"""
import struct

from uctest import patcher
import uctest

uctest.unicorn('padmenutest')
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_EDI

CODE, STUBS, STACK = 0x900000, 0xa00000, 0xb00000
ROW = patcher.BUILDS['European']
A = ROW['addresses']
LEVEL, EDGE, PREV, KEYS, SLOT = A['PADLEVEL'], A['PADEDGE'], A['PADPREV'], A['MENUKEYS'], A['PADPOLL']
UP, DOWN, LEFT, RIGHT, START, BACK, LS_LEFT, LS_RIGHT, LS_UP, LS_DOWN, BTN_A, BTN_B = 0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 12, 13


def main():
    blob = patcher.exe_blob(patcher.PADMENU_BLOB, 'European')
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    for addr in (CODE, STUBS, STACK):
        mu.mem_map(addr, 0x10000)
    for addr in (LEVEL, EDGE, PREV, KEYS, SLOT):
        try:
            mu.mem_map(addr & ~0xfff, 0x1000)
        except Exception:
            pass
    mu.mem_write(CODE, blob)
    mu.mem_write(STUBS, b'\xc2\x0c\x00')      # the poll: what it answers happens in the hook
    state = {'down': {}, 'calls': []}

    def poll(mu, addr, size, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        source, value, rng = struct.unpack('<III', mu.mem_read(esp + 4, 12))
        state['calls'].append(source)
        v = state['down'].get(source - 0x300, 0)
        full = 10000 if source - 0x300 >= 16 else 0x80
        mu.mem_write(value, struct.pack('<I', v))
        mu.mem_write(rng, struct.pack('<I', full))
        mu.reg_write(UC_X86_REG_EAX, 0)
    mu.hook_add(UC_HOOK_CODE, poll, begin=STUBS, end=STUBS + 1)

    def frame(down, level=0, prev=None, slot=STUBS):
        state['down'] = down
        mu.mem_write(SLOT, struct.pack('<I', slot))
        if prev is None:
            prev = struct.unpack('<I', mu.mem_read(PREV, 4))[0]
        for addr in (LEVEL, EDGE):
            mu.mem_write(addr, b'\0' * 4)
        esp = STACK + 0x8000
        mu.mem_write(esp, struct.pack('<I', CODE + len(blob) - 13))    # the site's return: +13 is the end
        mu.reg_write(UC_X86_REG_ESP, esp)
        regs = {UC_X86_REG_EAX: 0x11111111, UC_X86_REG_ESI: 0x22222222, UC_X86_REG_EDI: 0x33333333, UC_X86_REG_EBP: 0x44444444}
        for r, v in regs.items():
            mu.reg_write(r, v)
        mu.reg_write(UC_X86_REG_ECX, level)
        mu.reg_write(UC_X86_REG_EDX, prev)
        mu.emu_start(CODE, CODE + len(blob))
        assert mu.reg_read(UC_X86_REG_ESP) == esp + 4, 'the stack came back wrong'
        for r, v in regs.items():
            assert mu.reg_read(r) == v, 'a register came back changed'
        got = [struct.unpack('<I', mu.mem_read(a, 4))[0] for a in (LEVEL, EDGE, PREV, KEYS)]
        assert got[0] == got[2], 'the previous level is not the level'
        return got[0], got[1], got[3]

    mu.mem_write(KEYS, b'\0' * 4)
    mu.mem_write(PREV, b'\0' * 4)
    assert frame({}) == (0, 0, 0), 'bits with nothing pressed'
    assert frame({UP: 0x80}) == (1, 1, 0), 'D-pad up'
    assert frame({UP: 0x80}) == (1, 0, 0), 'up held: an edge again'
    assert frame({DOWN: 0x80, LEFT: 0x80, RIGHT: 0x80}) == (0xe, 0xe, 0), 'down, left, right'
    assert frame({LS_UP: 10000, LS_LEFT: 5001}) == (5, 1, 0), 'the stick past half: up new, left still down'
    assert frame({LS_DOWN: 5000, LS_RIGHT: 4999}) == (0, 0, 0), 'the stick at half or under'
    assert frame({BTN_A: 0x80, BTN_B: 0x80, START: 0x80}) == (0x8030, 0x8030, 0), 'A, B, Start'
    assert frame({}, level=0x8000, prev=0x8000) == (0x8000, 0, 0), 'the wrapper\'s own bits lost'
    assert frame({UP: 0x80}, level=0x10, prev=0x10) == (0x11, 1, 0), 'the annex\'s bits not added to the wrapper\'s'
    assert frame({BACK: 0x80}) == (0, 0, 0x2000), 'no TAB on a press of Back'
    mu.mem_write(KEYS, b'\0' * 4)                                     # the tasks clear the word each frame
    assert frame({BACK: 0x80}) == (0, 0, 0), 'TAB again while held'
    assert frame({}) == (0, 0, 0), 'TAB on the release'
    mu.mem_write(KEYS, struct.pack('<I', 0x8000))
    assert frame({BACK: 0x80}) == (0, 0, 0xa000), 'the keyboard word\'s other bits lost'
    assert sorted(set(state['calls'])) == sorted(0x300 + i for i in (0, 1, 2, 3, 4, 5, 12, 13, 18, 19, 20, 21)), 'the wrong sources asked for'
    n = len(state['calls'])
    mu.mem_write(KEYS, b'\0' * 4)
    assert frame({UP: 0x80, BACK: 0x80}, level=3, prev=1, slot=0) == (3, 2, 0) and len(state['calls']) == n, 'the empty slot: not the site\'s own stores'
    print('padmenutest: OK')


if __name__ == '__main__':
    main()

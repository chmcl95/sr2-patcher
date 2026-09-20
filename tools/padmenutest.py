#!/usr/bin/env python3
"""The pad's Back as TAB under Unicorn.

    python3 tools/padmenutest.py

padmenu.asm's entry with the European build's addresses in place: it
makes the six-byte store the site made, asks the poll slot's routine
for source 0x305 with the stdcall frame the annex's page poll expects,
and sets bit 13 of the keyboard word on a press - once per press, not
while held, and never with the slot empty. The registers come back as
they were.

Needs python3-unicorn; exits 0 with a note when it is missing.
"""
import struct

from uctest import patcher
import uctest

uctest.unicorn('padmenutest')
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EBP

CODE, STUBS, STACK = 0x900000, 0xa00000, 0xb00000
ROW = patcher.BUILDS['European']
EDGE, KEYS, SLOT = ROW['addresses']['PADEDGE'], ROW['addresses']['MENUKEYS'], ROW['addresses']['PADPOLL']


def main():
    blob = patcher.exe_blob(patcher.PADMENU_BLOB, 'European')
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    for addr in (CODE, STUBS, STACK):
        mu.mem_map(addr, 0x10000)
    for addr in (EDGE, KEYS, SLOT):
        try:
            mu.mem_map(addr & ~0xfff, 0x1000)
        except Exception:
            pass
    mu.mem_write(CODE, blob)
    mu.mem_write(STUBS, b'\xc2\x0c\x00')      # the poll: what it answers happens in the hook
    state = {'down': 0, 'calls': []}

    def poll(mu, addr, size, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        source, value, rng = struct.unpack('<III', mu.mem_read(esp + 4, 12))
        state['calls'].append(source)
        mu.mem_write(value, struct.pack('<I', 0x80 if state['down'] else 0))
        mu.mem_write(rng, struct.pack('<I', 0x80))
        mu.reg_write(UC_X86_REG_EAX, 0)
    mu.hook_add(UC_HOOK_CODE, poll, begin=STUBS, end=STUBS + 1)

    def frame(down, slot=STUBS):
        state['down'] = down
        mu.mem_write(SLOT, struct.pack('<I', slot))
        mu.mem_write(EDGE, b'\0' * 4)
        esp = STACK + 0x8000
        mu.mem_write(esp, struct.pack('<I', CODE + len(blob)))
        mu.reg_write(UC_X86_REG_ESP, esp)
        regs = {UC_X86_REG_EAX: 0x11111111, UC_X86_REG_ECX: 0x22222222, UC_X86_REG_EDX: 0x8007, UC_X86_REG_EBP: 0x33333333}
        for r, v in regs.items():
            mu.reg_write(r, v)
        mu.emu_start(CODE, CODE + len(blob))
        assert mu.reg_read(UC_X86_REG_ESP) == esp + 4, 'the stack came back wrong'
        for r, v in regs.items():
            assert mu.reg_read(r) == v, 'a register came back changed'
        assert struct.unpack('<I', mu.mem_read(EDGE, 4))[0] == 0x8007, 'the store was not made'
        return struct.unpack('<I', mu.mem_read(KEYS, 4))[0]

    mu.mem_write(KEYS, b'\0' * 4)
    assert frame(0) == 0, 'TAB with nothing pressed'
    assert frame(1) == 0x2000, 'no TAB on the press'
    mu.mem_write(KEYS, b'\0' * 4)             # the tasks clear the word each frame
    assert frame(1) == 0, 'TAB again while held'
    assert frame(0) == 0, 'TAB on the release'
    assert frame(1) == 0x2000, 'no TAB on the second press'
    mu.mem_write(KEYS, struct.pack('<I', 0x8000))
    state['down'] = 0
    frame(0)
    assert frame(1) == 0xa000, 'the word\'s other bits lost'
    assert set(state['calls']) == {0x305}, 'a source other than side 0\'s Back asked for'
    n = len(state['calls'])
    mu.mem_write(KEYS, b'\0' * 4)
    assert frame(1, slot=0) == 0 and len(state['calls']) == n, 'the empty slot called'
    print('padmenutest: OK')


if __name__ == '__main__':
    main()

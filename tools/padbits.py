#!/usr/bin/env python3
"""Which action the exe's screens read as each menu direction.

    python3 tools/padbits.py GAMEDIR

Runs the exe's pad-flag routine (0x43f8e0) under Unicorn with the input
wrapper stubbed, one action at a time, and prints the bit each lands on
against what the screens test there. See docs/NOTES.md, *The menus'
directions*. European build only: the routine's address is the European
one, and this is a tool to look with, not a check.
"""
import struct
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from uctest import unicorn                      # noqa: E402  the skip when it is missing

uc = unicorn('padbits')
from unicorn.x86_const import UC_X86_REG_ESP    # noqa: E402

EXE = 'SEGA RALLY 2.exe'
BASE = 0x400000
POLL = 0x43f8e0
HOLDER = 0x50b120        # -> object; [obj+8] the input wrapper
FLAGS_EDGE = 0x4ef7e4
FLAGS_LEVEL = 0x4ef7c4
PREV = 0x4ef7d4
REPEAT = (0x4b5630, 0x4b5634, 0x4b5638)

STACK = 0x200000
SCRATCH = 0x700000       # our stubbed objects live here; 0x700ff0 holds the action mask
RET = 0x900000


def load(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    nsec = struct.unpack_from('<H', raw, pe + 6)[0]
    opt = struct.unpack_from('<H', raw, pe + 20)[0]
    size = struct.unpack_from('<I', raw, pe + 24 + 56)[0]
    img = bytearray(size)
    img[:struct.unpack_from('<I', raw, pe + 24 + 60)[0]] = raw[:struct.unpack_from('<I', raw, pe + 24 + 60)[0]]
    for i in range(nsec):
        s = pe + 24 + opt + i * 40
        rva = struct.unpack_from('<I', raw, s + 12)[0]
        rsz = struct.unpack_from('<I', raw, s + 16)[0]
        ptr = struct.unpack_from('<I', raw, s + 20)[0]
        img[rva:rva + rsz] = raw[ptr:ptr + rsz]
    return bytes(img)


def probe(game):
    img = load(game + '/' + EXE)
    mu = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
    mu.mem_map(BASE, (len(img) + 0xfff) & ~0xfff | 0x1000)
    mu.mem_write(BASE, img)
    mu.mem_map(STACK - 0x10000, 0x20000)
    mu.mem_map(SCRATCH, 0x1000)
    mu.mem_map(RET, 0x1000)

    # the stub the wrapper's vtable +0x1c points at: mov eax, [0x6ffff0]; ret 4
    stub = SCRATCH + 0x100
    mu.mem_write(stub, bytes.fromhex('a1f00f7000') + b'\xc2\x04\x00')
    vtbl = SCRATCH + 0x200
    mu.mem_write(vtbl, struct.pack('<8I', *([0] * 7 + [stub])))   # +0x1c is slot 7
    obj = SCRATCH + 0x300
    mu.mem_write(obj, struct.pack('<I', vtbl))
    holder = SCRATCH + 0x400
    mu.mem_write(holder, struct.pack('<2I', 0, 0) + struct.pack('<I', obj))  # [holder+8] = obj
    mu.mem_write(HOLDER, struct.pack('<I', holder))

    names = {0: 'accel', 1: 'brake', 2: 'up', 3: 'down', 4: 'left', 5: 'right', 6: 'shift up',
             7: 'shift down', 8: 'handbrake', 9: 'view', 10: 'enter', 11: 'escape', 12: 'start'}
    menu = {0: 'UP', 1: 'DOWN', 2: 'LEFT', 3: 'RIGHT', 4: 'CONFIRM', 5: 'CANCEL', 15: 'ENTER'}
    print('%-4s %-11s %-10s %s' % ('act', 'name', 'menu bit', 'meaning'))
    for act in range(13):
        for addr, val in ((PREV, 0), (FLAGS_EDGE, 0), (FLAGS_LEVEL, 0),
                          (REPEAT[0], 1000), (REPEAT[1], 1000), (REPEAT[2], 1000)):
            mu.mem_write(addr, struct.pack('<I', val))
        mu.mem_write(0x700ff0, struct.pack('<I', 1 << act))
        mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.mem_write(STACK, struct.pack('<I', RET))
        mu.emu_start(POLL, RET)
        edge = struct.unpack('<I', mu.mem_read(FLAGS_EDGE, 4))[0]
        bits = [b for b in range(32) if edge >> b & 1]
        print('%-4d %-11s %-10s %s' % (act, names.get(act, '?'),
                                       ','.join(str(b) for b in bits) or '-',
                                       ' '.join(menu.get(b, '?') for b in bits)))


if __name__ == '__main__':
    probe(sys.argv[1])

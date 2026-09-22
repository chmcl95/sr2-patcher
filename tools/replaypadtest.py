#!/usr/bin/env python3
"""The replay's camera controls under Unicorn, against the real exe.

    python3 tools/replaypadtest.py GAMEDIR

The exe patched with replaypad alone and its own update of the replay
controls (the routine the site is in) run a frame at a time, with the
input wrapper, MGInput's GetDevice and the keyboard's GetState stubbed
and the annex's page poll answered from a table. Checked: the keyboard's
fixed keys as before with the poll's slot empty and with it set; the
D-pad and stick past half as the directions, A, B and X as 0x30, 0xc0
and 0x100; the edge made from the level; the stick's x as the analog
when the keyboard's is 0 and the keyboard's kept when not; player 2 on
side 1's sources and its own keys.

Needs python3-unicorn and pefile; exits 77 with a note when missing.
"""
import os
import struct
import sys

from uctest import patcher

try:
    import pefile
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EAX
except ImportError:
    print('replaypadtest: skipped, python3-unicorn or pefile not installed')
    sys.exit(77)

HEAP, STACK, STUBS = 0x2000000, 0x2100000, 0x2200000
HOLDER, WRAPPER, INPUT, DEVICE, KEYS, OBJ = (HEAP + 0x100 * i for i in range(1, 7))
KEYARRAY = HEAP + 0x1000
UPDATE_TO_SITE = 0xba                   # the join from the routine's start, every build
UP, DOWN, LEFT, RIGHT, LS_LEFT, LS_RIGHT, LS_UP, LS_DOWN, BTN_A, BTN_B, BTN_X = 0, 1, 2, 3, 18, 19, 20, 21, 12, 13, 14


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip())
        return 2
    build = patcher.check_build(argv[1])
    with open(os.path.join(argv[1], patcher.EXE), 'rb') as fh:
        buf = bytearray(fh.read())
    out = patcher.apply_replaypad(buf, build)
    row = patcher.BUILDS[build]
    pe = pefile.PE(data=bytes(out))
    base = pe.OPTIONAL_HEADER.ImageBase
    image = pe.get_memory_mapped_image()
    site = base + 0x1000 + row['sites']['replaypad'] - patcher._rva_to_off(out, 0x1000)
    update = site - UPDATE_TO_SITE
    if image[update - base:update - base + 4] != bytes.fromhex('83ec10a1'):
        raise SystemExit('replaypadtest: the update routine is not 0x%x before the site' % UPDATE_TO_SITE)
    holder_slot = struct.unpack_from('<I', image, update - base + 4)[0]
    slot = row['addresses']['PADPOLL']

    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(base, (len(image) + 0xfff) & ~0xfff)
    mu.mem_write(base, bytes(image))
    for addr in (HEAP, STACK, STUBS):
        mu.mem_map(addr, 0x10000)
    w = lambda a, *v: mu.mem_write(a, struct.pack('<%dI' % len(v), *v))
    r = lambda a: struct.unpack('<I', mu.mem_read(a, 4))[0]
    rs = lambda a: struct.unpack('<i', mu.mem_read(a, 4))[0]

    # stubs: ret n at STUBS + 0x10 * k; what they do happens in the hook
    GETDEVICE, GETSTATE, RELEASE, POLL = STUBS, STUBS + 0x10, STUBS + 0x20, STUBS + 0x30
    for addr, n in ((GETDEVICE, 16), (GETSTATE, 12), (RELEASE, 4), (POLL, 12)):
        mu.mem_write(addr, b'\xc2' + struct.pack('<H', n))
    w(holder_slot, HOLDER)
    w(HOLDER + 8, WRAPPER)
    w(WRAPPER + 4, INPUT)
    w(INPUT, INPUT + 0x40)
    w(INPUT + 0x40 + 0x20, GETDEVICE)
    w(DEVICE, DEVICE + 0x40)
    w(DEVICE + 0x40 + 8, RELEASE)
    w(DEVICE + 0x40 + 0x38, GETSTATE)
    state = {'pad': {}, 'calls': [], 'kinds': []}

    def hook(mu, addr, size, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        if addr == GETDEVICE:
            _this, kind, _index, out_ = struct.unpack('<IIII', mu.mem_read(esp + 4, 16))
            state['kinds'].append(kind)
            w(out_, DEVICE)
        elif addr == GETSTATE:
            _this, out_, _n = struct.unpack('<III', mu.mem_read(esp + 4, 12))
            w(out_, KEYARRAY)
        elif addr == POLL:
            source, value, rng = struct.unpack('<III', mu.mem_read(esp + 4, 12))
            state['calls'].append(source)
            full = 10000 if (source & 0x3f) >= 16 else 0x80
            w(value, state['pad'].get(source, 0))
            w(rng, full)
        mu.reg_write(UC_X86_REG_EAX, 0)
    mu.hook_add(UC_HOOK_CODE, hook, begin=STUBS, end=STUBS + 0x40)

    def setup(players):
        mu.mem_write(OBJ, bytes(0x40))
        w(OBJ + 4, players)
        for i in range(players):
            w(OBJ + 8 + 4 * i, 3)               # the keyboard, as a config with a key first on steering gets

    def frame(keys=(), pad=None, polled=True):
        mu.mem_write(KEYARRAY, bytes(256))
        for k in keys:
            mu.mem_write(KEYARRAY + k, b'\x80')
        state['pad'] = pad or {}
        w(slot, POLL if polled else 0)
        esp = STACK + 0x8000
        w(esp, 0xDEAD0000)
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.reg_write(UC_X86_REG_ECX, OBJ)
        mu.emu_start(update, 0xDEAD0000)
        assert mu.reg_read(UC_X86_REG_ESP) == esp + 4, 'the stack came back wrong'
        n = r(OBJ + 4)
        return [(r(OBJ + 0x20 + 4 * i), r(OBJ + 0x18 + 4 * i), rs(OBJ + 0x30 + 4 * i)) for i in range(n)]

    side = lambda player, i: 0x300 + player * 0x40 + i
    setup(1)
    assert frame(keys=[0xc8], polled=False) == [(1, 1, 0)], 'the keyboard\'s up with the slot empty'
    assert state['calls'] == [], 'the poll asked with the slot empty'
    assert frame(polled=False) == [(0, 0, 0)]
    assert frame() == [(0, 0, 0)], 'bits with nothing pressed'
    assert sorted(set(state['calls'])) == sorted(side(0, i) for i in (0, 1, 2, 3, 12, 13, 14, 18, 19, 20, 21)), 'the wrong sources asked for'
    assert frame(keys=[0xd2]) == [(0x10, 0x10, 0)], 'the keyboard\'s Insert lost with the slot set'
    assert frame(pad={side(0, UP): 0x80}) == [(1, 1, 0)], 'D-pad up'
    assert frame(pad={side(0, UP): 0x80}) == [(1, 0, 0)], 'D-pad up held: an edge again'
    assert frame(pad={side(0, DOWN): 0x80, side(0, LEFT): 0x80}) == [(6, 6, 0)], 'D-pad down, left'
    assert frame(pad={side(0, BTN_A): 0x80}) == [(0x30, 0x30, 0)], 'A as the meter'
    assert frame(pad={side(0, BTN_B): 0x80}) == [(0xc0, 0xc0, 0)], 'B as TAB and Page Up'
    assert frame(pad={side(0, BTN_X): 0x80}) == [(0x100, 0x100, 0)], 'X as Page Down'
    assert frame(pad={side(0, LS_UP): 10000}) == [(1, 1, 0)], 'the stick up'
    assert frame(pad={side(0, LS_DOWN): 5000}) == [(0, 0, 0)], 'the stick at half'
    assert frame(pad={side(0, LS_RIGHT): 10000}) == [(8, 8, 127)], 'the stick right: bit and analog'
    assert frame(pad={side(0, LS_LEFT): 3000}) == [(0, 0, -38)], 'the stick a little left: analog only'
    assert frame(keys=[0xcd], pad={side(0, LS_LEFT): 10000}) == [(0xc, 0xc, 127)], 'the keyboard\'s analog overwritten'
    assert state['kinds'] and set(state['kinds']) == {3}, 'a device other than the keyboard asked for'

    setup(2)
    assert frame(keys=[0x1f], pad={side(1, BTN_A): 0x80, side(0, RIGHT): 0x80}) == [(8, 8, 0), (0x31, 0x31, 0)], \
        'player 2: its keys and side 1\'s pad'
    assert frame(pad={side(1, LS_LEFT): 10000}) == [(0, 0, 0), (4, 4, -127)], 'player 2\'s stick'
    print('replaypad: the pad and stick in the replay controls, %s' % build.lower())
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

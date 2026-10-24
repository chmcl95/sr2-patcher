#!/usr/bin/env python3
"""Run MGameD3D's light release under Unicorn, stock and patched.

    python3 tools/lightreleasetest.py GAMEDIR    # the install folder

The real MGameD3D.dll, mapped and relocated to another base, its light
wrapper's release (0x10006f70) called on a wrapper whose light holds two
references, the create's and the viewport's, as dgVoodoo's AddLight
leaves it. Stock, the light's Release is called until the count is zero.
With lightrelease it is called once, the viewport's reference is left,
and the wrapper's pointer is cleared either way. A wrapper with no light
calls nothing. Needs python3-unicorn; exits 77 with a note when it is
missing.
"""
import struct
import sys

from uctest import patcher
import uctest

uctest.unicorn('lightreleasetest')
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EIP

DBASE = 0x01DD0000
WRAPPER, LIGHT, VTABLE, RELEASE, STACK, RETURN = 0x2000000, 0x2000100, 0x2001000, 0x2002000, 0x3000000, 0xdead0000
NAME = 'MUSASHI\\MGameD3D.dll'


def run(dll, refs, light=LIGHT):
    """Calls the release on a wrapper holding light with refs references;
    returns the Release calls, the count left and the wrapper's +0x20."""
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    uctest.map_image(mu, dll, DBASE)
    mu.mem_map(WRAPPER, 0x3000)
    mu.mem_map(STACK, 0x10000)
    mu.mem_write(WRAPPER + 0x20, struct.pack('<I', light))
    mu.mem_write(LIGHT, struct.pack('<II', VTABLE, refs))
    mu.mem_write(VTABLE + 8, struct.pack('<I', RELEASE))
    # mov eax,[esp+4]; dec dword [eax+4]; mov eax,[eax+4]; ret 4
    mu.mem_write(RELEASE, bytes.fromhex('8b442404ff48048b4004c20400'))
    calls = []
    mu.hook_add(UC_HOOK_CODE, lambda mu_, a, s, u: calls.append(a), begin=RELEASE, end=RELEASE)
    esp = STACK + 0x8000
    mu.mem_write(esp, struct.pack('<I', RETURN))
    mu.reg_write(UC_X86_REG_ESP, esp)
    mu.reg_write(UC_X86_REG_ECX, WRAPPER)
    mu.emu_start(DBASE + 0x6f70, RETURN, count=1000)
    assert mu.reg_read(UC_X86_REG_EIP) == RETURN, 'did not return'
    assert mu.reg_read(UC_X86_REG_ESP) == esp + 4, 'not a plain thiscall ret'
    left = struct.unpack('<I', mu.mem_read(LIGHT + 4, 4))[0]
    held = struct.unpack('<I', mu.mem_read(WRAPPER + 0x20, 4))[0]
    return len(calls), left, held


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip())
        return 2
    stock = uctest.stock(argv[1], NAME)
    if uctest.build_of(stock, NAME) is None:
        print('lightreleasetest: %s is not a MGameD3D.dll the patcher knows' % NAME)
        return 1
    _name, sites, _transform = patcher.patches(uctest.build_of(stock, NAME))['lightrelease']
    patched = bytearray(stock)
    for off, old, new in sites:
        assert patched[off:off + len(old)] == old, 'original bytes at 0x%x' % off
        patched[off:off + len(new)] = new
    assert run(stock, 2) == (2, 0, 0), 'stock: released until zero'
    assert run(patched, 2) == (1, 1, 0), 'patched: released once, the viewport\'s reference left'
    assert run(patched, 1) == (1, 0, 0), 'patched: a light no viewport holds still goes'
    assert run(patched, 2, light=0)[0] == 0, 'no light: nothing called'
    print('lightreleasetest OK: stock releases to zero, patched once, the pointer cleared')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

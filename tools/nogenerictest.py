#!/usr/bin/env python3
"""Run the nogeneric stub under Unicorn in the real MGInput.dll.

    python3 tools/nogenerictest.py GAMEDIR  # GAMEDIR holds MUSASHI/MGInput.dll

Patches a copy in memory, maps it relocated, and enters the device
loop's site as the DLL would - the null-GUID compare's flags, eax at the
instance's guidInstance, esi the input object, edx 0 - for a null GUID,
a type-0x11 instance and a keyboard: the first two reach the loop's
skip target with nothing pushed, the last the continuation with ecx
loaded and edx pushed, as the displaced instructions did. Needs
python3-unicorn; exits 0 with a note when it is missing so
tools/check.py can skip it.
"""
import hashlib
import importlib.util
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('patcher', os.path.join(HERE, '..', 'sr2-patcher.py'))
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

try:
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI,
                                   UC_X86_REG_EDI, UC_X86_REG_EFLAGS)
except ImportError:
    print('nogenerictest: skipped, python3-unicorn not installed')
    sys.exit(0)

BASE = 0x01DD0000
SCRATCH = 0x04000000
STACK = 0x05000000
ZF = 1 << 6
VTABLE = 0x0CAFE000


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip())
        return 2
    path = os.path.join(argv[1], 'MUSASHI', 'MGInput.dll')
    if os.path.isfile(path + '.bak'):
        path += '.bak'
    with open(path, 'rb') as fh:
        raw = bytearray(fh.read())
    build = next((b for b, row in patcher.BUILDS.items()
                  if row['files']['MUSASHI\\MGInput.dll'][1] == hashlib.md5(raw).hexdigest()), None)
    if build is None:
        print('nogenerictest: %s is not an MGInput.dll the patcher knows' % path)
        return 1
    _file, sites, _t = patcher.patches(build)['nogeneric']
    for off, old, _new in sites:
        assert raw[off:off + len(old)] == old, 'bytes at 0x%x are not the original' % off
    image = patcher.apply_nogeneric(raw, build)
    at = patcher.BUILDS[build]['sites']['nogeneric']

    pe_off = struct.unpack_from('<I', image, 0x3c)[0]
    nsec = struct.unpack_from('<H', image, pe_off + 6)[0]
    opt = pe_off + 24
    size = struct.unpack_from('<I', image, opt + 56)[0]
    table = opt + struct.unpack_from('<H', image, pe_off + 20)[0]
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, (size + 0xfff) & ~0xfff)
    mu.mem_write(BASE, bytes(image[:0x1000]))
    for i in range(nsec):
        _name, _vsize, va, rsize, roff = struct.unpack_from('<8sIIII', image, table + i * 40)
        mu.mem_write(BASE + va, bytes(image[roff:roff + rsize]))
    delta = BASE - struct.unpack_from('<I', image, opt + 28)[0]
    rel_rva, rel_size = struct.unpack_from('<II', image, opt + 136)
    off = patcher._rva_to_off(image, rel_rva)
    end = off + rel_size
    while off + 8 <= end:
        page, bsize = struct.unpack_from('<II', image, off)
        if not bsize:
            break
        for i in range(8, bsize, 2):
            e = struct.unpack_from('<H', image, off + i)[0]
            if e >> 12 == 3:
                a = BASE + page + (e & 0xfff)
                v = struct.unpack('<I', mu.mem_read(a, 4))[0]
                mu.mem_write(a, struct.pack('<I', (v + delta) & 0xffffffff))
        off += bsize
    mu.mem_map(SCRATCH, 0x10000)
    mu.mem_map(STACK, 0x100000)

    site = BASE + patcher._off_to_rva(image, at)
    cont, skip = site + 5, site + 2 + 0x1c
    stopped = {}

    def stop(mu, address, size_, user):
        if address in (cont, skip):
            stopped['at'] = address
            mu.emu_stop()

    mu.hook_add(UC_HOOK_CODE, stop, begin=site, end=site + 0x40)

    this, instance = SCRATCH, SCRATCH + 0x100
    mu.mem_write(this, struct.pack('<I', VTABLE))

    def run(devtype, null_guid):
        mu.mem_write(instance, struct.pack('<I', 0x244) + b'\x11' * 32 + struct.pack('<I', devtype))
        esp = STACK + 0x80000
        mu.mem_write(esp, b'\xaa' * 0x40)
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.reg_write(UC_X86_REG_EAX, instance + 4)
        mu.reg_write(UC_X86_REG_ESI, this)
        mu.reg_write(UC_X86_REG_ECX, 0)
        mu.reg_write(UC_X86_REG_EDX, 0)
        mu.reg_write(UC_X86_REG_EDI, 0x77777777)
        mu.reg_write(UC_X86_REG_EFLAGS, 0x202 | (ZF if null_guid else 0))
        stopped.clear()
        mu.emu_start(site, 0, count=100)
        return stopped.get('at'), mu.reg_read(UC_X86_REG_ESP) - esp, mu.reg_read(UC_X86_REG_ECX), mu.reg_read(UC_X86_REG_EAX)

    assert run(0x10013, True) == (skip, 0, 0, instance + 4)          # a null GUID: skipped, as before
    assert run(0x10011, False) == (skip, 0, 0, instance + 4)         # a device of no kind: skipped now
    for devtype in (0x10012, 0x10013, 0x10014, 0x10015, 0x10016, 0x1001c, 0x00013):
        assert run(devtype, False) == (cont, -4, VTABLE, instance + 4), hex(devtype)
        assert struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP), 4))[0] == 0     # edx, pushed
    print('nogenerictest: %s MGInput.dll OK' % build)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

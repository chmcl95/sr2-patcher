#!/usr/bin/env python3
"""Run the podium's car-load thunk under Unicorn.

    python3 tools/podiumcartest.py

PODIUMCAR_BLOB is filled for each build that sites it and called as the
car loader's `call` at 0x412abd does, with eax the car just stored in
slot esi. The slot's race entry must then name the car (its model's
+4), as the stale entry of the year-2 podium did not; the other entries
must stay as they were; edx must be the car, as the displaced
`mov edx, [esi*4 + CARS]` left it; and esi, edi, ebx, ebp and the stack
must come back unchanged. Needs python3-unicorn; exits 77 with a note
when it is missing.
"""
import struct
import sys

from uctest import patcher
import uctest

uctest.unicorn('podiumcartest')
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_EDI, UC_X86_REG_EDX,
                               UC_X86_REG_ESI, UC_X86_REG_ESP)

CODE, DATA, STACK = 0x00700000, 0x01000000, 0x30000000
RETURN = 0xdead0000
CAR, MODEL, STATE = DATA + 0x10000, DATA + 0x20000, DATA + 0x30000   # STATE + 0x100 the entries, 0x30 apiece
ENTRIES, ENTRY = 0x100, 0x30
RIVAL, STALE = 17, 15                   # LANEVO4 into slot 4, over the ST185 the second course left there


def run(build, slot):
    race = patcher.BUILDS[build]['addresses']['RACE']
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(CODE, 0x1000)
    mu.mem_map(race & ~0xfff, 0x1000)
    mu.mem_map(DATA, 0x40000)
    mu.mem_map(STACK, 0x10000)
    mu.mem_write(CODE, patcher.exe_blob(patcher.PODIUMCAR_BLOB, build))
    mu.mem_write(race, struct.pack('<I', STATE))
    mu.mem_write(CAR + 0x10, struct.pack('<I', MODEL))
    mu.mem_write(MODEL + 4, struct.pack('<I', RIVAL))
    before = [13, 7, 28, 23, STALE, 16, 0, 0]
    for i, car in enumerate(before):
        mu.mem_write(STATE + ENTRIES + i * ENTRY, struct.pack('<I', car))
    esp = STACK + 0x8000
    mu.mem_write(esp, struct.pack('<I', RETURN))
    regs = {UC_X86_REG_ESP: esp, UC_X86_REG_EAX: CAR, UC_X86_REG_ESI: slot, UC_X86_REG_EDI: 0x51,
            UC_X86_REG_EBX: 0x00e06fa0, UC_X86_REG_EBP: 0x1234, UC_X86_REG_EDX: 0x0badf00d}
    for reg, value in regs.items():
        mu.reg_write(reg, value)
    mu.emu_start(CODE, RETURN, count=50)
    after = [struct.unpack('<I', mu.mem_read(STATE + ENTRIES + i * ENTRY, 4))[0] for i in range(len(before))]
    want = list(before)
    want[slot] = RIVAL
    if after != want:
        raise SystemExit('podiumcartest: %s slot %d: the entries came back %r, not %r' % (build, slot, after, want))
    if mu.reg_read(UC_X86_REG_EDX) != CAR:
        raise SystemExit('podiumcartest: %s: edx is %x, not the car' % (build, mu.reg_read(UC_X86_REG_EDX)))
    if mu.reg_read(UC_X86_REG_ESP) != esp + 4:
        raise SystemExit('podiumcartest: %s: the stack came back at %x, not %x' % (build, mu.reg_read(UC_X86_REG_ESP), esp + 4))
    for reg in (UC_X86_REG_EAX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBX, UC_X86_REG_EBP):
        if mu.reg_read(reg) != regs[reg]:
            raise SystemExit('podiumcartest: %s: a register the loader keeps came back changed' % build)


def main(argv):
    builds = [b for b, row in patcher.BUILDS.items() if 'podiumcar' in row['sites']]
    if not builds:
        raise SystemExit('podiumcartest: no build sites podiumcar')
    for build in builds:
        for slot in (4, 5):             # past a field of three: the rival, and the championship's car 14 after it
            run(build, slot)
    print('podiumcartest OK: the slot\'s entry names its car, the rest kept, on %s' % ', '.join(builds))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

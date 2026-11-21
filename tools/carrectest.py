#!/usr/bin/env python3
"""Run carslot's records blob (asm/carrec.asm) under Unicorn.

    python3 tools/carrectest.py

Maps the blob with its buffers as carslot lays them out, a save buffer
with stock rankings, the game's state and a folder table with id 30, and
stubs the routines and imports it calls in Python (the insert as the
exe's, the files in a dict). Then: a load with no files, a new car's and
a stock car's records into the shared rankings, a new car's own list and
best lap, a save, and a second run's load from what was written. Checks
the save's write sees the stock cars only, the files, and that the second
load gives the rankings back. Needs python3-unicorn; exits 77 with a note
when it is missing so tools/check.py can skip it.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uctest                           # noqa: E402

uctest.unicorn('carrectest')
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE      # noqa: E402
from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,      # noqa: E402
                               UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EIP)
import carslot                          # noqa: E402

BLOB = 0x10000000
DATA = 0x20000000
GAMEPTR, SAVEPTR, LAPTIME, FOLDERS, NAMES = DATA, DATA + 4, DATA + 8, DATA + 0x100, DATA + 0x400
GAME, SAVE = DATA + 0x1000, DATA + 0x10000
STUBS = 0x30000000
IAT = STUBS + 0x1000
STACK = 0x40000000
DONE = STUBS + 0xff0
SAVE_SIZE = 0xdb08
SHARED = [(0, 0, 16)] + [(0x100 + i * 0x80, 0x100 + i * 0x80, 8) for i in range(4)] + \
         [(0x300 + i * 0x100, 0x300 + i * 0x100, 16) for i in range(10)] + \
         [(0xd10 + c * 0xa00, 0xd00 + c * 0x80, 8) for c in range(17)]
ROUTINES = ('INSERT', 'PASSWORD', 'CODE', 'LOAD', 'SAVEFN')
IMPORTS = ('CREATEFILE', 'READFILE', 'WRITEFILE', 'CLOSE', 'GETPROC', 'GETMOD', 'LSTRCPY', 'LSTRCAT', 'LSTRCMPI')
FAILS = []


def check(what, ok):
    if not ok:
        FAILS.append(what)
    print('  %s %s' % ('ok  ' if ok else 'FAIL', what))


def entry(name, time, car, gear=0):
    return name.encode().ljust(8, b'\0')[:8] + struct.pack('<IBBH', time, car, gear, 0)


class Run:
    def __init__(self, files, save):
        lab = carslot.CARREC_LABELS
        self.files, self.dirs, self.snapshot, self.handles = files, [], None, {}
        self.passwords = []
        stub = {name: STUBS + 0x10 * i for i, name in enumerate(ROUTINES + IMPORTS + ('CREATEDIR',))}
        self.stub = stub
        values = {name: stub[name] for name in ROUTINES}
        values.update({name: IAT + 4 * i for i, name in enumerate(IMPORTS)})
        values.update(GAME=GAMEPTR, SAVE=SAVEPTR, LAPTIME=LAPTIME, FOLDERS=FOLDERS, NCAR=1, BLBACK=DONE)
        code = bytes(carslot.CARREC_BLOB)
        for name, magic in carslot.CARREC_MAGICS.items():
            code = code.replace(struct.pack('<I', magic), struct.pack('<I', values[name]))
        shadow = lab['new'] - lab['stock']
        listed = 0x1580 // 16
        new = struct.pack('<4I', 0, 0, 0xffffffff, 0xff) * listed + struct.pack('<4I', 0, 0, 0, 0xff) * (shadow // 16 - listed)
        self.carrec0 = bytes(16) + b''.join(entry('DEF%d' % c, 90000 + i, 2) for c in range(17) for i in range(8))
        blob = (code + bytes(lab['stock'] - lab['tail']) + bytes(shadow) + new + bytes(lab['carrec'] - lab['filebuf'])
                + self.carrec0)
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BLOB, (len(blob) + 0xfff) & ~0xfff)
        mu.mem_write(BLOB, blob)
        mu.mem_map(DATA, 0x20000)
        mu.mem_map(STUBS, 0x2000)
        mu.mem_map(STACK, 0x10000)
        mu.mem_write(STUBS, b'\xc3' * 0x1000)
        for i, name in enumerate(IMPORTS):
            mu.mem_write(IAT + 4 * i, struct.pack('<I', stub[name]))
        mu.mem_write(GAMEPTR, struct.pack('<II', GAME, SAVE))
        mu.mem_write(NAMES, b'FOCUS2\0')
        mu.mem_write(FOLDERS + 30 * 4, struct.pack('<I', NAMES))
        mu.mem_write(SAVE, save)
        mu.hook_add(UC_HOOK_CODE, self.on_stub, begin=STUBS, end=STUBS + 0xfff)
        self.lab = lab

    def u32(self, va):
        return struct.unpack('<I', self.mu.mem_read(va, 4))[0]

    def cstr(self, va):
        out = b''
        while True:
            c = bytes(self.mu.mem_read(va + len(out), 1))
            if c == b'\0':
                return out
            out += c

    def arg(self, i):
        return self.u32(self.mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i)

    def ret(self, value, pop=0):
        mu = self.mu
        esp = mu.reg_read(UC_X86_REG_ESP)
        mu.reg_write(UC_X86_REG_EAX, value & 0xffffffff)
        mu.reg_write(UC_X86_REG_EIP, self.u32(esp))
        mu.reg_write(UC_X86_REG_ESP, esp + 4 + pop)

    def on_stub(self, mu, address, size, _data):
        if address == DONE:
            mu.emu_stop()
            return
        name = {v: k for k, v in self.stub.items()}.get(address)
        if name is None:
            raise SystemExit('carrectest: a call to 0x%x' % address)
        getattr(self, 'do_' + name.lower())()

    def do_insert(self):                # the exe's 0x44eb80: the record at +0x280 into the list by time
        lst, n, pw = self.arg(0), self.arg(1), self.arg(2)
        rec = bytes(self.mu.mem_read(GAME + 0x280, 16))
        time = struct.unpack_from('<I', rec, 8)[0]
        old = [bytes(self.mu.mem_read(lst + 16 * i, 16)) for i in range(n)]
        place = next((i for i, e in enumerate(old) if struct.unpack_from('<I', e, 8)[0] > time), n)
        out = (old[:place] + [rec] + old[place:])[:n]
        self.mu.mem_write(lst, b''.join(out))
        if pw and place == 0:
            self.passwords.append(pw)
        self.ret(0)

    def do_password(self):
        self.passwords.append('direct')
        self.ret(0)

    def do_code(self):
        self.ret(self.arg(0))

    def do_load(self):
        self.ret(0)

    def do_savefn(self):
        self.snapshot = bytes(self.mu.mem_read(SAVE, SAVE_SIZE))
        self.ret(0)

    def do_createfile(self):
        name, access, disp = self.cstr(self.arg(0)).decode(), self.arg(1), self.arg(4)
        if access & 0x40000000:
            self.files[name] = b''
        elif name not in self.files or disp != 3:
            return self.ret(0xffffffff, 28)
        h = 0x100 + len(self.handles)
        self.handles[h] = [name, 0]
        self.ret(h, 28)

    def do_readfile(self):
        h, buf, n, got = self.arg(0), self.arg(1), self.arg(2), self.arg(3)
        name, pos = self.handles[h]
        data = self.files[name][pos:pos + n]
        self.mu.mem_write(buf, data)
        self.mu.mem_write(got, struct.pack('<I', len(data)))
        self.handles[h][1] += len(data)
        self.ret(1, 20)

    def do_writefile(self):
        h, buf, n, got = self.arg(0), self.arg(1), self.arg(2), self.arg(3)
        self.files[self.handles[h][0]] += bytes(self.mu.mem_read(buf, n))
        self.mu.mem_write(got, struct.pack('<I', n))
        self.ret(1, 20)

    def do_close(self):
        self.handles.pop(self.arg(0))
        self.ret(1, 4)

    def do_getmod(self):
        self.ret(0x77000000 if self.cstr(self.arg(0)).upper() == b'KERNEL32.DLL' else 0, 4)

    def do_getproc(self):
        self.ret(self.stub['CREATEDIR'] if self.cstr(self.arg(1)) == b'CreateDirectoryA' else 0, 8)

    def do_createdir(self):
        self.dirs.append(self.cstr(self.arg(0)).decode())
        self.ret(1, 8)

    def do_lstrcpy(self):
        self.mu.mem_write(self.arg(0), self.cstr(self.arg(1)) + b'\0')
        self.ret(self.arg(0), 8)

    def do_lstrcat(self):
        self.mu.mem_write(self.arg(0), self.cstr(self.arg(0)) + self.cstr(self.arg(1)) + b'\0')
        self.ret(self.arg(0), 8)

    def do_lstrcmpi(self):
        a, b = self.cstr(self.arg(0)).lower(), self.cstr(self.arg(1)).lower()
        self.ret((a > b) - (a < b), 8)

    def call(self, label, args=(), regs=None):
        mu = self.mu
        esp = STACK + 0x8000
        stack = struct.pack('<I', DONE) + b''.join(struct.pack('<I', a) for a in args)
        esp -= len(stack)
        mu.mem_write(esp, stack)
        mu.reg_write(UC_X86_REG_ESP, esp)
        for reg, value in (regs or {}).items():
            mu.reg_write(reg, value)
        mu.emu_start(BLOB + self.lab[label], DONE)
        return {r: mu.reg_read(r) for r in (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_ESI)}

    def record(self, rec, car_id):
        self.mu.mem_write(GAME + 0x280, rec)
        self.mu.mem_write(GAME + 0x100, struct.pack('<I', car_id))

    def shadow(self, which, off, n):
        return bytes(self.mu.mem_read(BLOB + self.lab[which] + off, 16 * n))

    def save(self, off, n):
        return bytes(self.mu.mem_read(SAVE + off, 16 * n))


def entries(raw):
    return [raw[i:i + 16] for i in range(0, len(raw), 16)]


def stock_save():
    save = bytearray(SAVE_SIZE)
    for k, (off, _s, n) in enumerate(SHARED):
        for i in range(n):
            save[off + 16 * i:off + 16 * i + 16] = entry('S%d_%d' % (k, i), 10000 * (k + 1) + 1000 * i, (k + i) % 28)
    for c in range(17):
        save[0xd604 + 16 * c:0xd614 + 16 * c] = entry('LAP%d' % c, 50000 + c, 1)
    return bytes(save)


def main():
    files = {}
    save0 = stock_save()
    print('carrectest: first run')
    r = Run(files, save0)
    r.call('load_hook')
    check('the load leaves the rankings as loaded', bytes(r.mu.mem_read(SAVE, SAVE_SIZE)) == save0)
    check('STOCK is the loaded arcade', r.shadow('stock', 0, 16) == save0[:0x100])

    new_rec = entry('NEWCAR', 500, 30, 1)
    r.record(new_rec, 30)
    r.call('hook_shared', (SAVE, 16, SAVE + 0xb710, 0))
    check('a new car tops the arcade', r.save(0, 1) == new_rec)
    check('and NEW\'s', r.shadow('new', 0, 1) == new_rec)
    check('not STOCK\'s', r.shadow('stock', 0, 16) == save0[:0x100])
    check('no password for it', r.passwords == [])
    stock_rec = entry('STOCKCAR', 600, 5)
    r.record(stock_rec, 5)
    r.call('hook_shared', (SAVE, 16, SAVE + 0xb710, 0))
    check('a stock car second in the arcade', r.save(0, 2) == new_rec + stock_rec)
    check('and first in STOCK', r.shadow('stock', 0, 1) == stock_rec)
    check('its password from STOCK', r.passwords == [SAVE + 0xb710])
    ta = 0xd10 + 3 * 0xa00
    ta_rec = entry('NEWCAR', 100, 30)
    r.record(ta_rec, 30)
    r.call('hook_shared', (SAVE + ta, 8, SAVE + 0xb840, 0x13))
    check('a new car\'s time attack total into NEW at 0xd00 + 3 * 0x80', r.shadow('new', 0xd00 + 3 * 0x80, 1) == ta_rec)
    r.mu.mem_write(GAME + 0x100, struct.pack('<I', 30))
    r.call('pw_gate', (0, 0))
    check('no ten years\' password for a new car', r.passwords == [SAVE + 0xb710])
    r.mu.mem_write(GAME + 0x100, struct.pack('<I', 5))
    r.call('pw_gate', (0, 0))
    check('one for a stock car', r.passwords == [SAVE + 0xb710, 'direct'])

    carrec = BLOB + r.lab['carrec'] + 16
    r.mu.mem_write(GAME + 0x100, struct.pack('<I', 30))
    out = r.call('s4', regs={UC_X86_REG_EDX: (2 + 3 * 20) * 0x80, UC_X86_REG_EAX: SAVE})
    check('s4: id 30\'s list is its carrec\'s', out[UC_X86_REG_ECX] == carrec + 3 * 0x80)
    out = r.call('s1', regs={UC_X86_REG_ESI: (2 + 3 * 20) * 0x80, UC_X86_REG_EDI: SAVE})
    check('s1: and +8', out[UC_X86_REG_ESI] == carrec + 3 * 0x80 + 8)
    r.mu.mem_write(GAME + 0x100, struct.pack('<I', 5))
    out = r.call('s4', regs={UC_X86_REG_EDX: (2 + 3 * 20) * 0x80, UC_X86_REG_EAX: SAVE})
    check('s4: a stock car\'s stays', out[UC_X86_REG_ECX] == SAVE + 0xd10 + (2 + 3 * 20) * 0x80)
    out = r.call('s5', (0, 1), regs={UC_X86_REG_ECX: 3 * 20 * 0x80, UC_X86_REG_EDX: SAVE})
    check('s5: the total when asked', out[UC_X86_REG_ECX] == SAVE + 0xd10 + 3 * 20 * 0x80)

    r.mu.mem_write(GAME + 0x100, struct.pack('<I', 30))
    r.mu.mem_write(GAME + 0x104, b'\x01')
    r.mu.mem_write(GAME + 0x108, b'BESTLAP\0')
    r.mu.mem_write(LAPTIME, struct.pack('<I', 40000))
    stack = bytearray(0x20)
    struct.pack_into('<I', stack, 0x10, SAVE + 0xb920)
    esp = STACK + 0x8000
    r.mu.mem_write(esp, bytes(stack))
    r.mu.reg_write(UC_X86_REG_ESP, esp)
    r.mu.reg_write(UC_X86_REG_EBX, 3)
    r.mu.emu_start(BLOB + r.lab['bestlap'], DONE)
    lap = entry('BESTLAP', 40000, 30, 1)
    check('a new car\'s best lap into NEW\'s', r.shadow('new', 0x1580 + 3 * 16, 1) == lap)
    check('the compare as replaced', r.mu.reg_read(UC_X86_REG_ESI) == SAVE + 0xb920 + 0x30
          and r.mu.reg_read(UC_X86_REG_ECX) == 50003)
    r.mu.mem_write(SAVE + 0xd604 + 3 * 16, lap)      # as the exe writes it
    r.mu.mem_write(carrec + 3 * 0x80, entry('MINE', 1234, 30, 1))     # id 30's own record
    out = r.call('s2', regs={UC_X86_REG_EDX: (2 + 3 * 20) * 0x80, UC_X86_REG_ECX: SAVE})
    check('s2: id 30\'s best time from its own list', out[UC_X86_REG_EAX] == 1234)
    out = r.call('s3', (0,) * 9 + (30,), regs={UC_X86_REG_EDX: (2 + 3 * 20) * 0x80, UC_X86_REG_EAX: SAVE})
    check('s3: by the record\'s car', out[UC_X86_REG_EBX] == carrec + 3 * 0x80)

    merged = bytes(r.mu.mem_read(SAVE, SAVE_SIZE))
    r.call('save_hook')
    snap = r.snapshot
    check('the write saw no car from 30', all(e[12] < 30 for off, _s, n in SHARED for e in entries(snap[off:off + 16 * n])))
    check('the write\'s arcade: the stock car, then the stock 15', snap[:0x100] == stock_rec + save0[:0xf0])
    check('the write\'s best lap 3 the stock one', snap[0xd604 + 48:0xd614 + 48] == save0[0xd604 + 48:0xd614 + 48])
    check('the ten years\' total of STOCK', struct.unpack_from('<I', snap, 0xd08)[0] == sum(
        struct.unpack_from('<I', snap, 0x308 + 0x100 * y)[0] for y in range(10)))
    check('the rankings back as they were after', bytes(r.mu.mem_read(SAVE, SAVE_SIZE)) == merged)
    check('RECORD made', r.dirs == ['RECORD'])
    rank, car = files.get('RECORD\\RANKING.REC', b''), files.get('RECORD\\FOCUS2.REC', b'')
    check('RANKING.REC: SR2R, one name FOCUS2', rank[:12] == b'SR2R' + struct.pack('<II', 1, 1) and rank[16:23] == b'FOCUS2\0')
    check('RANKING.REC\'s size', len(rank) == 16 + 32 + 0x1690)
    check('its arcade entry with car 0 (the name\'s)', rank[48:64] == new_rec[:12] + b'\0' + new_rec[13:])
    check('FOCUS2.REC: SR2C, its size', car[:8] == b'SR2C' + struct.pack('<I', 1) and len(car) == 64 + 17 * 0x80)
    check('its own entry marked', car[64 + 3 * 0x80 + 12] == 0xfe)

    print('carrectest: second run, from what was written')
    r2 = Run(files, snap)
    r2.call('load_hook')
    after = bytes(r2.mu.mem_read(SAVE, SAVE_SIZE))
    check('the rankings as the first run left them', all(after[o:o + 16 * n] == merged[o:o + 16 * n] for o, _s, n in SHARED))
    check('the best laps too', after[0xd604:0xd604 + 17 * 16] == merged[0xd604:0xd604 + 17 * 16])
    check('id 30\'s own list from its file', bytes(r2.mu.mem_read(BLOB + r2.lab['carrec'] + 16, 17 * 0x80))
          == bytes(r.mu.mem_read(carrec, 17 * 0x80)))
    check('STOCK the written stock', r2.shadow('stock', 0, 16) == snap[:0x100])

    print('carrectest: %s' % ('%d failed' % len(FAILS) if FAILS else 'all passed'))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Run the widescreen stubs under Unicorn.

    python3 tools/widetest.py

wide.asm (the European exe's, with a stubbed SR2.CFG): the mode check
takes a wide size from the file and asks for a re-init once, the size
setter applies it for mode 0 and keeps 800x600 for mode 1. widegl.asm:
SetViewport scales a 640x480 rect and its centre and leaves a full-size
one alone, SetPerspective widens the angle for the aspect and leaves it
at 4:3; the trace lines come out as documented. wide2d.asm: a quad in 640x480 terms comes out scaled and centred
in a 1920x1080 buffer, a full-width one stretched, one at the left edge
drawn out to it with its texture coordinate shifted, a 640x480 buffer or
another FVF untouched, and the lists likewise.
Needs python3-unicorn; exits 0 with a note when it is missing.
"""
import importlib.util
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('patcher', os.path.join(HERE, '..', 'sr2-patcher.py'))
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

try:
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EBP,
                                   UC_X86_REG_EFLAGS)
except ImportError:
    print('widetest: skipped, python3-unicorn not installed')
    sys.exit(0)

ROW = patcher.BUILDS['European']
CODE, STACK, STUBS, VTABLE, RECTS, VERTS = 0x5a0000, 0x3000000, 0x600000, 0x610000, 0x620000, 0x4000000
ZF = 1 << 6


def exe_stub():
    """WIDE_BLOB placed with its table, the exe's globals and two kernel32
    stubs around it; the profile answer is settable."""
    blob = patcher.exe_blob(patcher.WIDE_BLOB, 'European') + patcher.resolution_table()
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    for addr in (CODE, STUBS, VTABLE, RECTS, 0x4d5000, 0x495000, 0x50a000):
        mu.mem_map(addr, 0x1000)
    mu.mem_map(STACK, 0x10000)
    mu.mem_write(CODE, blob)
    slots = ROW['slots']
    mu.mem_write(slots['GetModuleFileNameA'], struct.pack('<I', STUBS))
    mu.mem_write(slots['GetPrivateProfileStringA'], struct.pack('<I', STUBS + 0x10))
    mu.mem_write(STUBS, b'\xc2\x0c\x00')                # ret 12
    mu.mem_write(STUBS + 0x10, b'\xc2\x18\x00')         # ret 24
    mu.mem_write(VTABLE + 0x114, struct.pack('<I', STUBS + 0x20))
    mu.mem_write(STUBS + 0x20, b'\xc2\x10\x00')         # SetPerspective(this, angle, near, far): ret 16
    state = {'answer': b'', 'fov': None}

    def stub(mu, address, size_, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        args = struct.unpack('<6I', mu.mem_read(esp + 4, 24))
        if address == STUBS:
            mu.mem_write(args[1], b'C:\\game\\SEGA RALLY 2.exe\0')
        elif address == STUBS + 0x10:
            assert bytes(mu.mem_read(args[0], 8)) == b'Display\0' and bytes(mu.mem_read(args[1], 11)) == b'Resolution\0'
            assert bytes(mu.mem_read(args[5], 16)) == b'C:\\game\\SR2.CFG\0'
            mu.mem_write(args[3], state['answer'] + b'\0')
        elif address == STUBS + 0x20:
            state['fov'] = args[1]
            state['args'] = args[:4]
        mu.reg_write(UC_X86_REG_EAX, 0)

    mu.hook_add(UC_HOOK_CODE, stub, begin=STUBS, end=STUBS + 0x30)

    def call(entry, *args, eax=0, ecx=0, edx=0, retaddr=0xDEAD0000):
        """The entry, with the stack as the site's function has it: args
        from its own return address up. ebx as set before."""
        esp = STACK + 0x8000
        mu.mem_write(esp, struct.pack('<I', retaddr) + b''.join(struct.pack('<I', a) for a in args))
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.reg_write(UC_X86_REG_EAX, eax)
        mu.reg_write(UC_X86_REG_ECX, ecx)
        mu.reg_write(UC_X86_REG_EDX, edx)
        mu.emu_start(CODE + entry, retaddr, count=100000)
        return mu
    return mu, call, state


def size(mu):
    return tuple(struct.unpack('<I', mu.mem_read(ROW['addresses'][k], 4))[0] for k in ('WIDTH', 'HEIGHT'))


def angle(hfov, w, h):
    return round(2 * math.atan(math.tan(hfov / 2) * (w / h) / (4 / 3)) * 65536 / (2 * math.pi))


def test_gl():
    """widegl.asm over a stand-in MGameD3D's size dwords, found through a
    stubbed GetModuleHandleA; each entry with the stack as the method
    has it, the method's epilogue standing in for its body."""
    base, rva, d3d = 0x10000000, 0x20000, 0x20000000
    blob = patcher.WIDEGL_BLOB.replace(struct.pack('<I', patcher.FULLWIN_MAGIC), struct.pack('<I', rva))
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(base, 0x30000)
    mu.mem_map(d3d, 0x13000)
    mu.mem_map(STACK, 0x10000)
    mu.mem_map(RECTS, 0x1000)
    mu.mem_map(STUBS, 0x1000)
    mu.mem_write(base + rva, blob)
    for site, length in zip((0x37c0, 0x3870), (10, 9)):
        mu.mem_write(base + site + length, b'\x8b\xe5\x5d\xc3')     # the method resumes: its epilogue, back to the test
    mu.mem_write(STUBS + 0x40, b'\xc2\x04\x00')                      # GetModuleHandleA
    mu.mem_write(base + 0x1008c, struct.pack('<I', STUBS + 0x40))
    found = {'d3d': False}

    def module(mu, address, size_, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        name = bytes(mu.mem_read(struct.unpack('<I', mu.mem_read(esp + 4, 4))[0], 20)).split(b'\0')[0]
        if name != b'MGameD3D.dll':
            raise SystemExit('widetest: GetModuleHandleA asked for %r' % name)
        found['d3d'] = True
        mu.reg_write(UC_X86_REG_EAX, d3d)
    mu.hook_add(UC_HOOK_CODE, module, begin=STUBS + 0x40, end=STUBS + 0x43)

    def size(w, h):
        mu.mem_write(d3d + 0x123fc, struct.pack('<II', int(w), int(h)))

    def call(entry, *args, retaddr=0x0046c04f, above=0x00421819):
        """The entry as called from the exe's wrapper (a return in the
        exe's image, the wrapper's own caller's above its three saved
        registers) unless retaddr or above says a DLL - relocated, so
        anywhere else."""
        esp = STACK + 0x8000
        mu.mem_write(esp, struct.pack('<I', retaddr) + b''.join(struct.pack('<I', a) for a in args))
        mu.mem_write(esp + 4 + 4 * len(args), struct.pack('<IIII', 0, 0, 0, above))
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.reg_write(UC_X86_REG_EBX, 0xB0B0)
        mu.reg_write(UC_X86_REG_EBP, 0xB1B1)
        mu.emu_start(base + rva + entry, retaddr, count=100000)
        # the prologue re-done and the epilogue run: ebx and ebp as they were, the stack at the return
        # the prologue re-done and the epilogue run: ebx and ebp as they were, the stack at the return
        if mu.reg_read(UC_X86_REG_EBX) != 0xB0B0 or mu.reg_read(UC_X86_REG_EBP) != 0xB1B1 or mu.reg_read(UC_X86_REG_ESP) != esp + 4:
            raise SystemExit('widetest: a MGameGL entry re-did its prologue wrong')
        return struct.unpack('<5I', mu.mem_read(esp, 20))

    size(1920.0, 1080.0)
    mu.mem_write(RECTS, struct.pack('<4i', 0, 256, 640, 480))
    _, _, rect, cx, cy = call(0, 0x7715, RECTS, 320, 240)
    got = struct.unpack('<4i', mu.mem_read(rect, 16))
    if got != (0, 576, 1920, 1080) or (cx, cy) != (960, 540) or rect == RECTS:
        raise SystemExit('widetest: SetViewport gave %r %r' % (got, (cx, cy)))
    mu.mem_write(RECTS, struct.pack('<4i', 0, 0, 1920, 1080))
    _, _, rect, cx, cy = call(0, 0x7715, RECTS, 960, 540)
    if rect != RECTS or (cx, cy) != (960, 540):
        raise SystemExit('widetest: a full-size viewport changed')
    # the countdown's zoom: a 640x480 frame doubled about its centre, still 640x480 terms
    mu.mem_write(RECTS, struct.pack('<4i', -320, -240, 960, 720))
    _, _, rect, cx, cy = call(0, 0x7715, RECTS, 320, 240)
    got = struct.unpack('<4i', mu.mem_read(rect, 16))
    if got != (-960, -540, 2880, 1620) or (cx, cy) != (960, 540):
        raise SystemExit('widetest: a zoomed viewport gave %r %r' % (got, (cx, cy)))
    # a screen DLL's 640x480, direct or through the exe's wrapper: the whole picture like the exe's
    for where in ({'retaddr': 0x03b5550f}, {'above': 0x03b4a46f}):
        mu.mem_write(RECTS, struct.pack('<4i', 0, 0, 640, 480))
        _, _, rect, cx, cy = call(0, 0x7715, RECTS, 320, 240, **where)
        got = struct.unpack('<4i', mu.mem_read(rect, 16))
        if got != (0, 0, 1920, 1080) or (cx, cy) != (960, 540):
            raise SystemExit('widetest: a DLL\'s viewport gave %r %r' % (got, (cx, cy)))
    _, _, a, near, far = call(5, 0x7715, 15360, 0x3f000000, 0x43700000)
    want = angle(84.375 * math.pi / 180, 1920, 1080)
    if abs(a - want) > 1 or (near, far) != (0x3f000000, 0x43700000):
        raise SystemExit('widetest: SetPerspective gave %d, expected %d' % (a, want))
    size(1600.0, 1200.0)
    _, _, a, _, _ = call(5, 0x7715, 15360, 0x3f000000, 0x43700000)
    if a != 15360:
        raise SystemExit('widetest: SetPerspective changed a 4:3 angle')
    size(640.0, 480.0)
    mu.mem_write(RECTS, struct.pack('<4i', 0, 0, 640, 480))
    _, _, rect, cx, cy = call(0, 0x7715, RECTS, 320, 240)
    if rect != RECTS or (cx, cy) != (320, 240):
        raise SystemExit('widetest: a viewport changed at 640x480')
    if not found['d3d']:
        raise SystemExit('widetest: MGameD3D never looked for')
    # the trace: the flag set as gltrace sets it, kernel32 stubbed
    at = blob.find(b'GLTRACE\0') + 8
    mu.mem_write(base + rva + at, struct.pack('<I', 1))
    mu.mem_write(STUBS, b'\xc2\x04\x00' + b'\x90' * 13 + b'\xc2\x08\x00' + b'\x90' * 13 + b'\xc2\x04\x00')
    mu.mem_write(base + 0x100ec, struct.pack('<I', STUBS))
    mu.mem_write(base + 0x10088, struct.pack('<I', STUBS + 0x10))
    lines = []

    def stub(mu, address, size_, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        arg = struct.unpack('<I', mu.mem_read(esp + 4, 4))[0]
        if address == STUBS + 0x20:
            lines.append(bytes(mu.mem_read(arg, 128)).split(b'\0')[0].decode())
        mu.reg_write(UC_X86_REG_EAX, STUBS + 0x20 if address == STUBS + 0x10 else 0x1234)
    mu.hook_add(UC_HOOK_CODE, stub, begin=STUBS, end=STUBS + 0x30)
    size(1920.0, 1080.0)
    mu.mem_write(base + 0x128d4, struct.pack('<ff', 480.0, 640.0))    # MGameGL's own, stale, as traced
    mu.mem_write(RECTS, struct.pack('<4i', 0, 0, 640, 480))
    call(0, 0x7715, RECTS, 320, 240)
    call(5, 0x7715, 15360, 0x3f000000, 0x43700000)
    if lines != ['sr2 vp 00000000 00000000 00000280 000001e0 00000140 000000f0 0046c04f 00421819 ',
                 'sr2 vp> 00000000 00000000 00000780 00000438 000003c0 0000021c ',
                 'sr2 fov 00003c00 44f00000 44870000 %08x ' % want]:
        raise SystemExit('widetest: the trace said %r' % (lines,))


def test_exe():
    mu, call, state = exe_stub()
    mode = ROW['addresses']['MODE']
    # the mode check: no file, no wide size, mode 0 equal to MODE 0
    call(0, 0, 0xCAFE0000, 0)                           # the pushed esi, the setter's return, the mode
    if not mu.reg_read(UC_X86_REG_EFLAGS) & ZF:
        raise SystemExit('widetest: a re-init asked for with no wide size')
    state['answer'] = b'1920x1080'
    call(0, 0, 0xCAFE0000, 0)
    if mu.reg_read(UC_X86_REG_EFLAGS) & ZF:
        raise SystemExit('widetest: no re-init asked for with a new wide size')
    call(5, eax=0)                                      # setsize for mode 0
    if size(mu) != (1920, 1080):
        raise SystemExit('widetest: the wide size not applied: %r' % (size(mu),))
    call(0, 0, 0xCAFE0000, 0)
    if not mu.reg_read(UC_X86_REG_EFLAGS) & ZF:
        raise SystemExit('widetest: a re-init asked for with the wide size in force')
    mu.mem_write(mode, struct.pack('<I', 1))
    call(0, 0, 0xCAFE0000, 1)
    if not mu.reg_read(UC_X86_REG_EFLAGS) & ZF:
        raise SystemExit('widetest: a re-init asked for with mode 1 unchanged')
    # mode 1 keeps 800x600 and clears the wide size; a stock or odd size in the file counts for nothing
    call(5, eax=1)
    if size(mu) != (800, 600):
        raise SystemExit('widetest: mode 1 not 800x600: %r' % (size(mu),))
    for answer in (b'800x600', b'1234x999', b'', b'1920'):
        state['answer'] = answer
        mu.mem_write(mode, struct.pack('<I', 0))
        call(0, 0, 0xCAFE0000, 0)
        call(5, eax=0)
        if size(mu) != (640, 480):
            raise SystemExit('widetest: %r taken as a wide size' % answer)
    # the screen change: the setter with the front end's mode once the file's size differs from the one in force
    settings, setter = ROW['addresses']['SETTINGS'], ROW['addresses']['SETTER']
    mu.mem_map(setter & ~0xfff, 0x1000)
    mu.mem_write(setter, b'\xc3')
    mu.mem_write(settings, struct.pack('<I', RECTS + 0x100))
    mu.mem_write(RECTS + 0x150, struct.pack('<I', 1))
    calls = []

    def setter_stub(mu, address, size_, user):
        calls.append(struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4, 4))[0])
    mu.hook_add(UC_HOOK_CODE, setter_stub, begin=setter, end=setter + 1)

    def screen(answer):
        state['answer'] = answer
        mu.reg_write(UC_X86_REG_EBX, 0xB0B0B0B0)
        mu.reg_write(UC_X86_REG_EBP, 0xB1B1B1B1)
        call(10)
        if (mu.reg_read(UC_X86_REG_EAX), mu.reg_read(UC_X86_REG_ECX), mu.reg_read(UC_X86_REG_EBX), mu.reg_read(UC_X86_REG_EBP),
                mu.reg_read(UC_X86_REG_ESP)) != (RECTS + 0x100, 1, 0xB0B0B0B0, 0xB1B1B1B1, STACK + 0x8004):
            raise SystemExit('widetest: the screen entry resumed wrong')
    screen(b'640x480')
    screen(b'1920x1080')
    screen(b'1920x1080')
    if calls != [1, 1]:
        raise SystemExit('widetest: the screen entry called the setter %r' % (calls,))
    call(5, eax=0)                                      # the setter applies it
    screen(b'1920x1080')
    screen(b'2560x1440')
    if calls != [1, 1, 1]:
        raise SystemExit('widetest: the screen entry called the setter %r' % (calls,))


VERTEX = '<4f2I2f'


def test_2d():
    base, rva = 0x10000000, 0x20000
    blob = patcher.WIDE2D_BLOB.replace(struct.pack('<I', patcher.FULLWIN_MAGIC), struct.pack('<I', rva))
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(base, 0x40000)                       # the blob's 64 KB copy fits
    mu.mem_map(STACK, 0x10000)
    mu.mem_map(VERTS, 0x20000)
    mu.mem_write(base + rva, blob)
    for site, length in zip(patcher.WIDE2D_SITES, (6, 6, 10, 10, 10, 10, 9, 8)):
        mu.mem_write(base + site + length, b'\xc3')     # the draw resumes: return to the test
    mu.mem_write(base + 0x4d58, b'\x83\xc4\x10\xc3')   # the present resumes: add esp, 0x10; ret
    mu.mem_write(base + 0x1240c, struct.pack('<I', 0xF0F0F0F0))
    mu.mem_write(base + 0x11220, struct.pack('<I', 0x18))
    mu.mem_write(base + 0x12764, struct.pack('<I', 0xD3D3D3D3))
    device, vtable = VERTS + 0x10000, VERTS + 0x10100          # the draw's `this`, with a stubbed +0xf8
    mu.mem_write(device, struct.pack('<I', vtable))
    mu.mem_write(vtable + 0xf8, struct.pack('<I', VERTS + 0x10200))
    mu.mem_write(VERTS + 0x10200, b'\xc2\x08\x00')
    wraps = []

    def setwrap(mu, address, size_, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        wraps.append(struct.unpack('<II', mu.mem_read(esp + 4, 8)))
    mu.hook_add(UC_HOOK_CODE, setwrap, begin=VERTS + 0x10200, end=VERTS + 0x10203)

    def draw(entry, verts, fvf=0x1c4, w=1920, h=1080, uv=None):
        mu.mem_write(base + 0x1121c, struct.pack('<I', fvf))
        mu.mem_write(base + 0x123fc, struct.pack('<II', w, h))
        uv = uv or [(0.0, 0.0)] * len(verts)
        data = b''.join(struct.pack(VERTEX, x, y, 0.5, 1.0, 0xffffffff, 0, u, v) for (x, y), (u, v) in zip(verts, uv))
        mu.mem_write(VERTS, data)
        esp = STACK + 0x8000
        # the return, `this`, the vertices, a list's count (an indexed list's vertex count), its indices and index count
        mu.mem_write(esp, struct.pack('<IIIIII', 0xDEAD0000, device, VERTS, len(verts), 0x1D1D0000, 0x99))
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.emu_start(base + rva + entry, 0xDEAD0000, count=1000000)
        if entry in (10, 15, 20, 25):
            resumed = (mu.reg_read(UC_X86_REG_EAX), mu.reg_read(UC_X86_REG_ECX)) == (len(verts) if entry != 15 else 0x99, 0xD3D3D3D3)
        else:
            resumed = mu.reg_read(UC_X86_REG_EDX) == 0x18
        if (not resumed or mu.reg_read(UC_X86_REG_ESP) != esp + 4
                or struct.unpack('<I', mu.mem_read(esp + 4, 4))[0] != device):
            raise SystemExit('widetest: the 2D draw resumed wrong')
        at = struct.unpack('<I', mu.mem_read(esp + 8, 4))[0]
        out = mu.mem_read(at, len(data))
        return at != VERTS, [(lambda v: (v[0], v[1], v[6]))(struct.unpack(VERTEX, out[i:i + 32])) for i in range(0, len(out), 32)]

    def present():
        """The present's entry: the frame's widths become last frame's."""
        esp = STACK + 0x8000
        mu.mem_write(esp, struct.pack('<II', 0xDEAD0000, device))
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.emu_start(base + rva + 35, 0xDEAD0000, count=100000)
        if mu.reg_read(UC_X86_REG_EAX) != 0xF0F0F0F0 or mu.reg_read(UC_X86_REG_ESP) != esp + 4:
            raise SystemExit('widetest: the present resumed wrong')

    def grid(w, h, cols, rows, x0=0.0, y0=0.0):
        """cols by rows quads of w by h from (x0, y0), as a background draws its tiles."""
        for r in range(rows):
            for c in range(cols):
                x, y = x0 + c * w, y0 + r * h
                draw(0, [(x, y), (x + w, y), (x, y + h), (x + w, y + h)], uv=[(0, 0), (1, 0), (0, 1), (1, 1)])

    quad = [(100.0, 100.0), (200.0, 100.0), (100.0, 200.0), (200.0, 200.0)]
    copied, got = draw(0, quad)
    want = [(x * 2.25 + 240, y * 2.25) for x, y in quad]
    if not copied or any(abs(a - b) > 0.01 for p, q in zip(got, want) for a, b in zip(p[:2], q)):
        raise SystemExit('widetest: a quad came out %r' % (got,))
    copied, got = draw(0, [(0.0, 0.0), (640.0, 0.0), (0.0, 480.0), (640.0, 480.0)])
    if not copied or [p[:2] for p in got] != [(0.0, 0.0), (1920.0, 0.0), (0.0, 1080.0), (1920.0, 1080.0)]:
        raise SystemExit('widetest: a full-width quad came out %r' % (got,))
    # a tile at the edge extends only once its width tiled the whole frame the frame before: a sprite of 128 at the
    # edge with no such frame behind it keeps its place, as does one after a frame of four such quads, or of a row
    edge = [(-40.0, 0.0), (88.0, 0.0), (-40.0, 128.0), (88.0, 128.0)]
    mu.mem_write(base + 0x11240, struct.pack('<I', 0))
    present()
    copied, got = draw(0, edge, uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if [p[:2] for p in got] != [(150.0, 0.0), (438.0, 0.0), (150.0, 288.0), (438.0, 288.0)]:
        raise SystemExit('widetest: a lone edge quad extended: %r' % (got,))
    grid(128, 128, 2, 2)
    present()
    copied, got = draw(0, edge, uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if [p[:2] for p in got] != [(150.0, 0.0), (438.0, 0.0), (150.0, 288.0), (438.0, 288.0)]:
        raise SystemExit('widetest: an edge quad extended after four of its width: %r' % (got,))
    grid(128, 128, 5, 1, y0=100.0)
    present()
    copied, got = draw(0, edge, uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if [p[:2] for p in got] != [(150.0, 0.0), (438.0, 0.0), (150.0, 288.0), (438.0, 288.0)]:
        raise SystemExit('widetest: an edge quad extended after a row of its width: %r' % (got,))
    # a frame tiled 5 by 4 with them (the last row past the bottom, as a grid falls), scrolled 40 px left
    grid(128, 128, 6, 4, x0=-40.0)
    present()
    # a clamped tile at the left edge, 128 wide, u 0..1: out to the edge, u shifted by 240 / (128 * 2.25), wrap switched on
    copied, got = draw(0, edge, uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    # scrolled 40 px off the left edge first: its left vertex moves 240 - 40 * 2.25 picture pixels, the shift follows that
    tile = [(0.0, 0.0, -(240 / 2.25 - 40) / 128), (438.0, 0.0, 1.0), (0.0, 288.0, -(240 / 2.25 - 40) / 128), (438.0, 288.0, 1.0)]
    if not copied or any(abs(a - b) > 0.001 for p, q in zip(got, tile) for a, b in zip(p, q)):
        raise SystemExit('widetest: a scrolled edge tile came out %r' % (got,))
    # the widths seen this frame count only from the next present: a 64-wide sprite at the edge stays where it is
    copied, got = draw(0, [(-20.0, 200.0), (44.0, 200.0), (-20.0, 264.0), (44.0, 264.0)], uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if [p[:2] for p in got] != [(195.0, 450.0), (339.0, 450.0), (195.0, 594.0), (339.0, 594.0)]:
        raise SystemExit('widetest: a sprite at the edge extended: %r' % (got,))
    grid(128, 128, 5, 4)
    present()
    del wraps[:]
    copied, got = draw(0, [(0.0, 0.0), (128.0, 0.0), (0.0, 128.0), (128.0, 128.0)], uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if wraps != [(device, 1)]:
        raise SystemExit('widetest: wrap not switched on for a clamped tile: %r' % (wraps,))
    shift = 240 / (128 * 2.25)
    tile = [(0.0, 0.0, -shift), (528.0, 0.0, 1.0), (0.0, 288.0, -shift), (528.0, 288.0, 1.0)]
    if not copied or any(abs(a - b) > 0.001 for p, q in zip(got, tile) for a, b in zip(p, q)):
        raise SystemExit('widetest: an edge tile came out %r' % (got,))
    copied, got = draw(0, [(512.0, 0.0), (640.0, 0.0), (512.0, 128.0), (640.0, 128.0)], uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    tile = [(1392.0, 0.0, 0.0), (1920.0, 0.0, 1.0 + shift), (1392.0, 288.0, 0.0), (1920.0, 288.0, 1.0 + shift)]
    if not copied or any(abs(a - b) > 0.001 for p, q in zip(got, tile) for a, b in zip(p, q)):
        raise SystemExit('widetest: a right-edge tile came out %r' % (got,))
    # a strip of a picture at the right edge, tile-wide but tall, keeps its place
    copied, got = draw(0, [(512.0, 0.0), (640.0, 0.0), (512.0, 480.0), (640.0, 480.0)], uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if [p[:2] for p in got] != [(1392.0, 0.0), (1680.0, 0.0), (1392.0, 1080.0), (1680.0, 1080.0)]:
        raise SystemExit('widetest: a picture strip came out %r' % (got,))
    # a clamped quad wider than a tile at the left edge - a picture - keeps its place; wrapping, it extends
    photo = [(0.0, 0.0), (320.0, 0.0), (0.0, 480.0), (320.0, 480.0)]
    del wraps[:]
    copied, got = draw(0, photo, uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if wraps or [p[:2] for p in got] != [(240.0, 0.0), (960.0, 0.0), (240.0, 1080.0), (960.0, 1080.0)]:
        raise SystemExit('widetest: a clamped picture came out %r' % (got,))
    mu.mem_write(base + 0x11240, struct.pack('<I', 1))
    copied, got = draw(0, photo, uv=[(0, 0), (1, 0), (0, 1), (1, 1)])
    if wraps or [p[:2] for p in got] != [(240.0, 0.0), (960.0, 0.0), (240.0, 1080.0), (960.0, 1080.0)]:
        raise SystemExit('widetest: a wrapping picture came out %r' % (got,))
    mu.mem_write(base + 0x11240, struct.pack('<I', 0))
    copied, got = draw(5, quad[:3])
    if not copied or any(abs(a - b) > 0.01 for p, q in zip(got, want[:3]) for a, b in zip(p[:2], q)):
        raise SystemExit('widetest: a triangle came out %r' % (got,))
    if draw(0, quad, w=640, h=480)[0] or draw(0, quad, fvf=0x1e2)[0]:
        raise SystemExit('widetest: a quad copied that should have gone as it was')
    text = [(x, y) for i in range(20) for x, y in ((10.0 + i * 8, 20.0), (18.0 + i * 8, 20.0), (10.0 + i * 8, 28.0))]
    copied, got = draw(10, text)
    if not copied or any(abs(a - b) > 0.01 for p, (x, y) in zip(got, text) for a, b in zip(p[:2], (x * 2.25 + 240, y * 2.25))):
        raise SystemExit('widetest: a list came out %r' % (got[:3],))
    if draw(10, [(1.0, 1.0)] * 2049)[0]:
        raise SystemExit('widetest: an oversized list copied')
    # the trace: the flag set as d3dtrace sets it, kernel32 stubbed; a quad and a list report
    mu.mem_write(base + rva + blob.find(b'D3DTRACE\0') + 9, struct.pack('<I', 1))
    mu.mem_map(STUBS, 0x1000)
    mu.mem_write(STUBS, b'\xc2\x04\x00' + b'\x90' * 13 + b'\xc2\x08\x00' + b'\x90' * 13 + b'\xc2\x04\x00')
    mu.mem_write(base + 0xf114, struct.pack('<I', STUBS))
    mu.mem_write(base + 0xf0ac, struct.pack('<I', STUBS + 0x10))
    lines = []

    def stub(mu, address, size_, user):
        esp = mu.reg_read(UC_X86_REG_ESP)
        arg = struct.unpack('<I', mu.mem_read(esp + 4, 4))[0]
        if address == STUBS + 0x20:
            lines.append(bytes(mu.mem_read(arg, 128)).split(b'\0')[0].decode())
        mu.reg_write(UC_X86_REG_EAX, STUBS + 0x20 if address == STUBS + 0x10 else 0x1234)
    mu.hook_add(UC_HOOK_CODE, stub, begin=STUBS, end=STUBS + 0x30)
    draw(0, [(10.0, 20.0), (50.0, 20.0), (10.0, 60.0), (50.0, 60.0)], fvf=0x1e2)
    draw(10, text[:6])
    if lines != ['sr2 d q 000001e2 00000004 dead0000 41200000 41a00000 3f000000 ',
                 'sr2 d l 000001c4 00000006 dead0000 41200000 41a00000 3f000000 ']:
        raise SystemExit('widetest: the trace said %r' % (lines,))
    copied, got = draw(15, text)
    if not copied or any(abs(a - b) > 0.01 for p, (x, y) in zip(got, text) for a, b in zip(p[:2], (x * 2.25 + 240, y * 2.25))):
        raise SystemExit('widetest: an indexed list came out %r' % (got[:3],))
    # the countdown: a 640x480-terms strip; and a fan
    digit = [(170.0, 40.0), (470.0, 40.0), (170.0, 440.0), (470.0, 440.0)]
    for entry in (20, 25):
        copied, got = draw(entry, digit)
        if not copied or any(abs(a - b) > 0.01 for p, (x, y) in zip(got, digit) for a, b in zip(p[:2], (x * 2.25 + 240, y * 2.25))):
            raise SystemExit('widetest: a strip or fan came out %r' % (got,))
    if draw(20, digit, fvf=0x1e2)[0]:
        raise SystemExit('widetest: a 3D strip copied')
    # the device's viewport setter: the exe's 640x480 and a split half scaled, MGameGL's real one and a 640x480 picture's alone
    mu.mem_write(base + 0x6049, b'\x5f\x5e\x83\xc4\x08\xc2\x08\x00')     # the setter resumes: pop edi; pop esi; add esp,8; ret 8

    where = VERTS + 0x11000

    def setvp(rect, w=1920, h=1080):
        mu.mem_write(base + 0x123fc, struct.pack('<II', w, h))
        mu.mem_write(where, struct.pack('<4i4f', *rect, 0.5, 0.5, 1.0, 1.0))
        esp = STACK + 0x8000
        mu.mem_write(esp, struct.pack('<III', 0xDEAD0000, 0x7715, where))
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.emu_start(base + rva + 30, 0xDEAD0000, count=100000)
        at = struct.unpack('<I', mu.mem_read(esp + 8, 4))[0]
        return at != where, struct.unpack('<4i4f', mu.mem_read(at, 32))
    if setvp((0, 0, 640, 480)) != (True, (0, 0, 1920, 1080, 0.5, 0.5, 1.0, 1.0)):
        raise SystemExit('widetest: the device viewport for 640x480 came out %r' % (setvp((0, 0, 640, 480)),))
    if setvp((0, 240, 640, 480)) != (True, (0, 540, 1920, 1080, 0.5, 0.5, 1.0, 1.0)):
        raise SystemExit('widetest: the device viewport for a split half came out %r' % (setvp((0, 240, 640, 480)),))
    if setvp((0, 0, 1920, 1080))[0] or setvp((0, 0, 640, 480), w=640, h=480)[0]:
        raise SystemExit('widetest: a device viewport scaled that should have passed')


def main():
    test_exe()
    test_gl()
    test_2d()
    print('widetest: the size stubs, the viewport and perspective hooks and the 2D scaling OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())

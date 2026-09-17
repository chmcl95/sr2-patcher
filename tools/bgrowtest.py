#!/usr/bin/env python3
"""Run the .bg copies of the windowed and title patches under Unicorn.

    python3 tools/bgrowtest.py

BGROW_BLOB and TITLEROW_BLOB are called with the rows of a small 565
picture as the game calls the copies they replace: eax the row's byte
count, ebx the source row, edx the destination row, the lock description
at its place (the exe's global, Title.dll's stack) and the picture's
height where each loop keeps it. With the surface the picture's size a
16-bit row must come out byte for byte, a 32-bit one as XRGB8888 with the
low bits replicated. With a larger surface the whole picture must land on
the first row, scaled to fit with its aspect kept and centred on black,
and the rows after must touch nothing, with a bar each side: in
Title.dll's build the picture's own sliver beyond the drawn edge, blurred
across and stretched over it; in the exe's the row's edge pixel. eax and edx must survive, and ebx
too for the exe's, advanced by a row for Title.dll's. Needs
python3-unicorn; exits 0 with a note when it is missing.
"""
import importlib.util
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('patcher', os.path.join(HERE, '..', 'sr2-patcher.py'))
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

try:
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EDX,
                                   UC_X86_REG_ESP)
except ImportError:
    print('bgrowtest: skipped, python3-unicorn not installed')
    sys.exit(0)

CODE, DESC, SRC, DST, STACK, OBJ = 0x400000, 0x4e6000, 0x1000000, 0x1008000, 0x3000000, 0x2000000
LOCKDESC = patcher.BUILDS['European']['addresses']['LOCKDESC']
PIXELS = (0x0000, 0xffff, 0xf800, 0x07e0, 0x001f, 0x8410, 0x1234, 0x4321)   # a 4x2 picture
SRC_W, SRC_H = 4, 2


BIG_W, BIG_H = 64, 32                           # a picture wide enough for its stretch to show columns
DIM = 0x66                                      # the bars' brightness against the picture's


def big_picture():
    """A picture whose columns differ, so the stretch of it shows them."""
    return [((x >> 1) & 31) << 11 | ((y >> 1) & 63) << 5 | ((x + y) & 31) for y in range(BIG_H) for x in range(BIG_W)]


def blurred(row, src_w, first, last, dim):
    """A sliver of a row box-blurred as bgrow does it: each column the
    mean, channel by channel, of the columns a sixty-fourth of the width
    either side of it that the sliver has, dimmed."""
    reach = max(src_w >> 6, 1)
    out = [None] * src_w
    for c in range(first, last + 1):
        box = row[max(c - reach, first):min(c + reach, last) + 1]
        r = (sum(p >> 11 for p in box) // len(box)) * dim >> 8
        g = (sum((p >> 5) & 63 for p in box) // len(box)) * dim >> 8
        b = (sum(p & 31 for p in box) // len(box)) * dim >> 8
        out[c] = r << 11 | g << 5 | b
    return out


def stretched(pixels, src_w, src_h, dst_w, drawn_w, drawn_h, dst_h, title):
    """The bars as bgrow draws them: the whole picture stretched to the
    surface's width, nearest pixel, the drawn one covering the middle;
    rows above and below the picture take its first and last. In
    Title.dll's build each sliver is blurred across within itself and
    dimmed; in the exe's each bar is the row's own edge pixel throughout."""
    bar = (dst_w - drawn_w) // 2
    top = (dst_h - drawn_h) // 2
    ystep, xstep = (src_h << 16) // drawn_h, (src_w << 16) // dst_w
    lfirst, llast = 0, ((bar * xstep) >> 16)
    rfirst, rlast = ((bar + drawn_w) * xstep) >> 16, src_w - 1
    rows = [pixels[y * src_w:(y + 1) * src_w] for y in range(src_h)]
    out = []
    for y in range(dst_h):
        row = min(max(y - top, 0) * ystep >> 16, src_h - 1) if y >= top else 0
        if y >= top + drawn_h:
            row = min(((drawn_h - 1) * ystep) >> 16, src_h - 1)
        if title:
            soft = blurred(rows[row], src_w, lfirst, llast, DIM)
            soft = [a if a is not None else b for a, b in zip(soft, blurred(rows[row], src_w, rfirst, rlast, DIM))]
            line = [soft[(x * xstep) >> 16] for x in range(dst_w)]
            out.append((line[:bar], line[bar + drawn_w:]))
        else:
            out.append(([rows[row][0]] * bar, [rows[row][-1]] * (dst_w - bar - drawn_w)))
    return out


def expand(p):
    r, g, b = (p >> 11) & 0x1f, (p >> 5) & 0x3f, p & 0x1f
    return ((r << 3 | r >> 2) << 16) | ((g << 2 | g >> 4) << 8) | (b << 3 | b >> 2)


def run(bpp, title, dst_w, dst_h, pixels=None, src_w=None, src_h=None):
    """The rows of the picture copied into a dst_w x dst_h surface of the
    given depth: the surface's pixels, row by row, and the register check."""
    pixels = PIXELS if pixels is None else pixels
    src_w = SRC_W if src_w is None else src_w
    src_h = SRC_H if src_h is None else src_h
    blob = patcher.TITLEROW_BLOB if title else patcher.exe_blob(patcher.BGROW_BLOB, 'European')
    src = b''.join(p.to_bytes(2, 'little') for p in pixels)
    width = 4 if bpp == 32 else 2
    pitch = dst_w * width + 16
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    for addr in (CODE, DESC, OBJ):
        mu.mem_map(addr, 0x1000)
    mu.mem_map(SRC, 0x20000)                    # the destination sits inside this one too
    mu.mem_map(STACK, 0x10000)
    mu.mem_write(CODE, blob)
    mu.mem_write(SRC, src)
    mu.mem_write(DST, b'\xaa' * (pitch * dst_h))
    desc = bytearray(0x7c)
    struct.pack_into('<III', desc, 8, dst_h, dst_w, pitch)
    struct.pack_into('<I', desc, 0x24, DST)
    struct.pack_into('<I', desc, 0x54, bpp)
    end = CODE + len(blob)
    esp = STACK + 0x8000
    mu.mem_write(esp, end.to_bytes(4, 'little'))
    if title:
        mu.mem_write(esp + 0x1c, bytes(desc))
    else:
        mu.mem_write(LOCKDESC, bytes(desc))
        mu.mem_write(OBJ, struct.pack('<II', 0, OBJ + 0x100))    # the loop's object: +4 the picture
        mu.mem_write(OBJ + 0x100, struct.pack('<III', 0, src_w, src_h))
        mu.mem_write(esp + 4 + 0x18, OBJ.to_bytes(4, 'little'))
    row_bytes = src_w * 2
    for row in range(src_h):
        if title:
            mu.mem_write(esp + 4 + 0x10, (src_h - row).to_bytes(4, 'little'))     # rows still to copy
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.reg_write(UC_X86_REG_EAX, row_bytes)
        mu.reg_write(UC_X86_REG_EBX, SRC + row * row_bytes)
        mu.reg_write(UC_X86_REG_EDX, DST + row * pitch)
        mu.emu_start(CODE, end)
        regs = tuple(mu.reg_read(r) for r in (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EDX))
        want = (row_bytes, SRC + row * row_bytes + (row_bytes if title else 0), DST + row * pitch)
        if regs != want:
            raise SystemExit('bgrowtest: registers wrong at %d bpp%s, row %d: %r'
                             % (bpp, ', title' if title else '', row, regs))
    out = bytes(mu.mem_read(DST, pitch * dst_h))
    return [[int.from_bytes(out[y * pitch + x * width:y * pitch + (x + 1) * width], 'little')
             for x in range(dst_w)] for y in range(dst_h)]


def main():
    picture = [list(PIXELS[:4]), list(PIXELS[4:])]
    for title in (False, True):
        where = 'Title.dll' if title else 'the exe'
        if run(16, title, SRC_W, SRC_H) != picture:
            raise SystemExit('bgrowtest: 16-bit rows not copied as is, %s' % where)
        got = run(32, title, SRC_W, SRC_H)
        if got != [[expand(p) for p in row] for row in picture]:
            raise SystemExit('bgrowtest: 32-bit rows wrong, %s: %r' % (where, got))
        # twice the size: each source pixel becomes 2x2, the bars the picture's own ends stretched over them
        got = run(16, title, 12, 4)
        bars = stretched(PIXELS, SRC_W, SRC_H, 12, 8, 4, 4, title)
        want = [bars[y][0] + [p for p in picture[y // 2] for _ in range(2)] + bars[y][1] for y in range(4)]
        if got != want:
            raise SystemExit('bgrowtest: scaled 16-bit picture wrong, %s: %r' % (where, got))
        # a wider picture, stretched five times: the bars are the picture's own columns, nearest, and not one colour
        big = big_picture()
        got = run(16, title, 320, 32, big, BIG_W, BIG_H)
        bars = stretched(big, BIG_W, BIG_H, 320, 64, 32, 32, title)
        bar = (320 - 64) // 2
        if any((row[:bar], row[bar + 64:]) != bars[y] for y, row in enumerate(got)):
            raise SystemExit('bgrowtest: the stretched bars wrong, %s: %r' % (where, got[0][:bar]))
        if title and len(set(got[0][:bar])) < 4:
            raise SystemExit('bgrowtest: the bar did not carry the picture across, %s: %r' % (where, got[0][:bar]))
        got = run(32, title, 8, 6)     # letterboxed: a row of black above and below
        want = ([[0] * 8] + [[expand(p) for p in row for _ in range(2)] for row in picture for _ in range(2)]
                + [[0] * 8])
        if got != want:
            raise SystemExit('bgrowtest: scaled 32-bit picture wrong, %s: %r' % (where, got))
    print('bgrow: 16-bit copy, 32-bit expand and the scaled picture OK, exe and Title.dll')
    return 0


if __name__ == '__main__':
    sys.exit(main())

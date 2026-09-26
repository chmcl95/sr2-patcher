#!/usr/bin/env python3
"""Give the hidden car ids 18, 26 and 29 cars of their own.

    python3 tools/carslot.py GAME carslot.json     # apply a slot file
    python3 tools/carslot.py GAME --spec ID [OUT]  # a car's spec block as JSON
    python3 tools/carslot.py GAME --restore        # every file back

The three ids (CARISMA, PGT2051, FOCUS) are in every per-car table and
have no folder; each copies another car in most of them (docs/CARS.md).
A slot file names, per id, what the id gets instead:

    {"18": {"perf": 17,                      # spec, curve, engine, rev counter, gearboxes of car 17
            "spec": "carisma.json",          # the spec block from a --spec file, over perf's
            "sound": 17, "meter": 17,        # engine wavs and rev counter, over perf's
            "gearbox": [0, 1, 4, 5],         # 0/1 4-speed AT/MT, 2/3 5, 4/5 6, 6/7 7
            "name": "CARISMA GT",            # results, replay gallery
            "photo": "photo.png",            # car select, 256x128
            "logo": "logo.png",              # car select, 256x64
            "icon": "icon.png",              # records, rankings, replay gallery, 58x20
            "icon_small": "icon_s.png",      # records, 42x14
            "profile": "profile.png",        # the spec card, 256x256, CAR\\carproNN.txr
            "model": true}}                  # the car select's 3D car from the id's folder

Every key is optional; an id in the file is offered on the car select.
Paths are relative to the slot file. The car's own models, textures and
wavs go in its folder under BINDATA as for any car; the engine wavs keep
the names of the car `sound` (or `perf`) names.

Run it after sr2-patcher: each file it touches is kept as <file>.carslot
and every run starts from that, so running twice is running once and a
slot left out goes back. After the patcher has written a file again, the
next run takes the patcher's file as its start. The European and
MediaKite builds only, whose data addresses are the same.
"""
import hashlib
import importlib.util
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('patcher', os.path.join(HERE, '..', 'sr2-patcher.py'))
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

SLOTS = {18: 'CARISMA', 26: 'PGT2051', 29: 'FOCUS'}
CARS = 30
STATE = 'carslot.state'
DATA_SECTION = 0xc0000040               # initialised data, read, write

EXE = 'SEGA RALLY 2.exe'
SPEC, SPEC_SIZE = 0x495a98, 0x2a8       # 0xaa dwords, copied into the car at +0xac
CURVE = 0x4a9d60
NAME = 0x4af704
SOUND = 0x4b5d94
METER = 0x4b6aa8
HUD = (0x4b0cec, 0x4b0d64)
PROFILE = 0x49585c
FOLDERS = 0x4cef48

MSELECT = 'MSelect.dll'
MENU = 0x100b5970                       # {mask, id} x 30
PHOTO = (0x100b513c, 0x100b5880)
LOGO = 0x100b58f8
GEARBOX = 0x100b70a0                    # 4 dwords a car
CARMDL, CARTEX = 0x100b95a0, 0x100b9690 # {offset, size} into the two BINs

RECORD = 'Record.dll'
RECORD_ICONS = (0x1009fd28, 0x1009fda0) # 58x20, 42x14
REPLAY = 'ReplayGallery.dll'
REPLAY_ICON, REPLAY_NAME = 0x1009c8e0, 0x1009c958
CHAMPAGN = 'Champagn.dll'
CHAMPAGN_PROFILE = 0x1001c110

MISC = 'BINDATA\\MISC\\'
MS_CAR = MISC + 'MS_CAR.TXR'            # photos, two a page, pages 0x20-0x2f
M_CNAME = MISC + 'M_CNAME.TXR'          # logos, four a page, pages 0x30-0x3f
RECORD_TXRS = tuple(MISC + n for n in ('Record.txr', 'Rank10.txr', 'RankAC.txr', 'RankTA.txr'))
REPLAY_TXRS = tuple(MISC + n for n in ('RG_RG.txr', 'RG_AC.txr', 'RG_TA.txr', 'RG_10.txr'))
B_CARMDL, B_CARTEX = MISC + 'B_CARMDL.BIN', MISC + 'B_CARTEX.BIN'
PAGE_LIMIT = 16                         # MS_CAR and M_CNAME: the next archive loads 16 pages on

SIZES = {'photo': (256, 128), 'logo': (256, 64), 'icon': (58, 20), 'icon_small': (42, 14), 'profile': (256, 256)}
FILES = (EXE, MSELECT, RECORD, REPLAY, CHAMPAGN, MS_CAR, M_CNAME, B_CARMDL, B_CARTEX) + RECORD_TXRS + REPLAY_TXRS


def md5(data):
    return hashlib.md5(data).hexdigest()


class Image:
    """A PE file's bytes addressed by VA, growing an annex for new data."""

    def __init__(self, data):
        self.buf = bytearray(data)
        self.base = patcher._image_base(self.buf)
        self.relocs = []

    def off(self, va):
        return patcher._rva_to_off(self.buf, va - self.base)

    def u32(self, va):
        return struct.unpack_from('<I', self.buf, self.off(va))[0]

    def put(self, va, value):
        struct.pack_into('<I', self.buf, self.off(va), value & 0xffffffff)

    def read(self, va, n):
        return bytes(self.buf[self.off(va):self.off(va) + n])

    def write(self, va, data):
        self.buf[self.off(va):self.off(va) + len(data)] = data

    def cstr(self, va):
        data = self.read(va, 64)
        return data[:data.index(b'\0')].decode('latin-1')

    def add(self, data, pointers=()):
        """data in the annex; returns its VA. pointers: offsets in data of
        absolutes, which get relocation entries when the file has any."""
        self.buf, rva = patcher.append_section(self.buf, data, chars=DATA_SECTION)
        self.relocs += [rva + p for p in pointers]
        return self.base + rva

    def done(self):
        rel_size = struct.unpack_from('<I', self.buf, struct.unpack_from('<I', self.buf, 0x3c)[0] + 24 + 140)[0]
        if self.relocs and rel_size:
            patcher._add_relocations(self.buf, self.relocs)
        return bytes(self.buf)


# Textures

def txr_pages(data):
    if data[:4] != b'RTEX':
        raise ValueError('not a TXR')
    count = struct.unpack_from('<I', data, 4)[0]
    return [struct.unpack_from('<4I', data, 16 + 16 * i) for i in range(count)]


def txr_append(data, fmt, size, pixels):
    """The archive with one more square page; returns (data, its index)."""
    pages = txr_pages(data)
    index = len(pages)
    if 16 + 16 * (index + 1) > 0x1000:
        raise ValueError('no room in the TXR header')
    out = bytearray(data)
    struct.pack_into('<I', out, 4, index + 1)
    struct.pack_into('<4I', out, 16 + 16 * index, fmt, size, len(pixels), 0)
    return bytes(out) + pixels, index


def texels(img, fmt):
    """An RGBA image as 16-bit texels: 0 565, 2 1555, 8 4444."""
    out = bytearray()
    for r, g, b, a in img.getdata():
        if fmt == 0:
            v = (r >> 3) << 11 | (g >> 2) << 5 | b >> 3
        elif fmt == 2:
            v = (0x8000 if a >= 128 else 0) | (r >> 3) << 10 | (g >> 3) << 5 | b >> 3
        else:
            v = (a >> 4) << 12 | (r >> 4) << 8 | (g >> 4) << 4 | b >> 4
        out += struct.pack('<H', v)
    return bytes(out)


def open_png(path, what):
    try:
        from PIL import Image as PIL
    except ImportError:
        raise SystemExit('carslot: pictures need Pillow (pip install pillow)')
    img = PIL.open(path).convert('RGBA')
    if img.size != SIZES[what]:
        raise ValueError('%s: %s is %dx%d, not %dx%d' % (path, what, *img.size, *SIZES[what]))
    return img


def sheet(size, placed):
    """A transparent square page with (image, x, y) pasted."""
    from PIL import Image as PIL
    page = PIL.new('RGBA', (size, size), (0, 0, 0, 0))
    for img, x, y in placed:
        page.paste(img, (x, y))
    return page


# Sprites: a 0x58-byte record {uv table, parts, count, ...}; a part is
# 0x38 bytes {uv index, rect ...}; a uv entry 0x14 {page, u0, v0, u1, v1}.
# The page is the archive's own index. A new sprite copies a stock
# record and part and points them at a uv table of its own.

def sprite(img, donor, page, uv):
    record = bytearray(img.read(donor, 0x58))
    parts, count = struct.unpack_from('<II', record, 4)
    if count != 1:
        raise ValueError('sprite 0x%x has %d parts' % (donor, count))
    part = bytearray(img.read(parts, 0x38))
    struct.pack_into('<I', part, 0, 0)
    blob = struct.pack('<I4f', page, *uv) + bytes(12) + part + bytes(8)       # uv at 0, part at 0x20
    at = img.add(blob + bytes(0x60 - len(blob)))
    struct.pack_into('<II', record, 0, at, at + 0x20)
    return img.add(bytes(record), pointers=(0, 4))


def uv_of(x, y, w, h, size=256):
    return x / size, y / size, (x + w) / size, (y + h) / size


# The run

class Game:
    def __init__(self, dest):
        self.dest = dest
        path = os.path.join(dest, STATE)
        self.state = json.load(open(path)) if os.path.isfile(path) else {'files': {}, 'created': {}}
        self.data = {}

    def path(self, rel):
        return os.path.join(self.dest, *rel.split('\\'))

    def base(self, rel):
        """The file as carslot found it: its backup while the file is still
        what the last run wrote, else the file itself, the new start."""
        if rel not in self.data:
            path = self.path(rel)
            with open(path, 'rb') as fh:
                data = fh.read()
            bak = path + '.carslot'
            if os.path.isfile(bak) and self.state['files'].get(rel) == md5(data):
                with open(bak, 'rb') as fh:
                    data = fh.read()
            self.data[rel] = data
        return self.data[rel]

    def write(self, outputs, created, log):
        for rel in FILES:
            path = self.path(rel)
            if not os.path.isfile(path):
                continue
            base = self.base(rel)
            out = outputs.get(rel, base)
            bak = path + '.carslot'
            if out == base:
                with open(path, 'wb') as fh:
                    fh.write(base)
                if os.path.isfile(bak):
                    os.remove(bak)
                self.state['files'].pop(rel, None)
                continue
            with open(bak, 'wb') as fh:
                fh.write(base)
            with open(path, 'wb') as fh:
                fh.write(out)
            self.state['files'][rel] = md5(out)
            log('carslot: %s written' % rel)
        for rel, digest in list(self.state['created'].items()):
            path = self.path(rel)
            if os.path.isfile(path) and md5(open(path, 'rb').read()) == digest:
                os.remove(path)
            del self.state['created'][rel]
        for rel, data in created.items():
            with open(self.path(rel), 'wb') as fh:
                fh.write(data)
            self.state['created'][rel] = md5(data)
            log('carslot: %s written' % rel)
        with open(os.path.join(self.dest, STATE), 'w') as fh:
            json.dump(self.state, fh, indent=1)


def check(exe):
    for slot, folder in SLOTS.items():
        if exe.cstr(exe.u32(FOLDERS + 4 * slot)) != folder:
            raise ValueError('%s: not the European or MediaKite exe (folder %d is not %s)' % (EXE, slot, folder))


def spec_values(block):
    """A spec block as JSON values: a float where the dword reads as an
    ordinary float, else its hex."""
    out = []
    for (v,) in struct.iter_unpack('<I', block):
        f = struct.unpack('<f', struct.pack('<I', v))[0]
        e = v >> 23 & 0xff
        out.append(round(f, 7) if v == 0 or 0x60 <= e <= 0x9f else '0x%x' % v)
    return out


def spec_block(values):
    if len(values) != SPEC_SIZE // 4:
        raise ValueError('a spec has %d values, not %d' % (len(values), SPEC_SIZE // 4))
    return b''.join(struct.pack('<I', int(v, 0)) if isinstance(v, str) else struct.pack('<f', v) for v in values)


def apply(game, slots, here, log=print):
    exe = Image(game.base(EXE))
    check(exe)
    msel = Image(game.base(MSELECT))
    record = Image(game.base(RECORD))
    replay = Image(game.base(REPLAY))
    champagn = Image(game.base(CHAMPAGN))
    txr = {rel: game.base(rel) for rel in (MS_CAR, M_CNAME) + RECORD_TXRS + REPLAY_TXRS}
    carmdl, cartex = bytearray(game.base(B_CARMDL)), bytearray(game.base(B_CARTEX))
    created = {}
    pics = {what: [] for what in SIZES}

    for slot, conf in sorted(slots.items()):
        folder = SLOTS[slot]
        for i in range(CARS):                   # on the menu: the Corolla's bit, open from the start
            if msel.u32(MENU + 8 * i + 4) == slot:
                msel.put(MENU + 8 * i, 1)
        perf = conf.get('perf')
        if perf is not None:
            exe.write(SPEC + slot * SPEC_SIZE, exe.read(SPEC + perf * SPEC_SIZE, SPEC_SIZE))
            exe.put(CURVE + 4 * slot, exe.u32(CURVE + 4 * perf))
            for table in HUD:
                exe.put(table + 4 * slot, exe.u32(table + 4 * perf))
            msel.write(GEARBOX + 16 * slot, msel.read(GEARBOX + 16 * perf, 16))
        if 'spec' in conf:
            with open(os.path.join(here, conf['spec'])) as fh:
                exe.write(SPEC + slot * SPEC_SIZE, spec_block(json.load(fh)['values']))
        for key, table in (('sound', SOUND), ('meter', METER)):
            donor = conf.get(key, perf)
            if donor is not None:
                exe.put(table + 4 * slot, exe.u32(table + 4 * donor))
        if 'gearbox' in conf:
            msel.write(GEARBOX + 16 * slot, struct.pack('<4I', *conf['gearbox']))
        if 'name' in conf:
            text = conf['name'].encode('latin-1') + b'\0'
            exe.put(NAME + 4 * slot, exe.add(text))
            replay.put(REPLAY_NAME + 4 * slot, replay.add(text))
        for what in SIZES:
            if what in conf:
                pics[what].append((slot, open_png(os.path.join(here, conf[what]), what)))
        if conf.get('model'):
            name = folder.lower()
            src = game.path('BINDATA\\%s\\' % folder)
            with open(os.path.join(src, 'r_%s.mdl' % name), 'rb') as fh:
                mdl = fh.read()
            tex = []
            for fname, size in (('body.txr', 256), ('ta_tire.txr', 64)):
                with open(os.path.join(src, fname), 'rb') as fh:
                    data = fh.read()
                tex.append(data[0x1000:0x1000 + size * size * 2])
            head = bytearray(0x1000)
            head[:8] = b'RTEX' + struct.pack('<I', 2)
            struct.pack_into('<4I', head, 16, 0, 256, len(tex[0]), 0)
            struct.pack_into('<4I', head, 32, 0, 64, len(tex[1]), 0)
            carmdl += bytes(-len(carmdl) % 0x20)
            msel.write(CARMDL + 8 * slot, struct.pack('<II', len(carmdl), len(mdl)))
            carmdl += mdl
            cartex += bytes(-len(cartex) % 0x1000)
            blob = bytes(head) + tex[0] + tex[1]
            msel.write(CARTEX + 8 * slot, struct.pack('<II', len(cartex), len(blob)))
            cartex += blob

    # The photos, two a page, and the logos, four a page, on pages added to their archives.
    for what, rel, per, tables, fmt in (('photo', MS_CAR, 2, PHOTO, 2), ('logo', M_CNAME, 4, (LOGO,), 8)):
        items = pics[what]
        for first in range(0, len(items), per):
            group = items[first:first + per]
            h = SIZES[what][1]
            page = sheet(256, [(img, 0, h * i) for i, (_s, img) in enumerate(group)])
            txr[rel], index = txr_append(txr[rel], fmt, 256, texels(page, fmt))
            if index >= PAGE_LIMIT:
                raise ValueError('%s: more than %d pages' % (rel, PAGE_LIMIT))
            for i, (slot, _img) in enumerate(group):
                donor = msel.u32(tables[0] + 4 * slot)
                at = sprite(msel, donor, index, uv_of(0, h * i, 256, h))
                for table in tables:
                    msel.put(table + 4 * slot, at)

    # The icons: one page added to every archive of the records and of the
    # replay gallery, at one index in each, the rankings' padded to the records'.
    icons = dict(pics['icon'])
    small = dict(pics['icon_small'])
    if icons or small:
        placed, where = [], {}
        for i, slot in enumerate(sorted(set(icons) | set(small))):
            y = 1 + 24 * i
            if slot in icons:
                placed.append((icons[slot], 1, y))
                where[slot, 0] = uv_of(1, y, 58, 20)
            if slot in small:
                placed.append((small[slot], 64, y))
                where[slot, 1] = uv_of(64, y, 42, 14)
        pixels = texels(sheet(256, placed), 2)
        for img, rels, tables in ((record, RECORD_TXRS, RECORD_ICONS), (replay, REPLAY_TXRS, (REPLAY_ICON,))):
            index = max(len(txr_pages(txr[rel])) for rel in rels)
            for rel in rels:
                while len(txr_pages(txr[rel])) < index:     # a blank page so the new one lands at `index`
                    txr[rel], _ = txr_append(txr[rel], 2, 64, bytes(64 * 64 * 2))
                txr[rel], _ = txr_append(txr[rel], 2, 256, pixels)
            for (slot, kind), uv in where.items():
                if kind < len(tables):
                    donor = img.u32(tables[kind] + 4 * slot)
                    img.put(tables[kind] + 4 * slot, sprite(img, donor, index, uv))

    # The spec cards: CAR\carproNN.txr from 20 on, named by the exe and the champagne screen.
    number = 20
    for slot, img in pics['profile']:
        while True:
            rel = 'BINDATA\\CAR\\carpro%02d.txr' % number
            if not os.path.isfile(game.path(rel)) or rel in game.state['created']:
                break
            number += 1
        pixels = texels(img, 2)
        head = bytearray(0x1000)
        head[:8] = b'RTEX' + struct.pack('<I', 1)
        struct.pack_into('<4I', head, 16, 2, 256, len(pixels), 0)
        created[rel] = bytes(head) + pixels
        exe.put(PROFILE + 4 * slot, number)
        champagn.put(CHAMPAGN_PROFILE + 4 * slot, number)
        number += 1

    outputs = {EXE: exe.done(), MSELECT: msel.done(), RECORD: record.done(), REPLAY: replay.done(),
               CHAMPAGN: champagn.done(), B_CARMDL: bytes(carmdl), B_CARTEX: bytes(cartex)}
    outputs.update(txr)
    game.write(outputs, created, log)


def restore(dest, log=print):
    path = os.path.join(dest, STATE)
    if not os.path.isfile(path):
        raise SystemExit('carslot: nothing to restore in %s' % dest)
    game = Game(dest)
    for rel in game.state['files']:
        bak = game.path(rel) + '.carslot'
        if os.path.isfile(bak):
            os.replace(bak, game.path(rel))
            log('carslot: %s back' % rel)
    for rel in game.state['created']:
        if os.path.isfile(game.path(rel)):
            os.remove(game.path(rel))
            log('carslot: %s removed' % rel)
    os.remove(path)


def main(argv):
    if len(argv) >= 3 and argv[2] == '--restore':
        restore(argv[1])
        return 0
    if len(argv) >= 4 and argv[2] == '--spec':
        car = int(argv[3], 0)
        exe = Image(Game(argv[1]).base(EXE))
        check(exe)
        text = json.dumps({'car': car, 'folder': exe.cstr(exe.u32(FOLDERS + 4 * car)),
                           'values': spec_values(exe.read(SPEC + car * SPEC_SIZE, SPEC_SIZE))}, indent=1)
        if len(argv) > 4:
            with open(argv[4], 'w') as fh:
                fh.write(text + '\n')
        else:
            print(text)
        return 0
    if len(argv) != 3:
        print(__doc__.strip())
        return 2
    with open(argv[2]) as fh:
        conf = json.load(fh)
    slots = {}
    for key, value in conf.items():
        slot = int(key)
        if slot not in SLOTS:
            raise SystemExit('carslot: %d is not one of %s' % (slot, ', '.join(map(str, SLOTS))))
        slots[slot] = value
    apply(Game(argv[1]), slots, os.path.dirname(os.path.abspath(argv[2])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

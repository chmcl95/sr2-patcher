#!/usr/bin/env python3
"""Give the hidden car ids 18, 26 and 29 cars of their own.

    python3 tools/carslot.py GAME carslot.json     # apply a slot file
    python3 tools/carslot.py GAME --spec ID [OUT]  # a car's spec block as JSON
    python3 tools/carslot.py GAME --restore        # every file back

The three ids (CARISMA, PGT2051, FOCUS) are in every per-car table and
have no folder; each copies another car in most of them (docs/CARS.md).
A slot file names, per id, what the id gets instead:

    {"18": {"perf": 17,                      # spec, curve, engine sound, gearboxes of car 17
            "spec": "carisma.json",          # the spec block from a --spec file, over perf's
            "sound": 17,                     # engine wavs, over perf's
            "tacho": 17,                     # car 17's rev counter (TACO.TXR page and needle), over perf's
            "hud_icon": 17,                  # car 17's 40x14 icon in the race HUD
            "gearbox": [0, 1, 4, 5],         # 0/1 4-speed AT/MT, 2/3 5, 4/5 6, 6/7 7
            "name": "CARISMA GT",            # race HUD, ending, network, replay gallery
            "full_name": "MITSUBISHI CARISMA GT",    # the rankings' heading, after a race or championship
            "photo": "photo.png",            # car select, 256x128
            "logo": "logo.png",              # car select, 256x64
            "icon": "icon.png",              # records, rankings, replay gallery, 58x20
            "icon_small": "icon_s.png",      # records, 42x14
            "logo_2p": "logo_2p.png",        # two-player car select, 166x40, CLOGO2P.TXR
            "icon_2p": "icon_2p.png",        # two-player race HUD, 40x14, a page added to TACO.TXR
            "icon_demo": "icon_demo.png",    # the advertise demo's ranking, 84x31, ADV_TXT.TXR
            "profile": "profile.png",        # the spec card, 256x256, CAR\\carproNN.txr
            "replay": 17,                    # the spec card's demo run: car 17's CAR\\<car>.REP
            "crew": "CARIS",                 # the podium's people, CHAMPAGN\\MCARIS0.TXR (driver),
                                             # MCARIS1.TXR, FCARIS1.TXR (co-driver, male and female
                                             # voice); or a car id for that car's
            "model": true}}                  # the car select's 3D car from the id's folder

`tacho` can instead be a rev counter of the slot's own, one of four new
kinds (16-19) after the stock sixteen; any key but `dial` defaults to
the car `from` names (perf's by default), whose kind must be a needle
(not DELTA's, IMPREZA's or MEGANE's bars and lamps):

    "tacho": {"from": 5,                     # the car it starts from
              "dial": "dial.png",            # the face, 128x128, a page added to TACO.TXR
              "rpm_scale": 1.25,             # the rpm the needle is fed, times this: a face reads to
                                             # 8000 rpm at 1.0; past 8000, more (1.25 for 10000)
              "start_angle": 0.25,           # where the needle sits at 0 rpm, 6 o'clock 0 degrees:
                                             # + turned clockwise from there, - counter-clockwise;
                                             # a signed short as Q.15, 1.0 is half a turn,
                                             # -1.0 to under 1.0 (0.5 is 9 o'clock, -0.5 3 o'clock, 0.25 45 degrees)
              "start_turns": 1,              # the short above it, whole turns; the rotation drops it
              "slope": 4.9152,               # angle per rpm from `knee` up: rpm * slope - offset
              "knee": 0, "slope_low": 1.0,   # below the knee: rpm * slope_low
              "offset": 0,
              "needle": {"from": 7,          # that car's needle model, over from's
                         "scale": [1.0, 1.0],            # width, length
                         "recolor": {"ffeeeeee": "ffff2020"}}}   # ARGB, the model's to yours

Every key is optional; an id in the file is offered on the car select.
`replay` defaults to `perf`; without either the id has no demo run, and
the narration under the spec card crashes on it, as it does on the
stock FOCUS. A replay is recorded with its car's handling, so one from
another car than `perf` may leave the road.
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
NAME = 0x4af704                         # the ending's text
NAMES = (NAME, 0x5b0914, 0x4b53e8, 0x4b5470)    # and the race HUD's, the network screens' two
TACHO = 0x5b07ec                        # the rev counter, 0-15: TACO.TXR's page, the needle (0x5b2870)
# What a rev counter's kind indexes, each table with the instructions
# that read it; a new kind moves the tables to the annex and repoints them.
KINDS, NEW_KINDS = 16, 4                # the rpm scales on the stack have 20
TACHO_TABLES = (                        # (table, entry size, [(site, offset in the table)])
    (0x5b271c, 4, [(0x42e33c, 0)]),                                     # start angle: two shorts, the angle and whole turns
    (0x5b2760, 16, [(0x42e327, 0), (0x42e307, 4), (0x42e31f, 8), (0x42e32d, 12)]),  # slope, knee, slope_low, offset
    (0x5b2870, 4, [(0x42e24c, 0)]),                                     # needle model
    (0x5b08c4, 4, [(0x42ad75, 0), (0x42ae00, 0), (0x42aeee, 0), (0x42ae71, 0)]),    # the face's sprite
)
RPM_SCALE = 0x42aced + 4                # mov [esp+0x54+4k], imm32: kind 16+k's rpm scale, 8 bytes apart
NEEDLE_KINDS = set(range(KINDS)) - {2, 4, 12}   # the others are drawn as bars or lamps (0x42dba0)
TACO = 'BINDATA\\taco.txr'              # a 128x128 page a kind; the loader takes every page as page 0's size
# The two-player race's car icons: 0x4b6aa8 a car, a part at 0x5af728 + 0x34 * n whose uv
# is 0x5aa820 + 0x14 * its first dword, drawn into the bucket of METER01.TXR's page 1,
# which is full. New icons go on a page added to TACO.TXR: the two-player load of the rev
# counters' pages loads it too, the icon draws send the new parts to a bucket of their own,
# and that bucket is drawn after the stock icons'. Parts and uvs are reached by index, so
# the new ones sit in the annex where their index comes out whole.
HUD_ICON_UV, HUD_ICON_PARTS = 0x5aa820, 0x5af728
HUD_DRAW = 0x42d710                     # (bucket, part, count, x, y) -> the bucket's new end
ICON_CALLS = (0x42f65e, 0x42f69e)       # player 2's icon, player 1's
TACO_CLOSE, CLOSE_TXR = 0x42900d, 0x475c60      # the two-player rev counter load, closing the archive
SKIP_PAGES, LOAD_PAGE = 0x475bd0, 0x475c00      # thiscall on the archive: skip n pages; load the next
HANDLES, HANDLE_COUNT = 0x5b23e8, 0x5b23e4      # the HUD's textures
D3D, QUAD_INDICES = 0x50b118, 0x5b2434
FLUSH_AFTER_ICONS = 0x42a00b            # mov esi, [0x5b2454] (6 bytes), after the icons' bucket is drawn
ICON_BUCKET = 0x400                     # bytes; a quad is 4 vertices of 32
SOUND = 0x4b5d94
HUD_ICON = 0x4b6aa8                     # the race HUD's 40x14 car icon, sprites at 0x5af728
HUD = (0x4b0cec, 0x4b0d64)
PROFILE = 0x49585c
FOLDERS = 0x4cef48
DEMO_CASE, DEMO_NONE = 0x46232c, 7      # the demo's id rewrite: a byte per id from 3; case 7 keeps it
REP_CAR = 0x104                         # a replay's car id

MSELECT = 'MSelect.dll'
MENU = 0x100b5970                       # {mask, id} x 30
PHOTO = (0x100b513c, 0x100b5880)
LOGO = 0x100b58f8
GEARBOX = 0x100b70a0                    # 4 dwords a car
CARMDL, CARTEX = 0x100b95a0, 0x100b9690 # {offset, size} into the two BINs

MS_CAR_SLOT, M_CNAME_SLOT = 0x20, 0x30  # where MSelect loads the two; its start-up adds these to the stock pages
LOGO_2P = 0x100b51b4                    # the two-player car select's logos: CLOGO2P.TXR, also at slot 0x30

RECORD = 'Record.dll'
RECORD_ICONS = (0x1009fd28, 0x1009fda0) # 58x20, 42x14
# The rankings after a race or a championship head the page with the car's
# full name: TITLES[RECORD_INDEX[id]], 0 (TOTAL RANKING) from 29 on. The
# three sites go to a table of the ids' own, 29 in it.
RECORD_TITLES, RECORD_INDEX = 0x1009fccc, 0x1010ebec
TITLE_SITES = (0x100011c0, 0x100017a0, 0x10001ba0)    # cmp r, 0x1d; jge; mov r, [r*4+RECORD_INDEX]
REPLAY = 'ReplayGallery.dll'
REPLAY_ICON, REPLAY_NAME = 0x1009c8e0, 0x1009c958
# Record and the gallery turn each uv table's pages into texture handles
# once the archive is loaded, one call a table: {the call for the icons'
# table, the function it calls, the handle map it passes}.
REGISTER = {RECORD: (0x10003b60, 0x1000f170, 0x101118dc), REPLAY: (0x10004556, 0x1000b7d0, 0x100be208)}
CHAMPAGN = 'Champagn.dll'
CHAMPAGN_PROFILE = 0x1001c110
CREW = 0x100a2398                       # the podium's people, a name a car: CHAMPAGN\M<name>0.TXR and so on
CREW_FILES = ('M%s0.TXR', 'M%s1.TXR', 'F%s1.TXR')

MISC = 'BINDATA\\MISC\\'
MS_CAR = MISC + 'MS_CAR.TXR'            # photos, two a page, pages 0x20-0x2f
M_CNAME = MISC + 'M_CNAME.TXR'          # logos, four a page, pages 0x30-0x3f
RECORD_TXRS = tuple(MISC + n for n in ('Record.txr', 'Rank10.txr', 'RankAC.txr', 'RankTA.txr'))
REPLAY_TXRS = tuple(MISC + n for n in ('RG_RG.txr', 'RG_AC.txr', 'RG_TA.txr', 'RG_10.txr'))
B_CARMDL, B_CARTEX = MISC + 'B_CARMDL.BIN', MISC + 'B_CARTEX.BIN'
PAGE_LIMIT = 16                         # MS_CAR and M_CNAME: the next archive loads 16 pages on

CLOGO2P = MISC + 'CLOGO2P.TXR'          # two-player logos, six a page

# The advertise demo's ranking: a car's 84x31 sprite at 0x1009513c, on page 1
# of ADV_TXT.TXR, which is full. The archive loads at slot 0x5a, a page a
# slot, and the modes with the ranking let pages 3-6 go at once; page 3 is
# kept and its free rows below the text take the new icons.
ADVTELOP = 'AdvTelop.dll'
ADV_TXT = MISC + 'ADV_TXT.TXR'
ADV_ICON = 0x1009513c
ADV_SLOT, ADV_PAGE, ADV_FREE = 0x5a, 3, 176     # the archive's slot, the page, its first free row
ADV_RELEASE = 0x1000112d                # push 0x5d; push eax; call [ecx+0x2c]: page 3 let go
SIZES = {'photo': (256, 128), 'logo': (256, 64), 'icon': (58, 20), 'icon_small': (42, 14), 'profile': (256, 256),
         'logo_2p': (166, 40), 'icon_2p': (40, 14), 'icon_demo': (84, 31)}
DIAL = (128, 128)
FILES = ((EXE, MSELECT, RECORD, REPLAY, CHAMPAGN, ADVTELOP, MS_CAR, M_CNAME, CLOGO2P, ADV_TXT, B_CARMDL, B_CARTEX, TACO)
         + RECORD_TXRS + REPLAY_TXRS)


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

    def add(self, data, pointers=(), chars=DATA_SECTION):
        """data in the annex; returns its VA. pointers: offsets in data of
        absolutes, which get relocation entries when the file has any."""
        self.buf, rva = patcher.append_section(self.buf, data, chars=chars)
        self.relocs += [rva + p for p in pointers]
        return self.base + rva

    def next_va(self):
        """Where the next add's data starts."""
        pe = struct.unpack_from('<I', self.buf, 0x3c)[0]
        nsec = struct.unpack_from('<H', self.buf, pe + 6)[0]
        last = pe + 24 + struct.unpack_from('<H', self.buf, pe + 20)[0] + (nsec - 1) * 40
        if self.buf[last:last + 8] == patcher.ANNEX.ljust(8, b'\0'):
            vsize, va = struct.unpack_from('<II', self.buf, last + 8)
            return self.base + va + (vsize + 15) // 16 * 16
        return self.base + patcher._next_section_rva(self.buf)

    def add_indexed(self, data, table, size, pointers=()):
        """data in the annex at a whole number of `size`-byte entries
        past `table`; returns that number."""
        pad = -(self.next_va() - table) % size
        at = self.add(bytes(pad) + data, [pad + p for p in pointers]) + pad
        if (at - table) % size:
            raise ValueError('annex placement off: 0x%x' % at)
        return (at - table) // size

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
    size = DIAL if what == 'dial' else SIZES[what]
    if img.size != size:
        raise ValueError('%s: %s is %dx%d, not %dx%d' % (path, what, *img.size, *size))
    return img


def sheet(size, placed):
    """A transparent square page with (image, x, y) pasted."""
    from PIL import Image as PIL
    page = PIL.new('RGBA', (size, size), (0, 0, 0, 0))
    for img, x, y in placed:
        page.paste(img, (x, y))
    return page


# Sprites: a 0x58-byte record {uv table, parts, count, ...}; a part is
# 0x38 bytes {uv index, rect ...}; a uv entry 0x14 {page, u0, v0, u1, v1},
# a table of them followed by its header {table, count}. The stock pages
# are an archive's own index, made good at start-up: MSelect adds the
# archive's slot, Record and the gallery look the page up in the loaded
# archive's handle map. New sprites share one new uv table a file; each
# copies a stock record and part and points them at it.

def uv_table(img, entries):
    """entries: (page, (u0, v0, u1, v1)). Returns (table VA, header VA)."""
    table = img.add(b''.join(struct.pack('<I4f', page, *uv) for page, uv in entries))
    return table, img.add(struct.pack('<II', table, len(entries)), pointers=(0,))


def sprite(img, donor, table, index):
    record = bytearray(img.read(donor, 0x58))
    parts, count = struct.unpack_from('<II', record, 4)
    if count != 1:
        raise ValueError('sprite 0x%x has %d parts' % (donor, count))
    part = bytearray(img.read(parts, 0x38))
    struct.pack_into('<I', part, 0, index)
    struct.pack_into('<II', record, 0, table, img.add(bytes(part)))
    return img.add(bytes(record), pointers=(0, 4))


def register(img, name, header):
    """The icons' table's registration call goes through a stub that makes
    it, then registers the new table with the same handle map."""
    site, func, _map = REGISTER[name]
    if img.read(site, 1) != b'\xe8' or site + 5 + struct.unpack('<i', img.read(site + 1, 4))[0] != func:
        raise ValueError('%s: 0x%x is not the call carslot knows' % (name, site))
    stub = img.add(bytes(40), chars=patcher.CODE_SECTION | DATA_SECTION)   # filled in once its address is known
    code = bytearray(b'\xff\x74\x24\x08' * 2)           # push [esp+8] twice: the map, the stock header
    code += b'\xe8' + struct.pack('<i', func - (stub + len(code) + 5))
    code += b'\x83\xc4\x08\xff\x74\x24\x08'             # add esp, 8; push [esp+8]: the map
    code += b'\x68' + struct.pack('<I', header)         # push the new header
    code += b'\xe8' + struct.pack('<i', func - (stub + len(code) + 5))
    code += b'\x83\xc4\x08\xc3'
    img.write(stub, bytes(code))
    img.relocs.append(stub - img.base + code.index(b'\x68') + 1)
    img.write(site + 1, struct.pack('<i', stub - (site + 5)))


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


def new_kinds(exe, taco, tachos, here):
    """Rev counters of the slots' own: kinds 16 on, each a copy of its
    `from` car's kind with the slot file's changes. The four tables move
    to the annex with room for them and their reads are repointed; the
    face is a page added to TACO.TXR at the kind's index."""
    if len(tachos) > NEW_KINDS:
        raise ValueError('at most %d new rev counters' % NEW_KINDS)
    if len(txr_pages(taco)) != KINDS:
        raise ValueError('%s has %d pages, not %d' % (TACO, len(txr_pages(taco)), KINDS))
    tables = [bytearray(exe.read(t, size * KINDS)) for t, size, _s in TACHO_TABLES]
    for i, (slot, conf, perf) in enumerate(tachos):
        kind = KINDS + i
        donor = exe.u32(TACHO + 4 * conf.get('from', perf if perf is not None else slot))
        if donor not in NEEDLE_KINDS:
            raise ValueError('car %d: its rev counter (kind %d) has no needle' % (slot, donor))
        rows = [bytearray(t[donor * size:(donor + 1) * size]) for t, (_a, size, _s) in zip(tables, TACHO_TABLES)]
        if 'zero' in conf:
            raise ValueError('car %d: "zero" is now "start_angle" (Q.15) and "start_turns"' % slot)
        angle, turns = struct.unpack('<Hh', rows[0])     # MGameGL's rotations keep the low 16 bits
        if 'start_angle' in conf:
            steps = round(conf['start_angle'] * 0x8000)           # Q.15: a signed short, 1.0 half a turn
            if not -0x8000 <= steps < 0x8000:
                raise ValueError('car %d: start_angle %s is not from -1.0 to under 1.0' % (slot, conf['start_angle']))
            angle = steps & 0xffff
        turns = conf.get('start_turns', turns)
        if not -0x8000 <= turns < 0x8000:
            raise ValueError('car %d: start_turns %s is not a short' % (slot, turns))
        rows[0] = struct.pack('<Hh', angle, turns)
        slope, knee, slope_low, offset = struct.unpack('<4f', rows[1])
        rows[1] = struct.pack('<4f', conf.get('slope', slope), conf.get('knee', knee),
                              conf.get('slope_low', slope_low), conf.get('offset', offset))
        rows[2] = struct.pack('<I', needle(exe, conf.get('needle', {}), struct.unpack('<I', rows[2])[0]))
        for t, row in zip(tables, rows):
            t += row
        scale = conf.get('rpm_scale', 1.0 if donor >= KINDS else rpm_scale(exe, donor))
        exe.write(RPM_SCALE + 8 * i, struct.pack('<f', scale))
        if 'dial' in conf:
            img = open_png(os.path.join(here, conf['dial']), 'dial')
            face = texels(img, 8)
        else:                                   # the donor's face
            fmt, size, nbytes, _z = txr_pages(taco)[donor]
            face = taco[0x1000 + donor * nbytes:0x1000 + (donor + 1) * nbytes]
        taco, _index = txr_append(taco, 8 if 'dial' in conf else txr_pages(taco)[donor][0], 128, face)
        exe.put(TACHO + 4 * slot, kind)
    for t, (old, _size, sites) in zip(tables, TACHO_TABLES):
        new = exe.add(bytes(t))
        for site, delta in sites:
            ins = exe.read(site, 12)
            at = ins.find(struct.pack('<I', old + delta))
            if at < 1:
                raise ValueError('%s: 0x%x does not read 0x%x' % (EXE, site, old + delta))
            exe.write(site + at, struct.pack('<I', new + delta))
    return taco


def rpm_scale(exe, kind):
    """A stock kind's rpm scale, from the immediates that fill the stack
    array (mov [esp+0x14+4k], imm32 from 0x42ac6d)."""
    return struct.unpack('<f', exe.read(0x42ac6d + 4 + 8 * kind, 4))[0]


def needle(exe, conf, stock):
    """A needle: the stock descriptor copied with vertices of its own,
    scaled across and along and recoloured colour by colour (docs/CARS.md
    lists each model's); faces and material shared."""
    if 'from' in conf:
        stock = exe.u32(0x5b2870 + 4 * exe.u32(TACHO + 4 * conf['from']))
    if not set(conf) - {'from'}:
        return stock
    head = bytearray(exe.read(stock, 0x40))
    verts, _faces, _mat, count = struct.unpack_from('<4I', head)
    sx, sy = conf.get('scale', [1.0, 1.0])
    recolor = {int(a, 16): int(b, 16) for a, b in conf.get('recolor', {}).items()}
    out = bytearray()
    for i in range(count):
        v = bytearray(exe.read(verts + 0x20 * i, 0x20))
        x, y, z = struct.unpack_from('<3f', v)
        struct.pack_into('<3f', v, 0, x * sx, y * sy, z)
        colour = struct.unpack_from('<I', v, 0x10)[0]
        struct.pack_into('<I', v, 0x10, recolor.get(colour, colour))
        out += v
    struct.pack_into('<I', head, 0, exe.add(bytes(out)))
    return exe.add(bytes(head))


def icons_2p(exe, taco, icons):
    """The two-player race's car icons of the slots' own (see HUD_ICON_UV):
    a 128x128 page added to TACO.TXR, three icons a row; a uv and a part
    for each in the annex; three stubs."""
    if len(icons) > 24:
        raise ValueError('at most 24 two-player icons')
    for site in ICON_CALLS + (TACO_CLOSE,):
        target = site + 5 + struct.unpack('<i', exe.read(site + 1, 4))[0]
        if exe.read(site, 1) != b'\xe8' or target not in (HUD_DRAW, CLOSE_TXR):
            raise ValueError('%s: 0x%x is not the call carslot knows' % (EXE, site))
    if exe.read(FLUSH_AFTER_ICONS, 6) != b'\x8b\x35' + struct.pack('<I', 0x5b2454):
        raise ValueError('%s: 0x%x is not the load carslot knows' % (EXE, FLUSH_AFTER_ICONS))
    spots = [(1 + 42 * (i % 3), 1 + 16 * (i // 3)) for i in range(len(icons))]
    page = sheet(128, [(img, x, y) for (_s, img), (x, y) in zip(icons, spots)])
    taco, index = txr_append(taco, 2, 128, texels(page, 2))
    uv0 = exe.add_indexed(b''.join(struct.pack('<I4f', 0, *uv_of(x, y, 40, 14, 128)) for x, y in spots),
                          HUD_ICON_UV, 0x14)
    parts = b''
    for i, (slot, _img) in enumerate(icons):
        part = bytearray(exe.read(HUD_ICON_PARTS + 0x34 * exe.u32(HUD_ICON + 4 * slot), 0x34))
        struct.pack_into('<I', part, 0, uv0 + i)
        parts += part
    part0 = exe.add_indexed(parts, HUD_ICON_PARTS, 0x34)
    lo = HUD_ICON_PARTS + 0x34 * part0
    for i, (slot, _img) in enumerate(icons):
        exe.put(HUD_ICON + 4 * slot, part0 + i)

    data = exe.add(bytes(8 + ICON_BUCKET))      # the bucket's end, the page's handle index, the bucket
    end, which, bucket = data, data + 4, data + 8
    exe.put(end, bucket)

    def code(parts):
        """bytes with ('rel', target) placeholders, placed in the annex."""
        size = sum(5 if isinstance(p, tuple) else len(p) for p in parts)
        at = exe.add(bytes(size), chars=patcher.CODE_SECTION | DATA_SECTION)
        out = bytearray()
        for p in parts:
            if isinstance(p, tuple):            # (opcode, target): call/jmp rel32
                out += p[0] + struct.pack('<i', p[1] - (at + len(out) + 5))
            else:
                out += p
        exe.write(at, bytes(out))
        return at

    d = lambda v: struct.pack('<I', v)          # noqa: E731
    # The two-player load: before the archive closes, skip to the icon page,
    # load it and add its handle to the HUD's textures (ecx: the archive).
    load = code([b'\x51\x8b\x41\x10\xba' + d(index) + b'\x2b\xd0\x52', (b'\xe8', SKIP_PAGES),
                 b'\x8b\x0c\x24', (b'\xe8', LOAD_PAGE),
                 b'\x8b\x0c\x24\x8b\x51\x04\x8b\x92' + d(4 * index) + b'\xa1' + d(HANDLE_COUNT)
                 + b'\x89\x14\x85' + d(HANDLES) + b'\xa3' + d(which) + b'\x40\xa3' + d(HANDLE_COUNT) + b'\x59',
                 (b'\xe9', CLOSE_TXR)])
    # An icon draw: a new part goes to the bucket of its own, the caller's
    # bucket comes back as it was.
    draw = code([b'\x8b\x44\x24\x08\x3d' + d(lo) + b'\x72\x3b\x3d' + d(lo + 0x34 * len(icons)) + b'\x73\x34'
                 + b'\xa1' + d(end) + b'\x3d' + d(bucket + ICON_BUCKET - 0x100) + b'\x72\x05\xb8' + d(bucket)
                 + b'\xff\x74\x24\x14' * 4 + b'\x50', (b'\xe8', HUD_DRAW),
                 b'\x83\xc4\x14\xa3' + d(end) + b'\x8b\x44\x24\x04\xc3', (b'\xe9', HUD_DRAW)])
    # After the stock icons are drawn: the bucket of the new ones with their page.
    flush = code([b'\x60\x8b\x35' + d(end) + b'\x81\xee' + d(bucket) + b'\xc1\xee\x05\x74\x45'
                  + b'\xa1' + d(which) + b'\x8b\x0c\x85' + d(HANDLES) + b'\xa1' + d(D3D) + b'\x8b\x10\x51\x50'
                  + b'\xff\x92\xac\x00\x00\x00'
                  + b'\x8d\x04\x76\xd1\xe8\x50\xff\x35' + d(QUAD_INDICES) + b'\x56\x68' + d(bucket)
                  + b'\xa1' + d(D3D) + b'\x50\x8b\x10\xff\x92\xc4\x00\x00\x00'
                  + b'\xc7\x05' + d(end) + d(bucket)
                  + b'\x61\x8b\x35' + d(0x5b2454) + b'\xc3'])
    for site in ICON_CALLS:
        exe.write(site + 1, struct.pack('<i', draw - (site + 5)))
    exe.write(TACO_CLOSE + 1, struct.pack('<i', load - (TACO_CLOSE + 5)))
    exe.write(FLUSH_AFTER_ICONS, b'\xe8' + struct.pack('<i', flush - (FLUSH_AFTER_ICONS + 5)) + b'\x90')
    return taco


def demo_icons(adv, txt, icons):
    """The advertise demo's ranking icons of the slots' own (see ADV_ICON):
    pasted three a row into page 3's free rows, which then stays loaded."""
    w, h = SIZES['icon_demo']
    spots = [(86 * (i % 3), ADV_FREE + 1 + 32 * (i // 3)) for i in range(len(icons))]
    if spots and spots[-1][1] + h > 256:
        raise ValueError('at most %d demo icons' % (3 * ((256 - ADV_FREE) // 32)))
    if adv.read(ADV_RELEASE, 6) != b'\x6a\x5d\x50\xff\x51\x2c':
        raise ValueError('%s: 0x%x is not the release carslot knows' % (ADVTELOP, ADV_RELEASE))
    pages = txr_pages(txt)
    if pages[ADV_PAGE][:2] != (2, 256):
        raise ValueError('%s: page %d is not 256x256 1555' % (ADV_TXT, ADV_PAGE))
    start = 0x1000 + sum(p[2] for p in pages[:ADV_PAGE])
    out = bytearray(txt)
    for (_slot, img), (x, y) in zip(icons, spots):
        pixels = texels(img, 2)
        for row in range(h):
            at = start + 2 * (256 * (y + row) + x)
            if any(out[at:at + 2 * w]):
                raise ValueError('%s: page %d is not free at row %d' % (ADV_TXT, ADV_PAGE, y + row))
            out[at:at + 2 * w] = pixels[2 * w * row:2 * w * (row + 1)]
    table, _header = uv_table(adv, [(ADV_SLOT + ADV_PAGE, uv_of(x, y, w, h)) for x, y in spots])
    for i, (slot, _img) in enumerate(icons):
        adv.put(ADV_ICON + 4 * slot, sprite(adv, adv.u32(ADV_ICON + 4 * slot), table, i))
    adv.write(ADV_RELEASE, b'\x90' * 6)
    return bytes(out)


def apply(game, slots, here, log=print):
    exe = Image(game.base(EXE))
    check(exe)
    msel = Image(game.base(MSELECT))
    record = Image(game.base(RECORD))
    replay = Image(game.base(REPLAY))
    champagn = Image(game.base(CHAMPAGN))
    adv = Image(game.base(ADVTELOP))
    adv_txt = game.base(ADV_TXT)
    txr = {rel: game.base(rel) for rel in (MS_CAR, M_CNAME, CLOGO2P) + RECORD_TXRS + REPLAY_TXRS}
    carmdl, cartex = bytearray(game.base(B_CARMDL)), bytearray(game.base(B_CARTEX))
    taco = game.base(TACO)
    created = {}
    pics = {what: [] for what in SIZES}
    new_tachos = []

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
        for key, table in (('sound', SOUND), ('tacho', TACHO)):
            donor = conf.get(key, perf)
            if isinstance(donor, dict):         # a rev counter of its own, made after the loop
                new_tachos.append((slot, donor, perf))
            elif donor is not None:
                exe.put(table + 4 * slot, exe.u32(table + 4 * donor))
        if 'hud_icon' in conf:                  # a picture of a car, so not perf's by default
            exe.put(HUD_ICON + 4 * slot, exe.u32(HUD_ICON + 4 * conf['hud_icon']))
        if 'gearbox' in conf:
            msel.write(GEARBOX + 16 * slot, struct.pack('<4I', *conf['gearbox']))
        if 'name' in conf:
            text = conf['name'].encode('latin-1') + b'\0'
            at = exe.add(text)
            for table in NAMES:
                exe.put(table + 4 * slot, at)
            replay.put(REPLAY_NAME + 4 * slot, replay.add(text))
        crew = conf.get('crew')
        if isinstance(crew, int):
            if not 0 <= crew < CARS:
                raise ValueError('crew %d: no such car' % crew)
            champagn.put(CREW + 4 * slot, champagn.u32(CREW + 4 * crew))
        elif crew is not None:
            if not (crew.isascii() and crew.isalnum() and len(crew) <= 16):
                raise ValueError('crew %r: letters and digits, 16 at most' % crew)
            champagn.put(CREW + 4 * slot, champagn.add(crew.upper().encode() + b'\0'))
            for fname in CREW_FILES:
                if not os.path.isfile(game.path('BINDATA\\CHAMPAGN\\' + fname % crew)):
                    log('carslot: car %d: no BINDATA\\CHAMPAGN\\%s' % (slot, fname % crew))
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

    # The photos, two a page, the logos, four a page, and the two-player
    # logos, six a page as the stock's (x 1, every 42 from y 1), on pages
    # added to their archives; MSelect's pages are slots, so the new table's
    # are too. CLOGO2P and M_CNAME both load at slot 0x30, each in its mode.
    entries, uses = [], []
    for what, rel, per, tables, fmt, slot0, x0, y0, step in (
            ('photo', MS_CAR, 2, PHOTO, 2, MS_CAR_SLOT, 0, 0, 128),
            ('logo', M_CNAME, 4, (LOGO,), 8, M_CNAME_SLOT, 0, 0, 64),
            ('logo_2p', CLOGO2P, 6, (LOGO_2P,), 8, M_CNAME_SLOT, 1, 1, 42)):
        items = pics[what]
        w, h = SIZES[what]
        for first in range(0, len(items), per):
            group = items[first:first + per]
            page = sheet(256, [(img, x0, y0 + step * i) for i, (_s, img) in enumerate(group)])
            txr[rel], index = txr_append(txr[rel], fmt, 256, texels(page, fmt))
            if index >= PAGE_LIMIT:
                raise ValueError('%s: more than %d pages' % (rel, PAGE_LIMIT))
            for i, (slot, _img) in enumerate(group):
                uses.append((tables, slot, len(entries)))
                entries.append((slot0 + index, uv_of(x0, y0 + step * i, w, h)))
    if entries:
        table, _header = uv_table(msel, entries)
        for tables, slot, index in uses:
            at = sprite(msel, msel.u32(tables[0] + 4 * slot), table, index)
            for t in tables:
                msel.put(t + 4 * slot, at)

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
        for img, name, rels, tables in ((record, RECORD, RECORD_TXRS, RECORD_ICONS),
                                        (replay, REPLAY, REPLAY_TXRS, (REPLAY_ICON,))):
            index = max(len(txr_pages(txr[rel])) for rel in rels)
            for rel in rels:
                while len(txr_pages(txr[rel])) < index:     # a blank page so the new one lands at `index`
                    txr[rel], _ = txr_append(txr[rel], 2, 64, bytes(64 * 64 * 2))
                txr[rel], _ = txr_append(txr[rel], 2, 256, pixels)
            used = [(slot, kind, uv) for (slot, kind), uv in sorted(where.items()) if kind < len(tables)]
            table, header = uv_table(img, [(index, uv) for _s, _k, uv in used])
            register(img, name, header)
            for i, (slot, kind, _uv) in enumerate(used):
                donor = img.u32(tables[kind] + 4 * slot)
                img.put(tables[kind] + 4 * slot, sprite(img, donor, table, i))

    # The rankings' full names, by id.
    titles = [(slot, conf['full_name']) for slot, conf in sorted(slots.items()) if 'full_name' in conf]
    if titles:
        texts = [record.add(text.encode('latin-1') + b'\0') for _s, text in titles]
        first = record.add_indexed(struct.pack('<%dI' % len(texts), *texts), RECORD_TITLES, 4,
                                   range(0, 4 * len(texts), 4))
        index = [record.u32(RECORD_INDEX + 4 * i) if i < 0x1d else 0 for i in range(CARS)]
        for i, (slot, _text) in enumerate(titles):
            index[slot] = first + i
        table = record.add(struct.pack('<%dI' % CARS, *index))
        for site in TITLE_SITES:
            code = record.read(site, 12)
            if code[2] != 0x1d or code[3] != 0x7d or code[5] != 0x8b or struct.unpack_from('<I', code, 8)[0] != RECORD_INDEX:
                raise ValueError('Record.dll: not the title lookup at 0x%x' % site)
            record.write(site + 2, bytes([CARS]))
            record.put(site + 8, table)

    # The demo run under the spec card:CAR\<car>.REP, a copy of the replay
    # car's with the id in it; the demo's rewrite of 26 to 11 goes.
    for slot, conf in sorted(slots.items()):
        donor = conf.get('replay', conf.get('perf'))
        rel = 'BINDATA\\CAR\\%s.REP' % SLOTS[slot]
        if os.path.isfile(game.path(rel)) and rel not in game.state['created']:
            log('carslot: %s is there already, kept' % rel)
            donor = None
        if 3 <= slot < 3 + 0x18 and (donor is not None or os.path.isfile(game.path(rel))):
            exe.write(DEMO_CASE + slot - 3, bytes([DEMO_NONE]))
        if donor is None:
            continue
        src = game.path('BINDATA\\CAR\\%s.REP' % exe.cstr(exe.u32(FOLDERS + 4 * donor)))
        if not os.path.isfile(src):
            raise ValueError('no replay for car %d: %s' % (donor, src))
        with open(src, 'rb') as fh:
            rep = bytearray(fh.read())
        if struct.unpack_from('<I', rep, REP_CAR)[0] != donor:
            raise ValueError('%s: the car at 0x%x is not %d' % (src, REP_CAR, donor))
        struct.pack_into('<I', rep, REP_CAR, slot)
        created[rel] = bytes(rep)

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

    if new_tachos:
        taco = new_kinds(exe, taco, new_tachos, here)
    if pics['icon_2p']:                 # after the new kinds: its page is TACO.TXR's last
        taco = icons_2p(exe, taco, pics['icon_2p'])
    if pics['icon_demo']:
        adv_txt = demo_icons(adv, adv_txt, pics['icon_demo'])

    outputs = {EXE: exe.done(), MSELECT: msel.done(), RECORD: record.done(), REPLAY: replay.done(),
               CHAMPAGN: champagn.done(), ADVTELOP: adv.done(), ADV_TXT: adv_txt, B_CARMDL: bytes(carmdl), B_CARTEX: bytes(cartex), TACO: taco}
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

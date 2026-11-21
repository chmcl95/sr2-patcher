#!/usr/bin/env python3
"""Give the hidden car ids 18, 26 and 29 cars of their own, and new ids 30-127.

    python3 tools/carslot.py GAME carslot.json     # apply a slot file
    python3 tools/carslot.py GAME --spec ID [OUT]  # a car's spec block as JSON
    python3 tools/carslot.py GAME --restore        # every file back

The three ids (CARISMA, PGT2051, FOCUS) are in every per-car table and
have no folder; each copies another car in most of them (docs/CARS.md).
An id from 30 on needs the tables moved, which a slot file naming one
does: every per-car table goes to the annex with room for 128, and the
new id starts as a copy of its `perf` car (0-29, required) in all of
them, with a folder of its own, BINDATA\\<FOLDER> from `folder`
(required; its models named r_<folder>.mdl ...). It goes on the menu
after the stock cars, on the Corolla's bit. The advertise demo runs the
stock cars: no `icon_demo` for it. Its records stay out of SR2_SAVE.DAT,
in RECORD\\RANKING.REC and RECORD\\<FOLDER>.REC (asm/carrec.asm).
A slot file names, per id, what the id gets instead:

    {"18": {"folder": "CARISMA",             # BINDATA\\CARISMA beside the slot file: the car's models,
                                             # textures and engine wavs, copied into the id's folder
            "perf": 17,                      # spec, curve, engine sound, gearboxes of car 17
            "spec": "carisma.json",          # the spec block from a --spec file, over perf's
            "sound": 17,                     # engine wavs, over perf's
            "tacho": 17,                     # car 17's rev counter (TACO.TXR page and needle), over perf's
            "hud_icon": 17,                  # car 17's 40x14 icon in the race HUD
            "desert": true,                  # the desert kit (desert.mdl, de_light.mdl) or not, or a car's
            "rival": 28,                     # the one-race opponent and the championship's first:
                                             # 6, 7, 28, 5, 0, 27 or 1 (not 2, which no rotation starts at)
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
                                             # voice), copied from BINDATA\\CHAMPAGN beside the slot
                                             # file when there; or a car id for that car's
            "crew_height": 4,                # where the podium's two sit in the car: car 4's, or a float
                                             # (0x1001c254's, the larger the higher)
            "podium_run": 12,                # the car's run on the podium: car 12's (the front drives'
                                             # side turn 1, 12, 14; the drifts the others)
            "model": true}}                  # the car select's 3D car from the id's folder

`model` can instead name its parts, each defaulting to the folder's:

    "model": {"mdl": "r_car.mdl",            # the 3D car, a PC MDL as it is; the folder's r_<car>.mdl
                                             # gets the car select's windows
              "texture": "car.txr",          # an RTEX of two, the 256x256 body and the 64x64 tyre
              "reflection": 4}               # the car under the floor: car 4's, or a PC MDL
                                             # appended to B_REFMDL.BIN; none by default

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
wavs go in its folder under BINDATA as for any car (r_<id's folder>.mdl
...), from `folder` or put there by hand; the engine wavs keep the names
of the car `sound` (or `perf`) names. What carslot copies in, and the
folders it makes for it, go at --restore and when the slot file no
longer names them; a file of the same name it did not put there stays.

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
CARS = 30                               # the stock tables' entries, ids 0-29
IDS = 128                               # ids 0-127 once the tables are moved, for a slot from 30 on
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
# The lamp kit on desert courses: a list of model numbers (0x4cc410), -1
# ended; 7 desert.mdl, 8 de_light.mdl, 11 normal.mdl. 306, 106 and MEGANE
# have normal.mdl alone. The glow offset goes with de_light.mdl.
DESERT_KIT, DESERT_GLOW = 0x4cd3c8, 0x4cd2cc
DESERT_LISTS = {True: (7, 8, 11, -1), False: (11, -1)}
# The rivals: an id's base car (0x4b1074; 18 the Lancer, 26 the 205),
# the base car's set (0x49afd0), the set's first place (0x49b0a4) in the
# rotation (0x49b048) the opponents are taken from in turn, eight cars,
# and the player's own car ninth for the sets from 8 on. Its first is the
# one-race opponent and the one the race marks as the rival (0x41b4b0,
# from the id without its base car).
RIVAL_BASE, RIVAL_SET, RIVAL_START, ROTATION = 0x4b1074, 0x49afd0, 0x49b0a4, 0x49b048
ROTATION_CARS, RIVAL_SETS, OWN_CAR_SETS = 8, 22, 8
PROFILE = 0x49585c
FOLDERS = 0x4cef48
DEMO_CASE, DEMO_NONE = 0x46232c, 7      # the demo's id rewrite: a byte per id from 3; case 7 keeps it
REP_CAR = 0x104                         # a replay's car id

MSELECT = 'MSelect.dll'
MENU = 0x100b5970                       # {mask, id} x 30
# The two builders of the menu keep the entries whose mask is in the
# unlock mask, the cursor on the one in the current car's (1 << id); a
# stub at each start ORs the slots' bits into the unlock mask, so their
# entries keep their own bits and the cursor finds them again.
MENU_BUILDERS = ((0x10002a97, b'\x8b\x5c\x24\x0c\x55'),               # mov ebx, [esp+0xc]; push ebp
                 (0x10008c14, b'\x8b\x5c\x24\x18\x8b\x6c\x24\x14'))   # mov ebx, [esp+0x18]; mov ebp, [esp+0x14]
CAR_REMAP = 0x10004ce4                  # ids 3-26: a case of 0x10004c20, which turns the id into a menu car's; 6 none
# The ring of photos: its shape is a polynomial of u = (count - 8) / 11,
# 1.0 at the 19 cars the stock menu has at most; past 19 the ring draws in
# (22 cars put a neighbour 153 px off where 19 put it 218).
# The two screens' fild count; add esp, 8; fsub 8.0; fmul 1/11 become nops;
# add esp, 8; fld 11.0; fmul 1/11, so that u is 1.0, the shape of 19 cars.
RING = ((0x100030e1, 0x1c), (0x100093a1, 0x34))
RING_8, RING_11 = 0x10031184, 0x10031130
PHOTO = (0x100b513c, 0x100b5880)
LOGO = 0x100b58f8
GEARBOX = 0x100b70a0                    # 4 dwords a car
CARMDL, CARTEX, REFMDL = 0x100b95a0, 0x100b9690, 0x100b9780    # {offset, size} into the three BINs
# The exe's own copy of the three, read by time attack (0x4326b0 and 0x432780); an empty
# entry is a VirtualAlloc of 0, and the NULL it gets back is read at 0x475d9a.
EXE_CARMDL, EXE_CARTEX, EXE_REFMDL = 0x4b2c40, 0x4b2d30, 0x4b2e20

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
# Where the podium's two sit: a float a car, over the car's height; the
# two are put that plus 1.905 (0x1001c304), the larger the higher; ESCORT (2) plus 1.1
# (0x100a2414, 0x100a2420), a test for id 2 at 0x10003858 and 0x100038e8.
CREW_HEIGHT, CREW_UP, CREW_UP_ESCORT = 0x1001c254, 0x1001c304, 0x100a2414
# The car's run on the podium, a byte a car into a switch at 0x1000549f:
# 0 the drifts of most four-wheel drives (runs 6-8), 1 the front drives'
# side turn (2, 3), 2 the others' drifts (0-3).
PODIUM_RUN = 0x10005808

MISC = 'BINDATA\\MISC\\'
MS_CAR = MISC + 'MS_CAR.TXR'            # photos, two a page, pages 0x20-0x2f
M_CNAME = MISC + 'M_CNAME.TXR'          # logos, four a page, pages 0x30-0x3f
RECORD_TXRS = tuple(MISC + n for n in ('Record.txr', 'Rank10.txr', 'RankAC.txr', 'RankTA.txr'))
REPLAY_TXRS = tuple(MISC + n for n in ('RG_RG.txr', 'RG_AC.txr', 'RG_TA.txr', 'RG_10.txr'))
B_CARMDL, B_CARTEX, B_REFMDL = MISC + 'B_CARMDL.BIN', MISC + 'B_CARTEX.BIN', MISC + 'B_REFMDL.BIN'
PAGE_LIMIT = 16                         # MS_CAR and M_CNAME: the next archive loads 16 pages on

CLOGO2P = MISC + 'CLOGO2P.TXR'          # two-player logos, six a page

# The advertise demo's ranking: a car's 84x31 sprite at 0x1009513c, on page 1
# of ADV_TXT.TXR, which is full. The archive loads at slot 0x5a, a page a
# slot, and the modes with the ranking let pages 3-6 go at once; page 3 is
# kept and its free rows below the text (and padattract's lettering) take
# the new icons.
ADVTELOP = 'AdvTelop.dll'
ADV_TXT = MISC + 'ADV_TXT.TXR'
ADV_ICON = 0x1009513c
ADV_SLOT, ADV_PAGE, ADV_FREE = 0x5a, 3, 176     # the archive's slot, the page, its first free row at least
ADV_RELEASE = 0x1000112d                # push 0x5d; push eax; call [ecx+0x2c]: page 3 let go
SIZES = {'photo': (256, 128), 'logo': (256, 64), 'icon': (58, 20), 'icon_small': (42, 14), 'profile': (256, 256),
         'logo_2p': (166, 40), 'icon_2p': (40, 14), 'icon_demo': (84, 31)}
DIAL = (128, 128)
FILES = ((EXE, MSELECT, RECORD, REPLAY, CHAMPAGN, ADVTELOP, MS_CAR, M_CNAME, CLOGO2P, ADV_TXT, B_CARMDL, B_CARTEX, B_REFMDL, TACO)
         + RECORD_TXRS + REPLAY_TXRS)

# Ids from 30 on: every table of one entry a car moves to the annex with
# IDS entries (docs/CARS.md, *Past 30*), and a new id starts as a copy of
# its `perf` car in each but its own folder and names. The exe has no
# relocations: its tables come with the operands that point into them.
EXE_TABLES = (                          # (table, entry size, operands)
    (SPEC, SPEC_SIZE, (0x4051b9,)),
    (CURVE, 4, (0x405c72,)),
    (NAME, 4, (0x41584b,)),
    (0x5b0914, 4, (0x42c2ca,)),
    (0x4b53e8, 4, (0x435964,)),
    (0x4b5470, 4, (0x43598e,)),
    (TACHO, 4, (0x428dd6, 0x428e1f, 0x428e32)),
    (SOUND, 4, (0x4422bd, 0x4422d7)),
    (HUD_ICON, 4, (0x42f643, 0x42f689, 0x44881f)),
    (PROFILE, 4, (0x41217d, 0x412240)),
    (0x4cedc4, 4, (0x4193d4, 0x41ba6d, 0x41f507, 0x44f2e4, 0x44f4cc)),     # the records' index
    (RIVAL_BASE, 4, (0x41b365, 0x41b53d)),
    (RIVAL_SET, 4, (0x41b36f, 0x41b4d1, 0x41b564)),
    (HUD[0], 4, (0x418541,)),
    (HUD[1], 4, (0x41856c,)),
    (0x4d0368, 4, (0x485b69,)),                                             # the glows' kind
    (0x49dd50, 8, (0x4676b1, 0x4676fd)),                                    # colours
    (DESERT_GLOW, 4, (0x46a5fc,)),
    (DESERT_KIT, 4, (0x469dd7,)),
    (0x4cd440, 4, (0x469dc7,)),                                             # the lamp kits of the
    (0x4cd4b8, 4, (0x469daf,)),                                             # other course types
    (FOLDERS, 4, (0x476676, 0x476913, 0x476f17)),
    (0x4ccf48, 12, (0x469ba1, 0x46addd)),                                   # <car>.bin, <car>, <car>.txb
    # the models loaded, a car's 0x40 bytes; 0x506ac8, the last dword of
    # the last entry, is a variable of its own and stays
    (0x50634c, 0x40, (0x469b65, 0x469b96, 0x469fb9, 0x469ff2, 0x469ffb, 0x46a006,
                      0x46a1df, 0x46a20b, 0x46a230, 0x46a255, 0x46a7fc)),
    (EXE_CARMDL, 8, (0x43283a, 0x432884, 0x43288b)),
    (EXE_CARTEX, 8, (0x4326ef, 0x4326f6)),
    (EXE_REFMDL, 8, (0x432954, 0x4329a2, 0x4329a9)),
    (0x4bc56c, 4, (0x44eac7,)),                                             # the replay's car: 23-25 the cars they stand for
    (0x4cb850, 0x60, (0x46ae49, 0x46ae5b, 0x46ae6d, 0x46aecb)),             # the body's look, 0x20 a course kind (add r, table + 0x20k)
    # the lamp kit's models, 13 objects of 0x10 a car (vtable, model ...), built and
    # destroyed at start and exit as 0x186 objects; 0x508548 just past it is a variable
    (0x506ce8, 0xd0, (0x469972, 0x46999d, 0x469d1b, 0x469d23, 0x469e2f, 0x469e8d, 0x469edf,
                      0x46a3f0, 0x46a44f, 0x46a46d, 0x46a474, 0x46a47f, 0x46a486, 0x46a4a2,
                      0x46a4ad, 0x46a4e2, 0x46a53b, 0x46a578, 0x46a57e, 0x46a5c8, 0x46a5d3,
                      0x46a5de, 0x46a5ed, 0x46a63f, 0x46a64a, 0x46a66f, 0x46a686, 0x46a691, 0x46a82a)),
)
LAMP_COUNTS = (0x46996b, 0x469996)      # push 0x186: the objects built and destroyed
EXE_OWN = (FOLDERS, 0x4ccf48, 0x50634c, 0x4bc56c, 0x506ce8)    # not copied from perf
# The records' index reads as 0 from 29 on: cmp id, 0x1d; jge (jae for the byte) past the
# lookup. With a table of IDS the lookup is for every id.
RECORD_BOUNDS = ((0x4193cf, 0x7d), (0x41ba68, 0x7d), (0x41f4fd, 0x73), (0x44f2df, 0x7d), (0x44f4c7, 0x7d))
# A DLL's tables: (table, entry size, copied from perf, end operands). Its
# references come from the relocations.
MSELECT_TABLES = (
    (MENU, 8, False, (0x10002ac8, 0x10008c43)),     # the two builders' loop ends
    (0x1010f33c, 4, False, ()), (0x1010f3e8, 4, False, ()),     # the menu lists
    (PHOTO[0], 4, True, ()), (PHOTO[1], 4, True, ()), (LOGO, 4, True, ()), (LOGO_2P, 4, True, ()),
    (GEARBOX, 16, True, ()),
    (0x100b7600, 4, True, ()),                                  # the spec card's figures
    (0x1010c8a4, 4, True, ()),                                  # the gearbox choice's labels, a pair of 0x1010c884
    (CARMDL, 8, True, ()), (CARTEX, 8, True, (0x10018d5f,)), (REFMDL, 8, True, ()),
    (0x1011a71c, 4, False, ()), (0x1011a2fc, 4, False, ()),     # the 3D cars loaded, object and model
    (0x1011a564, 4, False, ()), (0x1011a14c, 4, False, ()),     # and their reflections
    (0x1010db44, 4, False, ()),                                 # the loader's folders
)
# The 3D cars are loaded at the screen's start, CARS of each kind (mov [count], 30).
# A car with a 3D car takes the next two texture slots from 0x60 (its body
# and tyre), the slot table 0x1011a7a8 has 0x100: 80 cars at most.
MSELECT_COUNTS = (0x10018a40, 0x10018bbb)       # the immediates
SELECT_CARS = (0x100 - 0x60) // 2
# Back on a car menu its cursor is on the entry whose mask has the car's bit,
# 1 << id (each stock entry's mask is its own bit): from 30 on the bit is
# another car's, or wraps, and a new entry's mask is the Corolla's. The sites
# that make the bit pass the id itself, and the two builders compare it with
# the entry's id: (site, stock bytes, ours).
MENU_CURSOR = tuple((site, 'ba01000000d3e2', '8bd19090909090')      # mov edx, ecx (not 1 << cl)
                    for site in (0x10004c4d, 0x10004c63, 0x10004c79, 0x10004c8f, 0x10004ca5, 0x10004cbb)) + (
    (0x100026c7, '8bf2d3e6', '8bf19090'), (0x100026d1, '8bf2d3e6', '8bf19090'),    # the 2P screen's two cars
    (0x10002eef, 'b801000000d3e0', '8bc19090909090'),                 # the 2P menu's choice
    # test ebp, edx (the entry's mask); je; mov [cursor], index; mov edx, [eax+4]
    #  -> mov edx, [eax+4] (the entry's id); cmp ebp, edx; jne; mov [cursor], index
    (0x10002ab4, '85d574038971188b5004', '8b500439d57503897118'),    # 2P
    (0x10008c2f, '85d574038979308b5004', '8b500439d57503897930'),    # 1P
)
RECORD_TABLES = ((RECORD_ICONS[0], 4, True, ()), (RECORD_ICONS[1], 4, True, ()), (0x1010fe0c, 4, False, ()),
                 (RECORD_INDEX, 4, True, ()))
# Record's lookups of the records' index by id, past 29 as 0 (cmp id, 0x1d; jae/jge),
# as the exe's (RECORD_BOUNDS); the title sites are TITLE_SITES'.
RECORD_DLL_BOUNDS = ((0x100058c2, 0x73), (0x10005901, 0x73), (0x10008aec, 0x7d))
# The podium's run: cmp id, 0x1d; ... ja to a default that reads its run from the stack.
PODIUM_BOUND = 0x1000545f
REPLAY_TABLES = ((REPLAY_ICON, 4, True, ()), (REPLAY_NAME, 4, True, ()), (0x100bca2c, 4, False, ()))
CHAMPAGN_TABLES = ((CHAMPAGN_PROFILE, 4, True, ()), (CREW, 4, True, ()), (CREW_HEIGHT, 4, True, ()),
                   (PODIUM_RUN, 1, True, ()), (0x100a3714, 4, False, ()))
DLL_FOLDERS = {MSELECT: 0x1010db44, RECORD: 0x1010fe0c, REPLAY: 0x100bca2c, CHAMPAGN: 0x100a3714}

# The records of the ids from 30 on, kept out of SR2_SAVE.DAT (asm/carrec.asm):
# the calls its hooks take (site, the routine called, the hook), the five
# places a car's own list is found (site, stock bytes, stub), the best
# lap update it jumps from, and its placeholders' values.
CARREC_CALLS = ((0x44edb4, 0x44eb80, 'hook_shared'), (0x44ee24, 0x44eb80, 'hook_shared'),    # the arcade, a year
                (0x44f002, 0x44eb80, 'hook_shared'), (0x44f330, 0x44eb80, 'hook_shared'),    # a course list, a time attack total
                (0x44eed3, 0x41f9e0, 'pw_gate'),                                             # the ten years' total password
                (0x427dcb, 0x44fda0, 'load_hook'), (0x428275, 0x44f7b0, 'save_hook'))
CARREC_LISTS = ((0x4193f0, '8db43e180d0000', 's1'), (0x41bacf, '8b840a180d0000', 's2'),
                (0x41f51e, '8d9c02100d0000', 's3'), (0x44f2fc, '8d8c02100d0000', 's4'),
                (0x44f4f6, '8d8c11100d0000', 's5'))
CARREC_BESTLAP = (0x44f057, '8b4424108bd3c1e2048b8c02ec1c00008d34023b0dc8225b00')
CARREC_VALUES = {'GAME': 0x50b108, 'SAVE': 0x50afe4, 'INSERT': 0x44eb80, 'PASSWORD': 0x41f9e0, 'CODE': 0x44eac0,
                 'LOAD': 0x44fda0, 'SAVEFN': 0x44f7b0, 'BLBACK': 0x44f070, 'LAPTIME': 0x5b22c8,
                 'CREATEFILE': 0x4950cc, 'READFILE': 0x4950b8, 'WRITEFILE': 0x4950d0, 'CLOSE': 0x4950e4,
                 'GETPROC': 0x4950f0, 'GETMOD': 0x495190, 'LSTRCPY': 0x4950f4, 'LSTRCAT': 0x495060, 'LSTRCMPI': 0x49506c}
SAVE_DEFAULTS = 0x4be5f0                # the save's rankings for a fresh start, as the save buffer
CARREC_SLOT = 16 + 17 * 0x80            # carrec: the spec's MD5, a list a course
CARREC_FOLDER = 31                      # a folder name's room in the record files

# --- GENERATED by asm/build.py: BEGIN (do not edit) ---
CARREC_BLOB = bytes.fromhex(
    '5589e55356e8000000005b81eb0a000000a131b1c3a50fb6808c0200008db310'
    '1000008b551083f81e72088db3a026000031d28b4508e8e003000001c6ff7514'
    '52ff750c56b833b1c3a5ffd083c410ff75146a00ff750cff7508b833b1c3a5ff'
    'd083c4105e5b5dc3a131b1c3a583b8000100001e7307b834b1c3a5ffe031c0c3'
    '60e8000000005f81ef86000000a131b1c3a58b88000100008dbf9025000083f9'
    '1e720681c790160000c1e30401df8b1539b1c3a58b770885f6740439d676368b'
    'b00801000089378bb00c01000089770489570851b835b1c3a5ffd083c4048847'
    '0ca131b1c3a58a800401000088470d66c7470e0000618b44241089dac1e2048b'
    '8c02ec1c00008d34023b0d39b1c3a56838b1c3a5c383ea1e724881fa3bb1c3a5'
    '7340515352e8000000005b81eb2a0100002b0532b1c3a52d100d000050832424'
    '7f31d2b9000a0000f7f1c1e0075901c85a69d29008000001d08d8418e0670000'
    '5b59c38db43e180d000050528b1531b1c3a58b920001000089f0e896ffffff89'
    'c65a58c3528d840a180d00008b1531b1c3a58b9200010000e878ffffff5a8b00'
    'c38d9c02100d000050520fb654243089d8e85fffffff89c35a58c38d8c02100d'
    '000050528b1531b1c3a58b920001000089c8e83effffff89c15a58c38d8c1110'
    '0d0000837c240c0074d8c3b836b1c3a5ffd060e8000000005b81ebf80100008b'
    '1532b1c3a58dab101000008d83f8030000e88c010000e8f0030000e8f8050000'
    '8dab500900008b45048db403a02600008b7d00033d32b1c3a58b4d0851807e0c'
    '807311837e08ff740b518b4c2404e8f00100005983c6104975e35983c50c837d'
    '080075c231c989cec1e6048db433203c000089cfc1e704033d32b1c3a581c704'
    'd60000e8430200004183f91172d861c360e8000000005b81eb960200008dab50'
    '0900008b7500033532b1c3a58b4d088dbb101000000fb6460c83e81e83f86273'
    '068dbba0260000037d04518b4d08e8c001000085c07505e8670100005983c610'
    '4975cc83c50c837d080075b731c989cec1e604033532b1c3a581c604d600008d'
    'bb902500000fb6460c83e81e83f86273068dbb203c000089c8c1e00401c7e8a8'
    '0100004183f91172c58b1532b1c3a58dab101000008d8301040000e862000000'
    '8b3532b1c3a5ffb6080d000031c031c903840e0803000081c10001000081f900'
    '0a000072eb8986080d0000b837b1c3a5ffd08b3532b1c3a58f86080d000089f2'
    '8dab101000008d8301040000e811000000e888050000e85a030000e8e6040000'
    '61c3535657515089d689efb940030000ff142431db89d969c9000a00008db40a'
    '100d000089d9c1e1078dbc0d000d0000b920000000ff14244383fb1172d78db2'
    '04d600008dbd80150000b944000000ff142458595f5e5bc3565751f3a5595f5e'
    'c3565751528b068b178916890783c60483c7044975ef5a595f5ec32b0532b1c3'
    'a53d100d0000721a52512d100d000031d2b9000a0000f7f1c1e00705000d0000'
    '595ac35352518b560831db39cb734089d8c1e00439540708770343ebee89c848'
    '39d8761b56575189c1c1e1048d740ff001cfb904000000f3a5595f5e48ebe156'
    '57c1e30401dfb904000000f3a55f5e595a5bc353515231c089fb85c974298b16'
    '3b13751d8b56043b530475158b56083b5308750d668b560c663b530c750340eb'
    '0683c31049ebd35a595bc3518b460885c0741c807e0c8073168b4f0885c97404'
    '39c8730b5657b904000000f3a55f5e59c3515731ff81ff3bb1c3a57321b83ab1'
    'c3a58b44b87885c0740c5056ff1544b1c3a585c0740347ebdc8d471eeb5731ff'
    '3bbbdc0a0000732389f8c1e0058d8403100c00005056ff1544b1c3a585c07403'
    '47ebdd8d8780000000eb2ab8ff00000083ff207320ff83dc0a000089f8c1e005'
    '8d8403100c00005650ff1542b1c3a58d87800000005f59c36a00688000000085'
    'c9750d6a036a006a016800000080eb0b6a026a006a00680000004056ff153cb1'
    'c3a5c35131c9e8cdffffff5983f8ff7426506a008d93e00a000052518d93303d'
    '00005250ff153db1c3a5ff153fb1c3a58b83e00a0000c331c0c351b901000000'
    'e893ffffff5983f8ff741f506a008d93e00a000052518d93303d00005250ff15'
    '3eb1c3a5ff153fb1c3a5c38db3cb0b0000b9a02a0000e888ffffff8dbb303d00'
    '003da01600000f829d000000813f535232520f8591000000837f04010f858700'
    '00008b4f0881f9a0000000777c89cac1e20581c2a016000039d0756d31ed39cd'
    '731c89eec1e6058d743710c6461f00e87dfeffff88842be40a000045ebe089ce'
    'c1e6058d74371051568dbba0260000b9a4050000f3a55e598dbba026000031d2'
    '0fb6470c39c873108a8403e40a00003cff740588470ceb05e80d00000083c710'
    '4281fa6901000072d7c3c70700000000c7470400000000c7470cff000000c747'
    '08ffffffff81fa580100007207c7470800000000c38dbb303d0000c707535232'
    '52c7470401000000b83bb1c3a50383dc0a0000894708c7470c00000000508d7f'
    '1057b90005000031c0f3ab5f31ed81fd3bb1c3a5731bb83ab1c3a58b44a87885'
    'c074085057ff1542b1c3a583c72045ebdd31ed3babdc0a0000731a89e8c1e005'
    '8d8403100c00005057ff1542b1c3a583c72045ebde8db3a026000057b9a40500'
    '00f3a55fb9690100000fb6470c3dff00000074193d80000000730583e81eeb0a'
    '2d80000000053bb1c3a588470c83c7104975d659c1e10581c1a01600008db3cb'
    '0b0000e812feffffc3b83ab1c3a58b44a87885c07441508d83840b0000508d83'
    'de0b0000508d83840b000050ff1542b1c3a5ff1543b1c3a58d83e60b0000508d'
    '83840b000050ff1543b1c3a58db3840b0000b801000000c331ed81fd3bb1c3a5'
    '7363e8a2ffffff85c07457b9c0080000e86efdffff3dc008000075468db3303d'
    '0000813e535232437538837e0401753283c64089ef69ff900800008dbc3be067'
    '000057b920020000f3a55f8d451eb988000000807f0cfe750388470c83c71049'
    '75f145eb95c331ed81fd3bb1c3a50f8389000000e830ffffff85c0747a568dbb'
    '303d0000b91000000031c0f3ab8dbb303d0000c70753523243c7470401000000'
    'b83ab1c3a5ff74a8788d471050ff1542b1c3a589ee69f6900800008db433d067'
    '00008dbb603d0000b924020000f3a58dbb703d00008d451eb98800000038470c'
    '7504c6470cfe83c7104975f15eb9c0080000e8c3fcffff45e96bffffffc38d83'
    'eb0b000050ff1541b1c3a585c0741d8d93f80b00005250ff1540b1c3a585c074'
    '0b6a008d93c40b000052ffd0c390909000000000000000001000000000010000'
    '0001000008000000800100008001000008000000000200000002000008000000'
    '8002000080020000080000000003000000030000100000000004000000040000'
    '1000000000050000000500001000000000060000000600001000000000070000'
    '0007000010000000000800000008000010000000000900000009000010000000'
    '000a0000000a000010000000000b0000000b000010000000000c0000000c0000'
    '10000000100d0000000d00000800000010170000800d00000800000010210000'
    '000e000008000000102b0000800e00000800000010350000000f000008000000'
    '103f0000800f0000080000001049000000100000080000001053000080100000'
    '08000000105d0000001100000800000010670000801100000800000010710000'
    '0012000008000000107b00008012000008000000108500000013000008000000'
    '108f0000801300000800000010990000001400000800000010a3000080140000'
    '0800000010ad0000001500000800000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
    '000000005245434f5244005245434f52445c52414e4b494e472e524543005245'
    '434f52445c002e524543004b45524e454c33322e444c4c004372656174654469'
    '726563746f7279410090909090909090'
)
CARREC_LABELS = {'hook_shared': 0x0, 'pw_gate': 0x68, 'bestlap': 0x80, 's1': 0x163, 's2': 0x184, 's3': 0x1a1, 's4': 0x1bb, 's5': 0x1dc, 'load_hook': 0x1eb, 'save_hook': 0x290, 'tail': 0xc10, 'unk': 0xc10, 'stock': 0x1010, 'new': 0x26a0, 'filebuf': 0x3d30, 'carrec': 0x67d0}
CARREC_MAGICS = {
    'GAME': 0xA5C3B131,
    'SAVE': 0xA5C3B132,
    'INSERT': 0xA5C3B133,
    'PASSWORD': 0xA5C3B134,
    'CODE': 0xA5C3B135,
    'LOAD': 0xA5C3B136,
    'SAVEFN': 0xA5C3B137,
    'BLBACK': 0xA5C3B138,
    'LAPTIME': 0xA5C3B139,
    'FOLDERS': 0xA5C3B13A,
    'NCAR': 0xA5C3B13B,
    'CREATEFILE': 0xA5C3B13C,
    'READFILE': 0xA5C3B13D,
    'WRITEFILE': 0xA5C3B13E,
    'CLOSE': 0xA5C3B13F,
    'GETPROC': 0xA5C3B140,
    'GETMOD': 0xA5C3B141,
    'LSTRCPY': 0xA5C3B142,
    'LSTRCAT': 0xA5C3B143,
    'LSTRCMPI': 0xA5C3B144,
}
# --- GENERATED by asm/build.py: END ---


def md5(data):
    return hashlib.md5(data).hexdigest()


class Image:
    """A PE file's bytes addressed by VA, growing an annex for new data."""

    def __init__(self, data):
        self.buf = bytearray(data)
        self.base = patcher._image_base(self.buf)
        self.relocs = []
        self.moved = {}                 # stock table -> (entry size, its VA in the annex)

    def off(self, va):
        """va's file offset; a moved table's entries are read and written where it moved to."""
        for table, (size, new) in self.moved.items():
            if table <= va < table + size * CARS:
                va += new - table
                break
        return patcher._rva_to_off(self.buf, va - self.base)

    def reloc_rvas(self):
        """The RVAs the relocation directory fixes up (HIGHLOW), and the ones carslot adds."""
        pe = struct.unpack_from('<I', self.buf, 0x3c)[0]
        rel_rva, rel_size = struct.unpack_from('<II', self.buf, pe + 24 + 136)
        out = []
        if rel_size:
            off = patcher._rva_to_off(self.buf, rel_rva)
            end = off + rel_size
            while off + 8 <= end:
                page, size = struct.unpack_from('<II', self.buf, off)
                if not size:
                    break
                for i in range(8, size, 2):
                    entry = struct.unpack_from('<H', self.buf, off + i)[0]
                    if entry >> 12 == 3:
                        out.append(page + (entry & 0xfff))
                off += size
        return out + self.relocs

    def move(self, table, size, fields=None, ends=()):
        """A table of CARS entries to the annex with room for IDS, the new
        entries zero. Every reference into it follows: an exe's `fields`
        (the 4-byte operands, it has no relocations), a DLL's relocated
        dwords; `ends` are the operands that hold the table's end (loop
        bounds). A relocated dword in the table moves with it, the same
        offsets of the new entries get relocations too."""
        new = self.add(self.loaded(table, size * CARS) + bytes(size * (IDS - CARS)))
        if fields is None:
            rvas = set(self.reloc_rvas())
            inside = sorted({(r - (table - self.base)) % size for r in rvas
                             if 0 <= r - (table - self.base) < size * CARS})
            self.relocs += [new - self.base + size * i + o for i in range(IDS) for o in inside]
            fields = [self.base + r for r in rvas
                      if table <= struct.unpack_from('<I', self.buf, patcher._rva_to_off(self.buf, r))[0] < table + size * CARS]
        for va in fields:
            at = patcher._rva_to_off(self.buf, va - self.base)
            value = struct.unpack_from('<I', self.buf, at)[0]
            if not table <= value < table + size * CARS:
                raise ValueError('0x%x: 0x%x is not in the table at 0x%x carslot knows' % (va, value, table))
            struct.pack_into('<I', self.buf, at, new + value - table)
        for va in ends:
            at = patcher._rva_to_off(self.buf, va - self.base)
            if struct.unpack_from('<I', self.buf, at)[0] != table + size * CARS:
                raise ValueError('0x%x: not the end of the table at 0x%x carslot knows' % (va, table))
            struct.pack_into('<I', self.buf, at, new + size * IDS)
        self.moved[table] = (size, new)
        return new

    def at(self, table, i, size=4):
        """The VA of a table's entry i: in the annex once the table moved, which
        the ids from CARS on need (their stock place is the next table's)."""
        if table in self.moved:
            return self.moved[table][1] + self.moved[table][0] * i
        if i >= CARS:
            raise ValueError('0x%x: no entry %d before the tables move' % (table, i))
        return table + size * i

    def loaded(self, va, n):
        """n bytes at va as the loader maps them: past a section's raw data
        (its uninitialised tail, .bss) zeros, not the next section's bytes."""
        pe = struct.unpack_from('<I', self.buf, 0x3c)[0]
        nsec = struct.unpack_from('<H', self.buf, pe + 6)[0]
        table = pe + 24 + struct.unpack_from('<H', self.buf, pe + 20)[0]
        rva = va - self.base
        for i in range(nsec):
            vsize, sva, rsize, roff = struct.unpack_from('<IIII', self.buf, table + i * 40 + 8)
            if sva <= rva < sva + max(vsize, rsize):
                have = max(0, min(n, rsize - (rva - sva)))
                return bytes(self.buf[roff + rva - sva:roff + rva - sva + have]) + bytes(n - have)
        raise ValueError('0x%x is in no section' % va)

    def copy_entry(self, table, src, dst):
        size = self.moved[table][0] if table in self.moved else 4
        self.write(self.at(table, dst, size), self.read(self.at(table, src, size), size))

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
        pe = struct.unpack_from('<I', self.buf, 0x3c)[0]
        rel_size = struct.unpack_from('<I', self.buf, pe + 24 + 140)[0]
        if self.relocs and rel_size:
            try:
                patcher._add_relocations(self.buf, self.relocs)
            except ValueError:          # no room left in .reloc: the whole directory to the annex
                rvas = sorted(set(self.reloc_rvas()))
                self.relocs = []
                blocks = b''
                for page in sorted({rva & ~0xfff for rva in rvas}):
                    entries = [0x3000 | (rva & 0xfff) for rva in rvas if rva & ~0xfff == page]
                    entries += [0] * (len(entries) % 2)
                    blocks += struct.pack('<II', page, 8 + 2 * len(entries)) + struct.pack('<%dH' % len(entries), *entries)
                at = self.add(blocks)
                struct.pack_into('<II', self.buf, pe + 24 + 136, at - self.base, len(blocks))
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


def widen(exe, dlls, slots, log):
    """The per-car tables to the annex with IDS entries; each new slot a
    copy of its perf car with a folder of its own and its menu entry, on
    the Corolla's bit (open from the start)."""
    msel, record, replay, champagn = (dlls[n] for n in (MSELECT, RECORD, REPLAY, CHAMPAGN))
    for table, size, fields in EXE_TABLES:
        exe.move(table, size, fields)
    for site in LAMP_COUNTS:
        if exe.u32(site) != 13 * CARS:
            raise ValueError('%s: 0x%x is not the count of lamp models carslot knows' % (EXE, site))
        exe.put(site, 13 * IDS)
    loader_flags(exe)
    for site, op in RECORD_BOUNDS:
        if exe.read(site, 1)[0] != op:
            raise ValueError('%s: 0x%x is not the records\' bound carslot knows' % (EXE, site))
        exe.write(site, b'\x90\x90')
    for img, tables in ((msel, MSELECT_TABLES), (record, RECORD_TABLES), (replay, REPLAY_TABLES),
                        (champagn, CHAMPAGN_TABLES)):
        for table, size, _copy, ends in tables:
            img.move(table, size, ends=ends)
    for site, op in RECORD_DLL_BOUNDS:
        if record.read(site, 1)[0] != op:
            raise ValueError("%s: 0x%x is not the records' bound carslot knows" % (RECORD, site))
        record.write(site, b'\x90\x90')
    if champagn.read(PODIUM_BOUND, 1) != b'\x1d':
        raise ValueError("%s: 0x%x is not the podium's bound carslot knows" % (CHAMPAGN, PODIUM_BOUND))
    champagn.write(PODIUM_BOUND, bytes([IDS - 1]))         # a signed byte: IDS is 128 at most
    for site in MSELECT_COUNTS:
        if msel.u32(site) != CARS:
            raise ValueError('%s: 0x%x is not the count of 3D cars carslot knows' % (MSELECT, site))
        msel.put(site, IDS)
    for site, stock, ours in MENU_CURSOR:
        if msel.read(site, len(stock) // 2) != bytes.fromhex(stock):
            raise ValueError("%s: 0x%x is not the menu cursor's code carslot knows" % (MSELECT, site))
        msel.write(site, bytes.fromhex(ours))
    entry = CARS
    for slot, conf in sorted(slots.items()):
        if slot < CARS:
            continue
        perf = conf.get('perf')
        if perf is None or not 0 <= perf < CARS:
            raise ValueError('car %d: a car from 30 on starts as a copy of a stock one: "perf" 0-29' % slot)
        if not isinstance(conf.get('folder'), str):
            raise ValueError('car %d: a car from 30 on needs its "folder", BINDATA\\<folder> beside the slot file' % slot)
        name = conf['folder'].upper()
        if not 0 < len(name) <= CARREC_FOLDER or not all(c.isalnum() or c in '_-' for c in name):
            raise ValueError('car %d: "folder" is %d letters, digits, _ or - at most (its records are RECORD\\<folder>.REC)' % (slot, CARREC_FOLDER))
        for table, size, _fields in EXE_TABLES:
            if table not in EXE_OWN:
                exe.copy_entry(table, perf, slot)
        exe.put(exe.at(0x4bc56c, slot, 4), slot)
        exe.put(exe.at(FOLDERS, slot, 4), exe.add(name.encode('latin-1') + b'\0'))
        low = name.lower().encode('latin-1')
        exe.write(exe.at(0x4ccf48, slot, 12), struct.pack('<3I', *(exe.add(s + b'\0') for s in (low + b'.bin', low, low + b'.txb'))))
        for img, tables in ((msel, MSELECT_TABLES), (record, RECORD_TABLES), (replay, REPLAY_TABLES),
                            (champagn, CHAMPAGN_TABLES)):
            for table, size, copy, _ends in tables:
                if copy:
                    img.copy_entry(table, perf, slot)
        for rel, table in DLL_FOLDERS.items():
            img = dlls[rel]
            img.put(img.at(table, slot, 4), img.add(name.encode('latin-1') + b'\0'))
        msel.write(msel.at(MENU, entry, 8), struct.pack('<II', 1, slot))
        entry += 1
    log('carslot: the tables moved, room for ids 0-%d' % (IDS - 1))


def loader_flags(exe):
    """The race's loading sequence (vtable 0x49b154) marks each car id it has
    set up in 30 dwords of its own (+0x1c), cleared when it is built; the
    first time an id comes it gets its body textures (0x41aff0). An id from
    30 on marks the fields past them, which the next race finds set and the
    car keeps the last race's texture handles. The marks go to IDS dwords
    in the annex."""
    sites = ((0x41affa, bytes.fromhex('8b4c861c85c9')),                 # mov ecx, [esi+eax*4+0x1c]; test ecx, ecx
             (0x41b010, bytes.fromhex('c744861c01000000')),             # mov dword [esi+eax*4+0x1c], 1
             (0x41ab72, bytes.fromhex('b91e0000008d7b1cf3ab')))         # mov ecx, 30; lea edi, [ebx+0x1c]; rep stosd
    for site, code in sites:
        if exe.read(site, len(code)) != code:
            raise ValueError('%s: 0x%x is not the loading sequence carslot knows' % (EXE, site))
    marks = exe.add(bytes(4 * IDS))
    d = lambda v: struct.pack('<I', v)          # noqa: E731

    def stub(code, back=None):
        at = exe.add(bytes(len(code) + 5), chars=patcher.CODE_SECTION | DATA_SECTION)
        if back is not None:
            code += b'\xe9' + struct.pack('<i', back - (at + len(code) + 5))
        exe.write(at, code)
        return at

    def jump(site, to, size, op=b'\xe9'):
        exe.write(site, op + struct.pack('<i', to - (site + 5)) + b'\x90' * (size - 5))

    # test: mov ecx, [eax*4+marks]; test ecx, ecx; jne 0x41b03d; back to 0x41b002
    test = stub(b'\x8b\x0c\x85' + d(marks) + b'\x85\xc9\x0f\x85' + struct.pack('<i', 0), 0x41b002)
    exe.write(test + 11, struct.pack('<i', 0x41b03d - (test + 15)))
    jump(0x41affa, test, 6)
    mark = stub(b'\xc7\x04\x85' + d(marks) + d(1), 0x41b018)       # mov dword [eax*4+marks], 1
    jump(0x41b010, mark, 8)
    clear = stub(b'\xbf' + d(marks) + b'\xb9' + d(IDS) + b'\xf3\xab'     # mov edi, marks; mov ecx, IDS; rep stosd
                 + b'\x8d\xbb\x94\x00\x00\x00\xc3')                      # lea edi, [ebx+0x94]; ret
    jump(0x41ab72, clear, 10, b'\xe8')


def records(exe, slots, log):
    """The records of the ids from 30 on (asm/carrec.asm): kept out of
    SR2_SAVE.DAT, in RECORD\\RANKING.REC and RECORD\\<FOLDER>.REC. Its
    buffers follow the code: STOCK zero (the load fills it), NEW every
    entry empty, and a carrec slot per id from 30 to the last new one
    with that car's spec MD5 and its perf car's fresh-start lists."""
    for site, target, _hook in CARREC_CALLS:
        if exe.read(site, 1) != b'\xe8' or site + 5 + struct.unpack('<i', exe.read(site + 1, 4))[0] != target:
            raise ValueError('%s: 0x%x is not the call of 0x%x carslot knows' % (EXE, site, target))
    for site, code, _stub in CARREC_LISTS + (CARREC_BESTLAP + (None,),):
        if exe.read(site, len(code) // 2) != bytes.fromhex(code):
            raise ValueError("%s: 0x%x is not the records' code carslot knows" % (EXE, site))
    last = max(slot for slot in slots if slot >= CARS)
    ncar = last - CARS + 1
    lab = CARREC_LABELS
    code = bytearray(CARREC_BLOB)
    values = dict(CARREC_VALUES, FOLDERS=exe.at(FOLDERS, 0, 4), NCAR=ncar)
    for name, magic in CARREC_MAGICS.items():
        code = code.replace(struct.pack('<I', magic), struct.pack('<I', values[name]))
    shadow = lab['new'] - lab['stock']
    listed = 0x1580 // 16
    new = (struct.pack('<4I', 0, 0, 0xffffffff, 0xff) * listed +
           struct.pack('<4I', 0, 0, 0, 0xff) * (shadow // 16 - listed))
    carrec = bytearray()
    for slot in range(CARS, last + 1):
        if slot not in slots:
            carrec += bytes(CARREC_SLOT)
            continue
        carrec += hashlib.md5(exe.read(exe.at(SPEC, slot, SPEC_SIZE), SPEC_SIZE)).digest()
        index = exe.u32(exe.at(0x4cedc4, slot, 4))
        for course in range(17):
            carrec += exe.read(SAVE_DEFAULTS + 0xd10 + course * 0xa00 + index * 0x80, 0x80)
    blob = (bytes(code) + bytes(lab['stock'] - lab['tail']) + bytes(shadow) + new
            + bytes(lab['carrec'] - lab['filebuf']) + bytes(carrec))
    at = exe.add(blob, chars=patcher.CODE_SECTION | DATA_SECTION)
    for site, _target, hook in CARREC_CALLS:
        exe.write(site, b'\xe8' + struct.pack('<i', at + lab[hook] - (site + 5)))
    for site, stock, stub in CARREC_LISTS:
        exe.write(site, b'\xe8' + struct.pack('<i', at + lab[stub] - (site + 5)) + b'\x90' * (len(stock) // 2 - 5))
    site, stock = CARREC_BESTLAP
    exe.write(site, b'\xe9' + struct.pack('<i', at + lab['bestlap'] - (site + 5)) + b'\x90' * (len(stock) // 2 - 5))
    log('carslot: the records of ids 30-%d go to RECORD\\, not SR2_SAVE.DAT' % last)


def menu_unlock(msel, slots):
    """Each menu builder's start calls a stub that loads its unlock mask
    with the slots' bits ORed in, as the instructions it replaces did."""
    bits = struct.pack('<I', sum(1 << slot for slot in slots if slot < CARS))
    for site, code in MENU_BUILDERS:
        if msel.read(site, len(code)) != code:
            raise ValueError('MSelect.dll: not the menu builder carslot knows at 0x%x' % site)
    stubs = (b'\x58\x8b\x5c\x24\x0c\x81\xcb' + bits + b'\x55\xff\xe0',    # pop eax; mov ebx, [esp+0xc]; or ebx; push ebp; jmp eax
             b'\x8b\x5c\x24\x1c\x81\xcb' + bits + b'\x8b\x6c\x24\x18\xc3')  # mov ebx, [esp+0x1c]; or ebx; mov ebp, [esp+0x18]; ret
    for (site, code), stub in zip(MENU_BUILDERS, stubs):
        at = msel.add(stub, chars=patcher.CODE_SECTION | DATA_SECTION)
        msel.write(site, b'\xe8' + struct.pack('<i', at - (site + 5)) + b'\x90' * (len(code) - 5))


def ring_shape(msel):
    """The ring of photos in the shape of 19 cars at any count (see RING)."""
    for site, count in RING:
        code = bytes.fromhex('db47') + bytes([count]) + bytes.fromhex('83c408d825') + struct.pack('<I', RING_8)
        if msel.read(site, len(code)) != code:
            raise ValueError('MSelect.dll: not the ring carslot knows at 0x%x' % site)
        msel.write(site, bytes.fromhex('90909083c408d905') + struct.pack('<I', RING_11))


def uv_of(x, y, w, h, size=256):
    return x / size, y / size, (x + w) / size, (y + h) / size


# The run

class Game:
    def __init__(self, dest):
        self.dest = dest
        path = os.path.join(dest, STATE)
        self.state = json.load(open(path)) if os.path.isfile(path) else {'files': {}, 'created': {}}
        self.state.setdefault('dirs', [])
        self.data = {}
        self.created = {}

    def ours(self, rel):
        """Free for carslot to write: not there, or there from its last run."""
        return not os.path.isfile(self.path(rel)) or rel.upper() in {key.upper() for key in self.state['created']}

    def copied(self, rel):
        """This run's copy of rel, matched as Windows matches names (any case), or None."""
        for key, data in self.created.items():
            if key.upper() == rel.upper():
                return data
        return None

    def exists(self, rel):
        return self.copied(rel) is not None or os.path.isfile(self.path(rel))

    def read(self, rel):
        """A game file as this run leaves it: what it copies in, else what is there."""
        if self.copied(rel) is not None:
            return self.copied(rel)
        with open(self.path(rel), 'rb') as fh:
            return fh.read()

    def copy_in(self, src, rel):
        """src (a file) to the game's rel, unless the game has a file there of its own:
        False then, and the game's stays."""
        if not self.ours(rel):
            return False
        with open(src, 'rb') as fh:
            self.created[rel] = fh.read()
        return True

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
        self.prune()
        for rel, data in created.items():
            self.make_dirs(os.path.dirname(rel.replace('\\', os.sep)))
            with open(self.path(rel), 'wb') as fh:
                fh.write(data)
            self.state['created'][rel] = md5(data)
            log('carslot: %s written' % rel)
        with open(os.path.join(self.dest, STATE), 'w') as fh:
            json.dump(self.state, fh, indent=1)

    def make_dirs(self, rel):
        """The folders up to rel, each carslot makes noted for prune."""
        if not rel or os.path.isdir(os.path.join(self.dest, rel)):
            return
        self.make_dirs(os.path.dirname(rel))
        os.mkdir(os.path.join(self.dest, rel))
        self.state['dirs'].append(rel.replace(os.sep, '\\'))

    def prune(self, log=None):
        """The folders carslot made, deepest first, once nothing is left in them."""
        for rel in sorted(self.state['dirs'], key=len, reverse=True):
            path = self.path(rel)
            if os.path.isdir(path) and not os.listdir(path):
                os.rmdir(path)
                if log:
                    log('carslot: %s removed' % rel)
            if not os.path.isdir(path):
                self.state['dirs'].remove(rel)


def check(exe):
    for slot, folder in SLOTS.items():
        if exe.cstr(exe.u32(exe.at(FOLDERS, slot, 4))) != folder:
            raise ValueError('%s: not the European or MediaKite exe (folder %d is not %s)' % (EXE, slot, folder))


def rival_set(exe, slot, rival):
    """The set whose rotation starts at `rival`, the slot's own if it does."""
    rotation = [exe.u32(ROTATION + 4 * i) for i in range(ROTATION_CARS)]
    if rival not in rotation:
        raise ValueError('rival %r: not in the rotation %s' % (rival, rotation))
    first = rotation.index(rival)
    own = exe.u32(RIVAL_SET + 4 * exe.u32(exe.at(RIVAL_BASE, slot, 4)))
    sets = [own] + list(range(OWN_CAR_SETS, RIVAL_SETS))
    for s in sets:
        if exe.u32(RIVAL_START + 4 * s) == first:
            return s
    raise ValueError('rival %d: no set starts the rotation at it' % rival)


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
        exe.put(exe.at(TACHO, slot, 4), kind)
    for t, (old, _size, sites) in zip(tables, TACHO_TABLES):
        new = exe.add(bytes(t))
        for site, delta in sites:
            ins = exe.read(site, 12)
            at = ins.find(struct.pack('<I', old + delta))
            if at < 1:
                raise ValueError('%s: 0x%x does not read 0x%x' % (EXE, site, old + delta))
            exe.write(site + at, struct.pack('<I', new + delta))
    return taco


def select_windows(mdl):
    """A race model's windows (the meshes on texture 2) drawn as every
    stock car select model draws them: draw options 0x07 and 1.0 where
    the race has 0x13 and 0.5, the first window's material c8c8c896
    14141400 where the race has 98989896 87878700 (docs/CARS.md)."""
    mdl = bytearray(mdl)
    rel = struct.unpack_from('<I', mdl, 8)[0]
    while rel >= 0x80:
        pointers, _draw, _index, texture = struct.unpack_from('<3Ii', mdl, rel - 0x60)
        child, sibling, no_mesh = struct.unpack_from('<3I', mdl, rel)
        if texture == 2 and not no_mesh:
            struct.pack_into('<B', mdl, pointers + 0x20, 0x07)
            struct.pack_into('<4f', mdl, pointers + 0x28, 1.0, 1.0, 1.0, 1.0)
            material = struct.unpack_from('<I', mdl, pointers + 8)[0]
            if mdl[material:material + 8] == bytes.fromhex('9898989687878700'):
                mdl[material:material + 8] = bytes.fromhex('c8c8c89614141400')
        if not child and not sibling:
            break
        rel -= 0x80
    return bytes(mdl)


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
        part = bytearray(exe.read(HUD_ICON_PARTS + 0x34 * exe.u32(exe.at(HUD_ICON, slot, 4)), 0x34))
        struct.pack_into('<I', part, 0, uv0 + i)
        parts += part
    part0 = exe.add_indexed(parts, HUD_ICON_PARTS, 0x34)
    lo = HUD_ICON_PARTS + 0x34 * part0
    for i, (slot, _img) in enumerate(icons):
        exe.put(exe.at(HUD_ICON, slot, 4), part0 + i)

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
    if adv.read(ADV_RELEASE, 6) not in (b'\x6a\x5d\x50\xff\x51\x2c', b'\x90' * 6):   # stock, or padattract's
        raise ValueError('%s: 0x%x is not the release carslot knows' % (ADVTELOP, ADV_RELEASE))
    pages = txr_pages(txt)
    if pages[ADV_PAGE][:2] != (2, 256):
        raise ValueError('%s: page %d is not 256x256 1555' % (ADV_TXT, ADV_PAGE))
    start = 0x1000 + sum(p[2] for p in pages[:ADV_PAGE])
    # below the last row in use: the patcher's padattract letters rows 176-194
    free = max([ADV_FREE] + [row + 1 for row in range(ADV_FREE, 256) if any(txt[start + 512 * row:start + 512 * (row + 1)])])
    spots = [(86 * (i % 3), free + 1 + 32 * (i // 3)) for i in range(len(icons))]
    if spots and spots[-1][1] + h > 256:
        raise ValueError('at most %d demo icons' % (3 * ((256 - free) // 32)))
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
        adv.put(adv.at(ADV_ICON, slot, 4), sprite(adv, adv.u32(adv.at(ADV_ICON, slot, 4)), table, i))
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
    carmdl, cartex, refmdl = (bytearray(game.base(rel)) for rel in (B_CARMDL, B_CARTEX, B_REFMDL))
    taco = game.base(TACO)
    created = game.created          # what the run copies or makes, new files of carslot's
    pics = {what: [] for what in SIZES}
    new_tachos = []
    if any(slot >= CARS for slot in slots):
        widen(exe, {MSELECT: msel, RECORD: record, REPLAY: replay, CHAMPAGN: champagn}, slots, log)

    for slot, conf in sorted(slots.items()):
        folder = SLOTS.get(slot) or conf['folder'].upper()
        if 'folder' in conf:                    # the car's own files, BINDATA\<folder> beside the slot file
            src = os.path.join(here, 'BINDATA', conf['folder'])
            if not os.path.isdir(src):
                raise ValueError('car %d: no folder %s' % (slot, src))
            kept = 0
            for root, _dirs, names in os.walk(src):
                for name in sorted(names):
                    sub = os.path.relpath(os.path.join(root, name), src).replace(os.sep, '\\')
                    kept += not game.copy_in(os.path.join(root, name), 'BINDATA\\%s\\%s' % (folder, sub))
            if kept:
                log('carslot: BINDATA\\%s: %d files there already, not carslot\'s, kept' % (folder, kept))
        for i in range(CARS):                   # on the menu by its own bit, unlocked by menu_unlock
            if msel.u32(MENU + 8 * i + 4) == slot:
                msel.put(MENU + 8 * i, 1 << slot)
        if 3 <= slot <= 26:                     # back on the menu as itself, not the car it stood in for (26: 11)
            if msel.read(CAR_REMAP + slot - 3, 1)[0] > 6:
                raise ValueError('MSelect.dll: not the id cases carslot knows at 0x%x' % CAR_REMAP)
            msel.write(CAR_REMAP + slot - 3, b'\x06')
        perf = conf.get('perf')
        if perf is not None:
            exe.write(exe.at(SPEC, slot, SPEC_SIZE), exe.read(SPEC + perf * SPEC_SIZE, SPEC_SIZE))
            exe.put(exe.at(CURVE, slot, 4), exe.u32(CURVE + 4 * perf))
            for table in HUD:
                exe.put(exe.at(table, slot, 4), exe.u32(table + 4 * perf))
            msel.write(msel.at(GEARBOX, slot, 16), msel.read(GEARBOX + 16 * perf, 16))
        if 'spec' in conf:
            with open(os.path.join(here, conf['spec'])) as fh:
                exe.write(exe.at(SPEC, slot, SPEC_SIZE), spec_block(json.load(fh)['values']))
        for key, table in (('sound', SOUND), ('tacho', TACHO)):
            donor = conf.get(key, perf)
            if isinstance(donor, dict):         # a rev counter of its own, made after the loop
                new_tachos.append((slot, donor, perf))
            elif donor is not None:
                exe.put(exe.at(table, slot, 4), exe.u32(table + 4 * donor))
        if 'hud_icon' in conf:                  # a picture of a car, so not perf's by default
            exe.put(exe.at(HUD_ICON, slot, 4), exe.u32(HUD_ICON + 4 * conf['hud_icon']))
        desert = conf.get('desert')
        if isinstance(desert, bool):
            exe.put(exe.at(DESERT_KIT, slot, 4), exe.add(struct.pack('<%di' % len(DESERT_LISTS[desert]), *DESERT_LISTS[desert])))
            if desert and not game.exists('BINDATA\\%s\\desert.mdl' % folder):
                log('carslot: car %d: no BINDATA\\%s\\desert.mdl' % (slot, folder))
        elif desert is not None:
            exe.put(exe.at(DESERT_KIT, slot, 4), exe.u32(DESERT_KIT + 4 * desert))
            exe.put(exe.at(DESERT_GLOW, slot, 4), exe.u32(DESERT_GLOW + 4 * desert))
        if 'rival' in conf:
            exe.put(exe.at(RIVAL_SET, slot, 4), rival_set(exe, slot, conf['rival']))
            exe.put(exe.at(RIVAL_BASE, slot, 4), slot)
        if 'gearbox' in conf:
            msel.write(msel.at(GEARBOX, slot, 16), struct.pack('<4I', *conf['gearbox']))
        if 'name' in conf:
            text = conf['name'].encode('latin-1') + b'\0'
            at = exe.add(text)
            for table in NAMES:
                exe.put(exe.at(table, slot, 4), at)
            replay.put(replay.at(REPLAY_NAME, slot, 4), replay.add(text))
        crew = conf.get('crew')
        if isinstance(crew, int):
            if not 0 <= crew < CARS:
                raise ValueError('crew %d: no such car' % crew)
            champagn.put(champagn.at(CREW, slot, 4), champagn.u32(CREW + 4 * crew))
        elif crew is not None:
            if not (crew.isascii() and crew.isalnum() and len(crew) <= 16):
                raise ValueError('crew %r: letters and digits, 16 at most' % crew)
            champagn.put(champagn.at(CREW, slot, 4), champagn.add(crew.upper().encode() + b'\0'))
            src = os.path.join(here, 'BINDATA', 'CHAMPAGN')
            mine = {name.upper(): name for name in (os.listdir(src) if os.path.isdir(src) else ())}
            for fname in CREW_FILES:
                rel = 'BINDATA\\CHAMPAGN\\' + fname % crew
                if (fname % crew).upper() in mine:      # BINDATA\CHAMPAGN beside the slot file, copied in
                    if not game.copy_in(os.path.join(src, mine[(fname % crew).upper()]), rel):
                        log('carslot: %s is there already, kept' % rel)
                if not game.exists(rel):
                    log('carslot: car %d: no BINDATA\\CHAMPAGN\\%s' % (slot, fname % crew))
        height = conf.get('crew_height')
        if isinstance(height, int):
            if not 0 <= height < CARS:
                raise ValueError('crew_height %d: no such car' % height)
            f32 = lambda va: struct.unpack('<f', champagn.read(va, 4))[0]
            up = f32(CREW_UP_ESCORT if height == 2 else CREW_UP)
            height = f32(CREW_HEIGHT + 4 * height) + up - f32(CREW_UP)
        if height is not None:
            champagn.write(champagn.at(CREW_HEIGHT, slot, 4), struct.pack('<f', height))
        if 'podium_run' in conf:
            run = conf['podium_run']
            if not 0 <= run < CARS:
                raise ValueError('podium_run %d: no such car' % run)
            champagn.write(champagn.at(PODIUM_RUN, slot, 1), champagn.read(PODIUM_RUN + run, 1))
        if slot >= CARS and 'icon_demo' in conf:
            raise ValueError('car %d: the advertise demo runs the stock cars, no icon_demo from 30 on' % slot)
        for what in SIZES:
            if what in conf:
                pics[what].append((slot, open_png(os.path.join(here, conf[what]), what)))
        if conf.get('model'):
            parts = conf['model'] if isinstance(conf['model'], dict) else {}
            if 'mdl' in parts:
                with open(os.path.join(here, parts['mdl']), 'rb') as fh:
                    mdl = fh.read()
            else:
                mdl = game.read('BINDATA\\%s\\r_%s.mdl' % (folder, folder.lower()))
            if 'mdl' not in parts:
                mdl = select_windows(mdl)
            if 'texture' in parts:
                with open(os.path.join(here, parts['texture']), 'rb') as fh:
                    data = fh.read()
                tex = [data[0x1000:0x1000 + 256 * 256 * 2], data[0x1000 + 256 * 256 * 2:0x1000 + (256 * 256 + 64 * 64) * 2]]
            else:
                tex = []
                for fname, size in (('body.txr', 256), ('ta_tire.txr', 64)):
                    data = game.read('BINDATA\\%s\\%s' % (folder, fname))
                    tex.append(data[0x1000:0x1000 + size * size * 2])
            if len(tex[0]) != 256 * 256 * 2 or len(tex[1]) != 64 * 64 * 2:
                raise ValueError('car %d: the texture is short of a 256x256 body and a 64x64 tyre' % slot)
            reflection = parts.get('reflection')
            if isinstance(reflection, int):
                if not 0 <= reflection < CARS:
                    raise ValueError('reflection %d: no such car' % reflection)
                msel.write(msel.at(REFMDL, slot, 8), msel.read(REFMDL + 8 * reflection, 8))
            elif reflection is not None:
                with open(os.path.join(here, reflection), 'rb') as fh:
                    ref = fh.read()
                refmdl += bytes(-len(refmdl) % 0x20)
                msel.write(msel.at(REFMDL, slot, 8), struct.pack('<II', len(refmdl), len(ref)))
                refmdl += ref
            head = bytearray(0x1000)
            head[:8] = b'RTEX' + struct.pack('<I', 2)
            struct.pack_into('<4I', head, 16, 0, 256, len(tex[0]), 0)
            struct.pack_into('<4I', head, 32, 0, 64, len(tex[1]), 0)
            carmdl += bytes(-len(carmdl) % 0x20)
            msel.write(msel.at(CARMDL, slot, 8), struct.pack('<II', len(carmdl), len(mdl)))
            carmdl += mdl
            cartex += bytes(-len(cartex) % 0x1000)
            blob = bytes(head) + tex[0] + tex[1]
            msel.write(msel.at(CARTEX, slot, 8), struct.pack('<II', len(cartex), len(blob)))
            cartex += blob

    count = IDS if CARTEX in msel.moved else CARS
    models = sum(msel.read(msel.at(CARTEX, i, 8), 8) != bytes(8) for i in range(count))
    if models > SELECT_CARS:
        raise ValueError('%d cars with a 3D car on the car select, its texture slots hold %d' % (models, SELECT_CARS))
    if slots:
        menu_unlock(msel, slots)
        ring_shape(msel)
    for mine, theirs in ((EXE_CARMDL, CARMDL), (EXE_CARTEX, CARTEX), (EXE_REFMDL, REFMDL)):
        if exe.read(mine, 8) != msel.read(theirs, 8):
            raise ValueError('%s: 0x%x is not the copy of MSelect\'s 0x%x carslot knows' % (EXE, mine, theirs))
        for slot in slots:
            exe.write(exe.at(mine, slot, 8), msel.read(msel.at(theirs, slot, 8), 8))

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
            at = sprite(msel, msel.u32(msel.at(tables[0], slot, 4)), table, index)
            for t in tables:
                msel.put(msel.at(t, slot, 4), at)

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
                donor = img.u32(img.at(tables[kind], slot, 4))
                img.put(img.at(tables[kind], slot, 4), sprite(img, donor, table, i))

    # The rankings' full names, by id.
    titles = [(slot, conf['full_name']) for slot, conf in sorted(slots.items()) if 'full_name' in conf]
    if titles:
        texts = [record.add(text.encode('latin-1') + b'\0') for _s, text in titles]
        first = record.add_indexed(struct.pack('<%dI' % len(texts), *texts), RECORD_TITLES, 4,
                                   range(0, 4 * len(texts), 4))
        index = [record.u32(record.at(RECORD_INDEX, i)) if i < 0x1d or (i >= CARS and RECORD_INDEX in record.moved)
                 else 0 for i in range(IDS)]
        for i, (slot, _text) in enumerate(titles):
            index[slot] = first + i
        table = record.add(struct.pack('<%dI' % IDS, *index))
        for site in TITLE_SITES:
            code = record.read(site, 12)
            index_at = record.moved[RECORD_INDEX][1] if RECORD_INDEX in record.moved else RECORD_INDEX
            if code[2] != 0x1d or code[3] != 0x7d or code[5] != 0x8b or struct.unpack_from('<I', code, 8)[0] != index_at:
                raise ValueError('Record.dll: not the title lookup at 0x%x' % site)
            record.write(site + 2, bytes([min(IDS, 0x7f)]))     # a signed byte: from 127 on, 0's
            record.put(site + 8, table)

    # The demo run under the spec card:CAR\<car>.REP, a copy of the replay
    # car's with the id in it; the demo's rewrite of 26 to 11 goes.
    for slot, conf in sorted(slots.items()):
        donor = conf.get('replay', conf.get('perf'))
        rel = 'BINDATA\\CAR\\%s.REP' % (SLOTS.get(slot) or slots[slot]['folder'].upper())
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
        exe.put(exe.at(PROFILE, slot, 4), number)
        champagn.put(champagn.at(CHAMPAGN_PROFILE, slot, 4), number)
        number += 1

    if new_tachos:
        taco = new_kinds(exe, taco, new_tachos, here)
    if pics['icon_2p']:                 # after the new kinds: its page is TACO.TXR's last
        taco = icons_2p(exe, taco, pics['icon_2p'])
    if pics['icon_demo']:
        adv_txt = demo_icons(adv, adv_txt, pics['icon_demo'])
    if any(slot >= CARS for slot in slots):     # after the specs: their MD5s go in
        records(exe, slots, log)

    outputs = {EXE: exe.done(), MSELECT: msel.done(), RECORD: record.done(), REPLAY: replay.done(),
               CHAMPAGN: champagn.done(), ADVTELOP: adv.done(), ADV_TXT: adv_txt, B_CARMDL: bytes(carmdl), B_CARTEX: bytes(cartex),
               B_REFMDL: bytes(refmdl), TACO: taco}
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
    game.prune(log)
    for rel in game.state['dirs']:
        log('carslot: %s kept, not empty' % rel)
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
        if slot not in SLOTS and not CARS <= slot < IDS:
            raise SystemExit('carslot: %d is not one of %s or %d-%d' % (slot, ', '.join(map(str, SLOTS)), CARS, IDS - 1))
        slots[slot] = value
    apply(Game(argv[1]), slots, os.path.dirname(os.path.abspath(argv[2])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

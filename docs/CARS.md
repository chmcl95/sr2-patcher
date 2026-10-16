# Cars

What a car is to the game, where its tables are, and what adding one
would take. Addresses are the European build's; the MediaKite exe has
the same data addresses (NOTES.md, *The Japanese releases*), and the
DLLs are the same files.

## The car id

A car is an index 0-29, the same number everywhere: the exe, every
screen DLL, the loader, the replays. There is no car count anywhere;
each table simply has 30 entries and nothing checks the index.

| Id | Dir | Menu | | Id | Dir | Menu |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | `COROLLA` | yes | | 15 | `ST185` | yes |
| 1 | `PGT306` | yes | | 16 | `LANEVO3` | yes |
| 2 | `ESCORT` | yes | | 17 | `LANEVO4` | yes |
| 3 | `IMPREZA` | yes | | 18 | `CARISMA` | no, no dir |
| 4 | `LANCER` | yes | | 19 | `IMP_WRX` | yes |
| 5 | `STRATOS0` | yes | | 20 | `REPST185` | yes |
| 6 | `CELICA` | yes | | 21 | `STR19750` | yes |
| 7 | `DELTA` | yes | | 22 | `COR_TEIN` | yes |
| 8 | `RALLY0` | yes | | 23 | `STRATOS1` | no |
| 9 | `DELTA16V` | yes | | 24 | `STR19751` | no |
| 10 | `FIAT` | yes | | 25 | `RALLY1` | no |
| 11 | `PGT2050` | yes | | 26 | `PGT2051` | no, no dir |
| 12 | `PGT106` | yes | | 27 | `LANEVO6` | yes |
| 13 | `ALPINE` | yes | | 28 | `IMP_99` | yes |
| 14 | `MEGANE` | yes | | 29 | `FOCUS` | no, no dir |

`ESCORT`'s folder holds `focus_*.wav`; its display name in the exe and
ReplayGallery is `KEROLLA WRC`.

## The menu (`MSelect.dll`)

`0x100b5970` (file `0xb3970`): 30 pairs `{mask, id}`, ending at
`0x100b5a60`. Each mask is one bit, 0-29, all different; bits 30 and 31
are unused. Two builders walk it (`0x10002a80`, `0x10008c00`), keep the
entries whose bit is in the unlock mask (from `0x10004c20`), and write
the ids into a 30-dword list (`0x1010f33c`, `0x1010f3e8`), the count at
`+0x20` of the screen object. Five screens call `0x10008c00`.

`car_extend/MSelect.dll` changes three masks to 1, the bit of the Corolla,
which is open from the start: CARISMA (`0xb3a18`), PGT2051 (`0xb3a50`) and FOCUS
(`0xb3a58`). Nothing else differs. The menu then offers 27 cars; ids
18, 26 and 29 exist in every table below - 18 mostly a copy of the
Lancer, 26 of the 205, 29 with entries of its own. With no folder they
need one before a race loads.

## Tables with one entry per car

Found by a scan for indexed tables exactly 30 entries long, then each
read at its use. The scan does not see arrays built at run time, so
this list is a floor.

### `SEGA RALLY 2.exe`

The car id of player `n` is at `[0x50b108] + n*0x30 + 0x100`.

| Address | Entry | What | Read at |
| --- | --- | --- | --- |
| `0x495a98` | 0x2a8 | **the car's spec**: 0xaa dwords copied into the car object at `+0xac` | `0x4051b6` |
| `0x4a9d60` | 4 | a pointer to the car's curve table (`0x4a9180`-`0x4a9d60`, 0xa0 each) | `0x405c6f` |
| `0x4af704` | 4 | display name, `COROLLA WRC` ...; 18 and 29 `----------`; drawn only by the ending's text (`END_TXT.TXR`, `0x415d48`), with the player's name | `0x415848` |
| `0x5b0914` | 4 | the race HUD's car name (`KEROLLA WRC` for 2) | `0x42c2c7` |
| `0x4b53e8`, `0x4b5470` | 4 | the network screens' car names, the first in the Japanese font's codes | `0x435964`, `0x43598e` |
| `0x5b07ec` | 4 | the rev counter, 0-15, into `0x5b2468` a player: `TACO.TXR`'s page (`0x428f6a`), the needle model (`0x5b2870`, seven models at `0x5a8ee0`-`0x5aa7e0` in METERDAT), and `0x5b08c4`, `0x5b271c`, `0x5b28d0`; 2, 4 and 12 are drawn without a needle (`0x42dba0`). All sixteen are some car's | `0x428dd3` |
| `0x4b5d94` | 4 | the engine's ten wav names (`evo5_e1.wav` ...), read from the car's folder | `0x4422ba` |
| `0x4b6aa8` | 4 | the two-player race HUD's car icon, 40x14: a part at `0x5af728` + 0x34 n, its uv at `0x5aa820` + 0x14 times the part's first dword, on `METER01.TXR`'s page 1, for player 1 (`+0x100`) and 2 (`+0x130`) | `0x42f686`, `0x42f640` |
| `0x49585c` | 4 | `CARPRO%02d` picture, -1 none | `0x41217a` |
| `0x4cedc4` | 4 | the car's index 0-19 in the records; ids from 29 on read as 0 | `0x4193d1`, `0x44f2dc` |
| `0x4b1074` | 4 | id to base car, for the arcade rivals; 25 is 8 first | `0x41b362` |
| `0x49afd0` | 4 | the rival set of a base car | `0x41b36c` |
| `0x4b0cec`, `0x4b0d64` | 4 | two HUD figures; 0 for 18 and 29 | `0x41853e` |
| `0x4d0368` | 4 | the glows' kind, 1-3 | `0x485b66` |
| `0x49dd50` | 8 | colours | `0x4676fa` |
| `0x4cd2cc` | 4 | desert glow offset (NOTES.md, *Car models*) | `0x46a609` |
| `0x4cd3c8`, `0x4cd440`, `0x4cd4b8` | 4 | the lamp kit's model list by course type | `0x469dd4` |
| `0x4cef48` | 4 | loader folder names; the course folders follow at `0x4cefc0` as their own table | `0x476673`, `0x476910`, `0x476f14` |
| `0x4ccf48` | 12 | `<car>.bin`, `<car>`, `<car>.txb` | `0x469b9e` |
| `0x50634c` | 0x40 | loaded models per car; `0x506acc` follows at once | `0x469b94` |

Two places change the id itself. Mode 10 (`0x462084`, the demo
replays in `CAR\*.REP`) turns 3 to 28, 4 to 27, 20 to 15, 21, 23 and 24
to 5, 22 to 0, 25 to 8 and 26 to 11 before it loads the replay. After a
race `0x418188` turns 23, 24 and 25 back to 5, 21 and 8: those three are
the course-modified cars, put in by the race and taken out by it.

### `MSelect.dll`

| Address | Entry | What |
| --- | --- | --- |
| `0x100b5970` | 8 | the menu table above |
| `0x10004ce4` | 1 | ids 3-26: the case of `0x10004c20`, which turns the current car's id into a menu car's before its mask (`1 << id`) places the cursor: 3 to 28, 4 to 27, 20 to 15, 21 to 5, 22 to 0, 26 to 11; 6 none |
| `0x1010f33c`, `0x1010f3e8` | 4 | the menu lists |
| `0x100b513c`, `0x100b5880` | 4 | the photo, a sprite in `MS_CAR.TXR` |
| `0x100b58f8` | 4 | the name logo, a sprite in `M_CNAME.TXR` |
| `0x100b51b4` | 4 | the two-player select's name logo, 166x40, six a page in `CLOGO2P.TXR`, which loads at slot 0x30 as M_CNAME does elsewhere |
| `0x100b70a0` | 16 | the four gearboxes offered (0/1 4-speed, 2/3 5, 4/5 6, 6/7 7; AT, MT) |
| `0x100b95a0` | 8 | offset and size of the 3D car in `MISC\B_CARMDL.BIN` |
| `0x100b9690` | 8 | offset and size of its textures in `MISC\B_CARTEX.BIN` |

The 3D car is the car's `r_<car>.mdl` with the tyre's UVs moved (23
dwords differ for the Lancer), its textures one RTEX of two: the 256²
body and the 64² tyre. The models are loaded once into `0x1011a71c`
(the object) and `0x1011a2fc` (the model); an id with a zero entry gets
no model, and the screen goes on drawing the one before.

A sprite is a 0x58-byte record: a texture object, a sub-record, 1, the
width and height, x and y on the page, then the page's index. The
name logos fill `M_CNAME.TXR`'s five pages, and the records' icon page
(`Record.txr` texture 8) holds 24 icons of each size and is full: new
art goes on a page added to the archive.

### The other screen DLLs

Every screen DLL links its own copy of the loader and its folder table:
MSelect `0x1010db44`, Record `0x1010fe0c`, ReplayGallery `0x100bca2c`,
Champagn `0x100a3714`, AdvTelop `0x10098d90`, MainMode `0x100989cc`,
Title `0x10097418`, Options `0x100b7348`.

| DLL | Address | What |
| --- | --- | --- |
| Record | `0x1009fd28`, `0x1009fda0` | the records' car icons, 58x20 and 42x14 |
| Record | `0x1010ebec`, `0x1009fccc` | the records' index (the exe's `0x4cedc4`), and by it the rankings' heading, the car's full name (`TOTAL RANKING` at 0); read at `0x100011c5`, `0x100017a5`, `0x10001ba5` for ids under 29, 0 from 29 on |
| ReplayGallery | `0x1009c8e0`, `0x1009c958` | icons, display names |
| Champagn | `0x1001c110`, `0x100a2398` | the same map as `0x49585c`; the podium's people, a name a car (`KERO` for 2 and 29, `EVO5` for 18, `205` for 26), read at `0x100031a9` into `CHAMPAGN\M<name>0.TXR` (driver), `M<name>1.TXR` and, with the female co-driver's voice, `F<name>1.TXR` |
| AdvTelop | `0x1009513c` | the advertise demo's ranking icons, 84x31, on `ADV_TXT.TXR`'s page 1 |

### The hidden ids against the cars they copy

What the three free ids share with a car, table by table:

| | 18 CARISMA / 4 LANCER | 26 PGT2051 / 11 PGT2050 | 29 FOCUS / 2 ESCORT |
| --- | --- | --- | --- |
| spec | same | same | same |
| curve | same | same | 0x4a9220 (RALLY0's) |
| engine sound | same | same | same |
| HUD icon | 0x13 (LANEVO6's) | 0x17 (IMP_99's) | same |
| display name | `----------` | same | `----------` |
| menu photo, logo | same | same | `Not avilable` |
| gearboxes | same | same | same |
| 3D car | none | none | none |
| record icons | same | own | own |
| records index | same | same | 0, which no other car has |

The spec, curve and engine are what drives; they are the donor's in
all three, so a slot drives as its donor until they change.

## The rev counter

A car's rev counter is a kind, 0-15, from `0x5b07ec`, copied at a race's
start into `0x5b2468` a player (`0x428dd3`). The kind picks, and nothing
else of the car does:

| What | Where | Read at |
| --- | --- | --- |
| the face | `TACO.TXR` page = kind, 128x128; the loader places page n at n times page 0's size, so every page is 128x128 | `0x428f6a` |
| the face's sprite | `0x5b08c4`, a part pointer; `0x5b1a38` (128x128) for all but 2, 4, 12 | `0x42ad75` and three more |
| rpm scale | 20 floats built on the stack at `0x42ac6d`, `mov [esp+0x14+4k], imm32` 8 bytes apart; the car's rpm times this is what the counter shows. A face reads to 8000 rpm at 1.0; a car that revs past 8000 takes more than 1.0 (1.25 for a face to 10000) | `0x42ad41` |
| needle angle | `0x5b2760` 16 bytes a kind: slope, knee, slope_low, offset; rpm below the knee gives rpm * slope_low, from it rpm * slope - offset | `0x42e307`-`0x42e32d` |
| start angle | `0x5b271c`, two shorts a kind added to that: where the needle sits at 0 rpm, the angle from 6 o'clock as 0 degrees, a signed short, 65536 a turn, positive when turned clockwise from there and negative when turned counter-clockwise (`start_angle` gives it as Q.15, the short over 0x8000: 1.0 half a turn, 0.5 9 o'clock, -0.5 3 o'clock), and whole turns above it, which MGameGL's rotations drop (`and ecx, 0xffff` into the 65536-entry sine table in MGAMEMAT) | `0x42e33c` |
| needle model | `0x5b2870`: seven models in METERDAT, `0x5a8ee0`-`0x5aa7e0`, drawn scaled 10 about the origin | `0x42e24c` |

The draw (`0x42dba0`) takes 2 (DELTA), 4 (IMPREZA) and 12
(MEGANE) as lamps or a bar of their own, from `0x5aa820`, `0x5b2934`
and `0x5b28d0`; every other kind is a needle.

| Kind | Cars | rpm scale | start_angle | start_turns | slope | knee | slope_low | offset | needle |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | CELICA, ST185, REPST185 | 1 | -0.171875 (`0xEA00`) | 0 | 5.46133 | 0 | 1 | 0 | `0x5a8ee0` |
| 1 | COROLLA, COR_TEIN | 1 | 0.1640625 (`0x1500`) | 1 | 5.472 | 0 | 1 | 0 | `0x5a8ee0` |
| 2 | DELTA (lamps) | 1 | 0.25 (`0x2000`) | 1 | 5 | 0 | 1 | 0 | - |
| 3 | ESCORT, FOCUS | 1 | -0.171875 (`0xEA00`) | 0 | 5.46133 | 0 | 1 | 0 | `0x5a8ee0` |
| 4 | IMPREZA, IMP_99 (bar) | 1 | 0.25 (`0x2000`) | 1 | 4.9152 | 0 | 1 | 0 | - |
| 5 | LANCER, LANEVO3/4/6, CARISMA | 1 | -0.265625 (`0xDE00`) | 0 | 8.192 | 3000 | 1.49333 | 20096 | `0x5a8ee0` |
| 6 | PGT306 | 1 | 0.328125 (`0x2A00`) | 1 | 5.46133 | 0 | 1 | 0 | `0x5a96e0` |
| 7 | STRATOS0, STR19750/1, STRATOS1 | 1.25 | 0.25 (`0x2000`) | 1 | 4.9152 | 0 | 1 | 0 | `0x5a92c0` |
| 8 | ALPINE | 1 | -0.1875 (`0xE800`) | 0 | 6.03429 | 1000 | 2.816 | 3228.3 | `0x5a9b20` |
| 9 | IMP_WRX | 1.18 | -0.21875 (`0xE400`) | 0 | 7.3216 | 4000 | 1.792 | 22118.4 | `0x5a8ee0` |
| 10 | DELTA16V | 1.25 | 0.0546875 (`0x0700`) | 1 | 5.12944 | 1000 | 0 | 5129.4 | `0x5a9f60` |
| 11 | FIAT | 1.25 | 0.2890625 (`0x2500`) | 1 | 4.672 | 0 | 1 | 0 | `0x5aa7e0` |
| 12 | MEGANE (lamps) | 1.12 | -0.203125 (`0xE600`) | 0 | 5 | 0 | 1 | 0 | - |
| 13 | RALLY0, RALLY1 | 1.25 | 0.2890625 (`0x2500`) | 1 | 4.672 | 0 | 1 | 0 | `0x5aa7e0` |
| 14 | PGT106 | 1 | 0.328125 (`0x2A00`) | 1 | 5.46133 | 0 | 1 | 0 | `0x5a96e0` |
| 15 | PGT2050, PGT2051 | 1.25 | 0.328125 (`0x2A00`) | 1 | 4.72178 | 1000 | 3.072 | 1649.7 | `0x5aa3e0` |

A needle model is a mesh descriptor {vertices, faces, material,
vertex count, face count} with 0x20-byte vertices, x and y along and
across the needle (the tip at y 4.4-4.9), the colour at `+0x10`:

| Model | Kinds | Colours |
| --- | --- | --- |
| `0x5a8ee0` | 0, 1, 3, 5, 9 | `ffeeeeee` needle, `ff171717` hub |
| `0x5a92c0` | 7 | `ffe7e7e7` all |
| `0x5a96e0` | 6, 14 | `ffff0000` needle, `ff171717` hub |
| `0x5a9b20` | 8 | `ff00ff00` needle, `ff171717` hub |
| `0x5a9f60` | 10 | `ffff6400` needle, `ff171717` hub |
| `0x5aa3e0` | 15 | `ffff6400` needle, `ff171717` hub |
| `0x5aa7e0` | 11, 13 | `ffc74800` all |

A new kind, 16-19 (the stack array's four spare floats): the tool
copies the four tables to the annex with the new rows, repoints their
ten reads, writes the rpm scale's immediate and adds the face as page
16 on of `TACO.TXR`. Its needle is a stock descriptor with vertices of
its own, scaled and recoloured.

## Three cars of their own: `tools/carslot.py`

The tool rewrites, for each id a slot file names, the entries above
that make the id a copy of another car (the file's format is in the
tool's docstring):

| Key | What changes |
| --- | --- |
| (any) | on the car select: the id's menu entry keeps its own bit (`1 << id`), which a stub at the start of each menu builder (`0x10002a97`, `0x10008c14`) ORs into the unlock mask, so the cursor finds the car again on the way back; `0x10004c20`'s turn of 26 into 11 (`0x10004ce4`, a case per id 3-26) goes |
| `perf` | spec block, curve, the two HUD figures and the gearboxes from that car; `sound` and `tacho` too unless given |
| `spec` | the spec block from a JSON file `--spec ID` writes: 170 values, floats as numbers, the rest as hex |
| `desert` | the lamp kit on desert courses (`0x4cd3c8`, model numbers into `0x4cc410`): `true` desert.mdl, de_light.mdl and normal.mdl, `false` normal.mdl alone (as the 306, 106 and MEGANE), a car id for that car's list and glow offset (`0x4cd2cc`) |
| `sound`, `tacho`, `hud_icon`, `gearbox` | the engine wav set, the rev counter (a car's, perf's unless given, or a new kind: *The rev counter*), the race HUD's car icon (another car's; only given), the four gearboxes |
| `name` | a new string in the exe's and ReplayGallery's annex, for the race HUD, the ending, the network screens and the gallery's list of saved replays; the results and records name cars in pictures |
| `full_name` | a new string in Record's annex, the heading of the rankings after a race or championship: the three lookups go to a table by id (29 in it), the stock ids keeping their records' names |
| `photo`, `logo` | a page added to `MS_CAR.TXR` (two photos) or `M_CNAME.TXR` (four logos), a new sprite in MSelect's annex |
| `icon`, `icon_small` | one page added at the same index to `Record.txr` and the three `Rank*.txr` (padded with blank pages to 15 first) and to the four `RG_*.txr`; new sprites in Record and ReplayGallery |
| `logo_2p` | a page added to `CLOGO2P.TXR` (six logos), a new sprite in MSelect's annex |
| `icon_2p` | a page added last to `TACO.TXR` (three icons a row) and three stubs: see *The two-player icons* |
| `icon_demo` | pasted into the free rows of `ADV_TXT.TXR`'s page 3, a new sprite in AdvTelop's annex: see *The advertise demo's icons* |
| `profile` | `CAR\carproNN.txr` from 20 on, the number in the exe's and Champagn's maps |
| `crew` | the podium's people: a name, a new string in Champagn's annex for `CHAMPAGN\M<name>0.TXR`, `M<name>1.TXR` and `F<name>1.TXR`, which go in that folder as any car's do (the tool says which are missing); or a car id for that car's |
| `replay` | `CAR\<car>.REP` from that car's replay, for the narration |
| `model` | `r_<car>.mdl`, `body.txr` and `ta_tire.txr` of the id's folder appended to `B_CARMDL.BIN` and `B_CARTEX.BIN`, their offsets in MSelect's table |

A uv entry's page is the archive's own index in the file, made good
at start-up table by table, each table followed by its header {table,
count}: MSelect adds the slot the archive loads at (`0x1002000a`, from
`0x1001a150`: MS_CAR 0x20, M_CNAME 0x30, the next archives 0x40 on, so
16 pages each at most); Record and the gallery replace it with the
loaded archive's texture handle (`0x1000f170` with the map `0x101118dc`,
`0x1000b7d0` with `0x100be208`). A table outside those lists keeps its
raw page - a new photo on page 10 showed msArcade's slot 10. So the new
sprites share one new uv table a file: MSelect's with the slots
written in, Record's and the gallery's registered by a stub the icons'
own registration call (`0x10003b60`, `0x10004556`) now goes through.

The spec card is shown under the car select's narration, mode 10,
which plays `CAR\<car>.REP` (the car id at `0x104`) after the rewrite
at `0x462084`; with no replay for the id the narration crashes, as it
does on the stock FOCUS. The tool writes `<car>.REP` from the `replay`
car's (default `perf`) with the id changed, and turns the rewrite of 26
to 11 off.

Each file the tool writes keeps what it found as `<file>.carslot`, and
`carslot.state` in the game folder holds the MD5 of what it wrote, so a
run starts from the backups while the files are still its own and from
the files when something else, the patcher, wrote them since. The
patcher's build check reads a `.carslot` for a file it does not patch
(MSelect, Champagn).

Not changed, and what that leaves:

- the records' car index (`0x4cedc4`): 20 places, 19 used and the 20th
  FOCUS's, so 18 and 26 share their donors' records;
- the menu's 3D car is the race's `r_` model as it is; the stock menu
  models move the tyre's UVs a little (23 dwords in the Lancer's);
- the glow kind, the colours and the arcade rivals.

## The two-player icons

The race HUD writes its quads into buckets, one a texture, and draws
them after (`0x429e40` on): the car icons go to the bucket at
`0x5b2458`/`0x5b245c`, drawn with the HUD's texture 1 (`0x5b23ec`),
`METER01.TXR`'s page 1. That page holds the 24 icons and has room for
two more at most, and no other page has room no stock uv reaches; a
page added to `METER01.TXR` itself would shift the HUD's texture list,
whose entries from 3 on are released by number (`0x4465b4`). So the
tool adds the page last to `TACO.TXR`, whose pages the HUD loads and
releases with the rev counters', and patches three places:

| Site | Was | Now |
| --- | --- | --- |
| `0x42900d` | the two-player rev counter load closing the archive (`0x475c60`) | skip to the icon page (`0x475bd0`), load it (`0x475c00`), add its handle to the texture list, then close |
| `0x42f65e`, `0x42f69e` | the two icons' `0x42d710(bucket, part, 1, x, y)` | a part in the annex goes to a bucket of the tool's own; the caller's bucket comes back as it was |
| `0x42a00b` | `mov esi, [0x5b2454]` after the icons' bucket | that bucket drawn with the icon page (texture `+0xac`, quads `+0xc4` as the stock buckets), emptied, then the load |

The new parts and uvs are reached by index like the stock ones, so the
tool places them in the annex where `(address - table) / size` comes
out whole. The icons are drawn in modes 4 and 5, the only ones that
load `METER01.TXR`.

## The advertise demo's icons

AdvTelop loads `ADV_TXT.TXR`'s seven pages at slots 0x5a-0x60
(`0x10001105`) and adds 0x5a to its uv table's pages at start-up
(`0x10004dfa`, header `0x10095ce8`); a new table's pages are the slots.
The ranking's car icons, 24 of them, fill page 1. The modes with the
ranking (all but 1 and 4) let pages 3-6 go right after the load
(`0x10001126` on), and the exit lets all seven go (`0x10001240`). Page 3
is text down to row 171 and nothing below, which no uv reaches, so the
tool pastes the new icons there (from row 177, three a row, six at
most), leaves out its release (`push 0x5d; push eax; call [ecx+0x2c]` at
`0x1000112d` to six nops) and points `0x1009513c` at sprites on slot
0x5d.

## What adding a car takes

**Within the 30 ids.** Ids 18, 26 and 29 are in every table and have no
folder. A new car can take one of them: its folder under `BINDATA`, the
mask in MSelect's table set to 1, and the entries above rewritten for
it where a copy of another car will not do (name, sprites, handling,
sound). Ids 23-25 have folders but are not free: the race puts them in
for the course-modified cars and turns them back after it (`0x418188`).
That is three ids without moving any table.

**Past 30.** Every table above moves to an annex with room for the new
ids and every read is repointed - the exe's twenty-odd tables and the
model array, MSelect's table, lists and sprites, the other DLLs'
sprites and names, and eight copies of the loader's folder table. The
patcher already appends sections and drops the relocations of the
sites it rewrites (`append_section`, `_self_section`,
`_drop_relocations`), so the method is there; the work is the count,
and the tables the scan did not find. Before that, a trace of reads
indexed by the car id during a race and each screen would give the
full list. The unlock mask has two spare bits; a new car can use
Corolla's bit instead. Two players on the network need the same
tables.

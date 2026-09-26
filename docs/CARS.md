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
| `0x4af704` | 4 | display name, `COROLLA WRC` ...; 18 and 29 `----------` | `0x415848` |
| `0x4b5d94` | 4 | the engine's ten wav names (`evo5_e1.wav` ...), read from the car's folder | `0x4422ba` |
| `0x4b6aa8` | 4 | the rev counter's design, 0-0x17, into `0x5af728` | `0x42f686` |
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
| `0x1010f33c`, `0x1010f3e8` | 4 | the menu lists |
| `0x100b513c`, `0x100b5880` | 4 | the photo, a sprite in `MS_CAR.TXR` |
| `0x100b58f8` | 4 | the name logo, a sprite in `M_CNAME.TXR` |
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
| ReplayGallery | `0x1009c8e0`, `0x1009c958` | icons, display names |
| Champagn | `0x1001c110`, `0x100a2398` | the same map as `0x49585c`, team names |
| AdvTelop | `0x1009513c` | sprites |

### The hidden ids against the cars they copy

What the three free ids share with a car, table by table:

| | 18 CARISMA / 4 LANCER | 26 PGT2051 / 11 PGT2050 | 29 FOCUS / 2 ESCORT |
| --- | --- | --- | --- |
| spec | same | same | same |
| curve | same | same | 0x4a9220 (RALLY0's) |
| engine sound | same | same | same |
| rev counter | 0x13 (LANEVO6's) | 0x17 (IMP_99's) | same |
| display name | `----------` | same | `----------` |
| menu photo, logo | same | same | `Not avilable` |
| gearboxes | same | same | same |
| 3D car | none | none | none |
| record icons | same | own | own |
| records index | same | same | 0, which no other car has |

The spec, curve and engine are what drives; they are the donor's in
all three, so a slot drives as its donor until they change.

## Three cars of their own: `tools/carslot.py`

The tool rewrites, for each id a slot file names, the entries above
that make the id a copy of another car (the file's format is in the
tool's docstring):

| Key | What changes |
| --- | --- |
| (any) | the id's menu mask becomes 1, so it is on the car select |
| `perf` | spec block, curve, the two HUD figures and the gearboxes from that car; `sound` and `meter` too unless given |
| `spec` | the spec block from a JSON file `--spec ID` writes: 170 values, floats as numbers, the rest as hex |
| `sound`, `meter`, `gearbox` | the engine wav set, the rev counter, the four gearboxes |
| `name` | a new string in the exe's and ReplayGallery's annex for the display name |
| `photo`, `logo` | a page added to `MS_CAR.TXR` (two photos) or `M_CNAME.TXR` (four logos), a new sprite in MSelect's annex |
| `icon`, `icon_small` | one page added at the same index to `Record.txr` and the three `Rank*.txr` (padded with blank pages to 15 first) and to the four `RG_*.txr`; new sprites in Record and ReplayGallery |
| `profile` | `CAR\carproNN.txr` from 20 on, the number in the exe's and Champagn's maps |
| `model` | `r_<car>.mdl`, `body.txr` and `ta_tire.txr` of the id's folder appended to `B_CARMDL.BIN` and `B_CARTEX.BIN`, their offsets in MSelect's table |

A sprite's page is the archive's own index: MS_CAR's pages load at
texture slot 0x20 and M_CNAME's at 0x30, so each archive has 16 pages
at most. A new sprite copies a stock record and part and points them
at a uv table of its own; the two pointers in the record get relocation
entries.

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
- AdvTelop's sprites (`0x1009513c`), Champagn's team names, the glow
  kind, the colours and the arcade rivals.

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

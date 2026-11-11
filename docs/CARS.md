# Cars

What a car is to the game, where its tables are, and what adding one
would take. Addresses are the European build's; the MediaKite exe has
the same data addresses (GAME.md, *The DigiCube and MediaKite build*), and the
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
(`0xb3a58`). Nothing else differs. The menu then offers three cars
more, 22 where the stock one shows 19 at most (*The car select's
ring*); ids 18, 26 and 29 exist in every table below - 18 mostly a
copy of the Lancer, 26 of the 205, 29 with entries of its own. With
no folder they need one before a race loads.

## Tables with one entry per car

Found by a scan for indexed tables exactly 30 entries long, then each
read at its use. The scan does not see arrays built at run time, so
this list is a floor.

### `SEGA RALLY 2.exe`

The car id of player `n` is at `[0x50b108] + n*0x30 + 0x100`.

| Address | Entry | What | Read at |
| --- | --- | --- | --- |
| `0x495a98` | 0x2a8 | **the car's spec**: 0xaa dwords copied into the car's physics object (`[0x4d64bc] + 0x2f4` for player 1) at `+0xac`; what they are in *The spec block*, every car's in [CARS_SPECS.md](CARS_SPECS.md) | `0x4051b6` |
| `0x4a9d60` | 4 | a pointer to the car's curve table (`0x4a9180`-`0x4a9d60`, 0xa0 each) | `0x405c6f` |
| `0x4af704` | 4 | display name, `COROLLA WRC` ...; 18 and 29 `----------`; drawn only by the ending's text (`END_TXT.TXR`, `0x415d48`), with the player's name | `0x415848` |
| `0x5b0914` | 4 | the race HUD's car name (`KEROLLA WRC` for 2) | `0x42c2c7` |
| `0x4b53e8`, `0x4b5470` | 4 | the network screens' car names, the first in the Japanese font's codes | `0x435964`, `0x43598e` |
| `0x5b07ec` | 4 | the rev counter, 0-15, into `0x5b2468` a player: `TACO.TXR`'s page (`0x428f6a`), the needle model (`0x5b2870`, seven models at `0x5a8ee0`-`0x5aa7e0` in METERDAT), and `0x5b08c4`, `0x5b271c`, `0x5b28d0`; 2, 4 and 12 are drawn without a needle (`0x42dba0`). All sixteen are some car's | `0x428dd3` |
| `0x4b5d94` | 4 | the engine's ten wav names (`evo5_e1.wav` ...), read from the car's folder | `0x4422ba` |
| `0x4b6aa8` | 4 | the two-player race HUD's car icon, 40x14: a part at `0x5af728` + 0x34 n, its uv at `0x5aa820` + 0x14 times the part's first dword, on `METER01.TXR`'s page 1, for player 1 (`+0x100`) and 2 (`+0x130`) | `0x42f686`, `0x42f640` |
| `0x49585c` | 4 | `CARPRO%02d` picture, -1 none | `0x41217a` |
| `0x4cedc4` | 4 | the car's index 0-19 in the records; ids from 29 on read as 0 | `0x4193d1`, `0x44f2dc` |
| `0x4b1074` | 4 | id to base car, for the rivals (*The rivals*); 25 is 8 first | `0x41b362` |
| `0x49afd0` | 4 | the rival set of a base car, 0-21 | `0x41b36c` |
| `0x4b0cec`, `0x4b0d64` | 4 | two HUD figures; 0 for 18 and 29 | `0x41853e` |
| `0x4d0368` | 4 | the glows' kind, 1-3 | `0x485b66` |
| `0x49dd50` | 8 | colours | `0x4676fa` |
| `0x4cd2cc` | 4 | desert glow offset (GAME.md, *Car models*) | `0x46a609` |
| `0x4cd3c8`, `0x4cd440`, `0x4cd4b8` | 4 | the lamp kit's model list by course type | `0x469dd4` |
| `0x4cef48` | 4 | loader folder names; the course folders follow at `0x4cefc0` as their own table | `0x476673`, `0x476910`, `0x476f14` |
| `0x4ccf48` | 12 | `<car>.bin`, `<car>`, `<car>.txb` | `0x469b9e` |
| `0x50634c` | 0x40 | loaded models per car; `0x506acc` follows at once | `0x469b94` |
| `0x4b2c40`, `0x4b2d30`, `0x4b2e20` | 8 | MSelect's three tables of the 3D car (`0x100b95a0`, `0x100b9690`, `0x100b9780`), a copy entry for entry; time attack loads the car from them (`0x4326b0` the textures, `0x432780` the model). An empty entry asks `VirtualAlloc` for 0 bytes, and the NULL it returns is read at `0x475d9a`: a crash | `0x4326ec`, `0x432780` |

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
| `0x100b9780` | 8 | offset and size of its reflection, the car under the floor, in `MISC\B_REFMDL.BIN` (*The car select's reflection*) |

The 3D car is the car's `r_<car>.mdl` with the tyre's UVs moved (23
dwords differ for the Lancer), its textures one RTEX of two: the 256²
body and the 64² tyre. The models are loaded once into `0x1011a71c`
(the object) and `0x1011a2fc` (the model); an id with a zero entry gets
no model, and the screen goes on drawing the one before.

The windows, the meshes on texture 2 (node 7, and 8 where a car has a
second), differ in every one of the 27 against its `r_<car>.mdl`: draw
options 0x07 and four 1.0 where the race model has 0x13 and 0.5, and
the first window's material `c8c8c896 14141400` where the race's is
`98989896 87878700` (the second's, `060606e6 34343400`, is the same).
IMP_99's car select model has no second window. A race model put on
the car select as it is draws its windows unlike the others';
`tools/carslot.py` makes the folder's `r_<car>.mdl` over so. The
Corolla's two models differ besides in their body (554 vertices against
542) and node 6 (445 against 449).

The draw options are the 0x20 bytes after a mesh's model pointers: the
window's first byte is the 0x07 or 0x13 (the second, 0x01, is the same
in both), and the four floats at `+0x08` the 1.0 or 0.5. What the bits
of 0x07 and 0x13 select is not known. The slots' folder models were
race models as any: FOCUS's and PGT2051's windows 0x13 and 0.5,
CARISMA's (the SEICENTO) 0x13 and 0.05, below every stock race model's
0.5. Made over, the three draw their windows as the stock cars do in
the game. A model named by `model`'s `mdl` is taken as it is, for one
already made for the car select.

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
| Champagn | `0x1001c254`, `0x10005808` | where the podium's two sit, and the car's run there (*The podium*) |
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

## The spec block

What is known of the 0x2a8 bytes each car id has at `0x495a98`
(`SEGA RALLY 2.exe`, the European and MediaKite builds): 170 dwords,
copied at the race's start (`0x4051b6`) into the car's physics object
at `+0xac`. The physics object is `[0x4d64bc] + 0x2f4` for player 1
(*What a race reads*); the step that reads most of the block is
`0x404120`. `tools/carslot.py --spec ID` writes a car's block as JSON,
and a slot's `spec` key takes one back (*Three cars of their own*). Every car's values, unpatched, are
in [CARS_SPECS.md](CARS_SPECS.md).

The names below come from where the code reads each dword. A `?` marks
a reading from the values and the arithmetic, not from a test.

### Who shares a block

The stock menu table holds 24 ids (*The car id*'s yes; it shows 19 of
them at most, *The car select's ring*). Less the three liveries,
COR_TEIN, REPST185 and STR19750, they are 21 cars with 19 blocks: IMP_99
has IMPREZA's, LANEVO6 LANCER's. Of the other ids, COR_TEIN has
COROLLA's, REPST185 ST185's, the three Stratos variants STRATOS0's,
RALLY1 RALLY0's, and the slots copy theirs: CARISMA LANCER's, PGT2051
PGT2050's, FOCUS ESCORT's. 28 of the 170 dwords are the same in every
car.

### The layout

| # | Offset | What |
| --- | --- | --- |
| 0-16 | `+0xac` | one a course, by `[0x50b108]+0x54`: the top speed there in km/h. The speed (`+0x14`, m/s) over it times 0.278 (`0x4956b0`) is kept at `+0x70` (`0x40413e`); at 236 km/h on Desert SS1, whose entry is 265, it read 0.891. See *Courses* |
| 17 | `+0xf0` | the driven wheels, bits: 1 rear, 2 front, 3 all four |
| 18-31 | `+0xf4` | surface table A, read by the first surface (`+0xa0`, `0x40457f`): tarmac 170, gravel 80, water 40, snow 100, mud 120 for most; the drive's grip? |
| 32 | `+0x12c` | 100000 for most |
| 33 | `+0x130` | 50 for most |
| 34-47 | `+0x134` | surface table B, by the second surface (`+0xa4`, `0x404846`) |
| 48 | `+0x16c` | 25000 in every car |
| 49 | `+0x170` | the most the car slides sideways: the clamp of `+0x60` (`0x404922`), which then gives `+0x64` as a fraction of it. 8192 for most, 5461 the 306, 106 and MEGANE, 10240 STRATOS, 13653 the 037 and ALPINE. Not the rev limit: the engine read 8795 rpm |
| 50-63 | `+0x174` | surface table C, by the second surface (`0x40459e`) |
| 64-68 | `+0x1ac` | the 4-speed set: a factor by the gear in use (`0x4041c1`, the gear at `+0x28`) |
| 69, 70 | `+0x1c0`, `+0x1c4` | how fast `+0x84` and `+0x88` follow the slide `+0x60` (`0x40421a`, `0x404243`): -8146 and -2636 against -8136 |
| 71-73 | `+0x1c8`-`+0x1d0` | two factors and a sum in one term (`0x404537`-`0x404569`) |
| 74-78 | `+0x1d4`-`+0x1e4` | five factors on absolute values summed into a slowing term (`0x404991`-`0x404a25`): the drags? |
| 79-92 | `+0x1e8` | surface table D, by the second surface (`0x40475f`) |
| 93-106 | `+0x220` | surface table E, by the second surface (`0x404830`) |
| 107-120 | `+0x258` | surface table F, by the second surface (`0x404452`) |
| 121 | `+0x290` | a factor on the drive's term (`0x4047b6`): 5 for most, 2.5 the 037, 3 STRATOS, 6 the 306, 106 and MEGANE |
| 122 | `+0x294` | times a gear's speed share, the speed the automatic shifts up at (`0x404ae3`) |
| 123-127 | `+0x298` | the 4-speed set: each gear's share of the top speed, 1.0 the last; the first entry 0 |
| 128-132 | `+0x2ac` | the 4-speed set, table C |
| 133-137 | `+0x2c0` | the 4-speed set, table D |
| 138-145 | `+0x2d4` | the other set's factor by gear (as 64-68) |
| 146-153 | `+0x2f4` | the other set's speed shares; the gears are the entries up to 1.0 (`0x40536c`), 6 for most, 7 the 306 |
| 154-161 | `+0x314` | the other set, table C |
| 162-169 | `+0x334` | the other set, table D |

The gearbox chosen picks the set (`0x40530f`, a case on its number):
the physics object's `+0x394`-`+0x3a0` then point at the 4-speed set
(`+0x1ac`, `+0x298`, `+0x2ac`, `+0x2c0`) or the other (`+0x2d4`,
`+0x2f4`, `+0x314`, `+0x334`), and the shares are scaled by the
set-up's ratio setting (`0x405425` on).

### Courses

`[0x50b108]+0x54`; the loading card is picked by it (`0x41a704`, cases
at `0x41a804`), and a replay file's course id is the same number:

| Index | Course |
| --- | --- |
| 0 | Desert SS1 |
| 1 | Mountain SS2 |
| 2 | Snowy SS3 |
| 3 | Riviera |
| 4 | Desert SS2 |
| 5 | Desert SS3 |
| 6 | Mountain SS1 |
| 7 | Mountain SS3 |
| 8 | Snowy SS1 |
| 9 | Snowy SS2 |
| 10 | Muddy SS1 |
| 11 | Muddy SS2 |
| 12 | Muddy SS3 |
| 13 | Isle SS1 |
| 14 | Isle SS2 |
| 15 | Isle SS3 |
| 16 | Super SS |

### Surfaces

Four surfaces are kept at `+0x90`-`+0x9c`, and the step takes one of
`+0x90`/`+0x94` and one of `+0x98`/`+0x9c` by the sign of `+0x60`
(`0x404264`); `0x4a9dd8` turns each into the tables' index (0 0, 1 1,
2 2, 3 3, 4 4, 5 2, 6 6, 7 10, 8 0, 9 2, 10 10, 11 11, 12 12, 13 13),
kept at `+0xa0` (the first surface) and `+0xa4` (the second). So
entries 5, 7, 8 and 9 of every surface table are never read.

What each index is, from the road noise the step starts for it
(`0x4042b6`, cases at `0x405068`, the car's sound slots at `0x4b5e0c`
into the race's list, `0x4cdd10` from the 15th entry on), and where it
was read (*What a race reads*):

| Index | Sound | Read on |
| --- | --- | --- |
| 0 | `rn_tar.wav` | tarmac (Desert SS1) |
| 1 | `gap.wav` | snow with the tarmac showing (Snowy SS2) |
| 2 | `rn_gra.wav` | the desert's gravel (Desert SS1), the plain mud road (Muddy SS3) |
| 3 | `rn_gra.wav` | not met |
| 4 | `water.wav` | a puddle (Desert SS1) |
| 6 | none | not met |
| 10 | `rn_snow.wav` | deep snow (Snowy SS2) and ice (Snowy SS1) alike |
| 11 | `rn_snow.wav` | the snow beside the road (Snowy SS1) |
| 12 | `rn_mud.wav` | deep mud (Muddy SS3) |
| 13 | `rn_mud.wav` | not met |

`0x495404` holds one more float a surface, the same for every car.

### What a race reads

The physics object of player 1 is `[0x4d64bc] + 0x2f4` (its spec at
`+0xac` after it). Read with the game paused, which keeps every value,
in the car setting mode (`[0x50b108]+0x38` 9) with COROLLA and its
4-speed box:

| Offset | What |
| --- | --- |
| `+0x14` | the speed, m/s |
| `+0x28` | the gear, 0 neutral |
| `+0x2c` | the engine, rpm: 7625 against the counter's 7600, 6499 against 6500 |
| `+0x60` | the slide: -8136 drifting left, 8182 right, near 0 straight on |
| `+0x64` | `+0x60` over #49, unsigned |
| `+0x70` | the speed's share of the course's top speed |
| `+0x78`, `+0x7c` | the throttle, 1 flat out, and it smoothed |
| `+0x84`, `+0x88` | `+0x60` followed at #69 and #70 |
| `+0x90`-`+0x9c`, `+0xa0`, `+0xa4` | the surfaces, raw and as the tables' index |
| `+0x394`-`+0x3a0` | the gear set's four tables (`+0x1ac`, `+0x298`, `+0x2ac`, `+0x2c0` with the 4-speed box) |

### Tyres and conditions

After the spec the same start (`0x4052c7`) copies 14 floats into
`+0x354`-`+0x388`: a grip factor a raw surface, read by the surface
under the car (`0x40428e`, `[esi + raw*4 + 0x354]`). They are one row
of `0x49bfb0`, 60 rows of 0x38 bytes, the row the condition times 12
plus the tyre:

- the tyre is the set-up's `+0x10`, in the order of MSelect's names
  (`0x100b5a80`): 0 `A DRY/DAMP`, 1 `A DAMP/WET1`, 2 `A DAMP/WET2`,
  3 `A WET`, 4 `G ASPHALT DRY/DAMP`, 5 `G COMPACTED GRAVEL`, 6 `G DRY
  DAMP/WET`, 7 `G SOFT/WET GRAVEL`, 8 `S ASPHALT SNOWY/FROZEN`, 9 `S
  ICE`, 10 `S SNOW`, 11 `DEFAULT`, the last all 1.0 and not offered;
- the condition, 0-4, is `0x49bf0c[a*4 + b]`. By the mode
  (`[0x50b108]+0x38`, cases at `0x405574`): in 0, 3, 5, 6, 9 and 10
  `{set, a, b}` comes from the stage, `0x4cf410` a course in mode 0,
  `0x4cf4dc` three a course otherwise, the one of the three
  `[0x50b108]+0x58` in modes 6 and 9 (the car setting's weather) and
  the first in the rest; one not set takes the course's own,
  `0x49bec8`. Mode 4, the ten-year one, takes `a` and `b` from
  `[0x50b108]+0x60` and `+0x64` (`0x4052b3`); the others condition 0.

What was read against it, the tyre `A DRY/DAMP` in the car setting
mode and `G DRY DAMP/WET` in the ten-year one:

| Stage | Condition | `+0x380`-`+0x388` |
| --- | --- | --- |
| Desert SS1 | 4, the course's own | 1, 1, 1 |
| Desert SS3, CLEAR (`+0x58` 0) | 1 (`a` 5, `b` 3) | 0.6, 1, 1 |
| Desert SS3, RAINY (`+0x58` 1) | 2 (`a` 7, `b` 3) | 1, 0.75, 0.6 |
| Snowy SS2 | 1 | 0.6, 1, 1 |
| Mountain SS2, Snowy SS1, Muddy SS3 | 0 | 0.6, 0.75, 0.7 |
| ten-year, tarmac, rain 30%, morning, 20 C (`+0x60`, `+0x64` 0) | 0 | 0.85, 1.05, 0.95 |
| Mountain SS2, RAINY (`+0x58` 1) | 3 | 1, 1, 0.75 (tarmac 0.65) |

The car setting's weathers, by course: MSelect names them from
`0x100b8238` (seven a course, an index into the names at `0x100b5af4`:
SUNNY, CLEAR, RAINY, FOGGY, SNOWING, HEAVY SNOW, BLIZAARD, SUNNY,
NIGHT, EVENING), the exe's condition for each from the tables above:

| Course | Weather and condition |
| --- | --- |
| Desert SS1 | CLEAR 4, EVENING 4, RAINY 2 |
| Desert SS2 | CLEAR 1, EVENING 1, RAINY 2 |
| Desert SS3 | CLEAR 1, RAINY 2 |
| Mountain SS1 | CLEAR 0, EVENING 0 |
| Mountain SS2 | CLEAR 0, RAINY 3 |
| Mountain SS3 | CLEAR 0, NIGHT 0, FOGGY 0 |
| Snowy SS1 | SNOWING 0, NIGHT 0 |
| Snowy SS2 | SNOWING 1, SUNNY 1, NIGHT 1 |
| Snowy SS3 | SNOWING 0, SUNNY 0, HEAVY SNOW 0 |
| Riviera | NIGHT 0, RAINY 3 |
| Muddy SS1 | CLEAR 0, RAINY 2 |
| Muddy SS2, SS3 | CLEAR 0, RAINY 3 |
| Isle SS1, SS3 | CLEAR 0, RAINY 3 |
| Isle SS2 | CLEAR 0, NIGHT 0, RAINY 2 |
| Super SS | 0 |

So the condition is the ground's, not the sky's: the time of day and
fog change nothing, CLEAR is 4, 1 or 0 by the course, and the rains
are 2 or 3. With `A DRY/DAMP`, tarmac and gravel (surfaces 0 and 2)
are 1.1 and 0.8 at 4, 1.0 and 0.8 at 1, 1.0 and 1.0 at 0 (which takes
the snow and mud surfaces down instead), 0.82 and 0.7 at 2, 0.65 and
0.8 at 3: 4 and 1 read as dry ground, 2 as wet and 3 as soaked, 0 as
the snow's and mud's; the names are a guess.

The set-up's `+0x1c` and `+0x20` times 0.2 go to `+0x38c` and `+0x390`
(`0x4052ed`), factors in the drive's terms.

## The podium (`Champagn.dll`)

Two more tables by car id, read through `[[0x100a6128]+0x10]+4`.

### Where the two sit

`0x1001c254` (file `0x1ac54`), a float a car. `0x10003780` adds it to
the car's height (`+0x23c`) into `0x100a67d8`; the driver (`0x10003850`)
and the co-driver (`0x100038e0`) are then put at {x, that + 1.905
(`0x1001c304`), 1.46}, x -0.436 for the driver and 0.316 for the
co-driver, through the object's `+0xa8`. x and z are the code's own
immediates, the same for every car; only the height is a car's. The
larger the value, the higher the two sit. ESCORT (2) alone is tested
for (`cmp [ecx+4],2` at `0x10003858`, `0x100038e8`) and gets 1.1
(`0x100a2414`, `0x100a2420`) instead of 1.905, the same x and z from
`0x100a2410`-`0x100a2424`: on the PC its people sit 0.805 lower than
the table says.

### The car's run

`0x10005808` (file `0x4c08`), a byte a car, the case of the switch at
`0x1000549f` (`0x1000545d` takes ids up to 29). Each case picks one of
nine runs at random from `CHAMPAGN\end_spin.bin` (runs 5 on from its
`+0x1800`):

| Case | Jumps to | Runs | Cars |
| --- | --- | --- | --- |
| 0 | `0x1000558a` | 6-8 | most four-wheel drives: a circle drift |
| 1 | `0x100054a6` | 2, 3 | the front drives, PGT306, PGT106, MEGANE: a side turn |
| 2 | `0x100055a3` | 0-3 | the others, rear and four-wheel drives: a drift |

### The PC's values

Unpatched, the European and MediaKite files (MediaKite's SHA-1
056885606fa0992e95b0ccd116ad3cd727fb605e):

| Id | Dir | Height | Run |
| --- | --- | --- | --- |
| 0 | `COROLLA` | 0.448 | 0 |
| 1 | `PGT306` | 0.326 | 1 |
| 2 | `ESCORT` | 0.429 | 2 |
| 3 | `IMPREZA` | 0.385 | 0 |
| 4 | `LANCER` | 0.344 | 0 |
| 5 | `STRATOS0` | 0.249 | 2 |
| 6 | `CELICA` | 0.461 | 0 |
| 7 | `DELTA` | 0.442 | 2 |
| 8 | `RALLY0` | 0.318 | 2 |
| 9 | `DELTA16V` | 0.432 | 2 |
| 10 | `FIAT` | 0.443 | 2 |
| 11 | `PGT2050` | 0.390 | 2 |
| 12 | `PGT106` | 0.309 | 1 |
| 13 | `ALPINE` | 0.278 | 2 |
| 14 | `MEGANE` | 0.402 | 1 |
| 15 | `ST185` | 0.442 | 2 |
| 16 | `LANEVO3` | 0.392 | 0 |
| 17 | `LANEVO4` | 0.402 | 0 |
| 18 | `CARISMA` | 0.344 | 2 |
| 19 | `IMP_WRX` | 0.377 | 0 |
| 20 | `REPST185` | 0.442 | 0 |
| 21 | `STR19750` | 0.249 | 2 |
| 22 | `COR_TEIN` | 0.448 | 0 |
| 23 | `STRATOS1` | 0.249 | 2 |
| 24 | `STR19751` | 0.249 | 2 |
| 25 | `RALLY1` | 0.318 | 2 |
| 26 | `PGT2051` | 0.390 | 2 |
| 27 | `LANEVO6` | 0.344 | 0 |
| 28 | `IMP_99` | 0.385 | 0 |
| 29 | `FOCUS` | 0.318 | 2 |

### The Dreamcast's

Both `CHAMPAGN.DLL` hold the same height table, 27 ids (0-26, then
other data), and one set of constants: -0.436, 0.316, 1.46, 1.905. There
is no 1.1 and so no case for ESCORT: every car sits at its value plus
1.905.

| File | SHA-1 | Table, file (address) | 1.905, file (address) |
| --- | --- | --- | --- |
| DC JP `CHAMPAGN.DLL` | 131856170264fa4b0f26477328db1bb9d0b73002 | `0x13754` (`0x10015154`) | `0x2278` (`0x10002e78`) |
| DC US `CHAMPAGN.DLL` | 335a99e87ff1e12403990f5519a8346c5b9fef5f | `0x18b70` (`0x1001a170`) | `0x22b4` (`0x10002eb4`) |

Ids 0-26 are the PC's values in both, but for the US ESCORT:

| Car | DC JP | DC US | PC |
| --- | --- | --- | --- |
| ESCORT (2) | 0.429 | 0.329 | 0.429, plus 1.1 |
| PGT106 (12) | 0.309 | 0.309 | 0.309 |

A slot with the Dreamcast's ESCORT model sits right at DC JP's 0.429
(id 29); 0.329, DC US's, suits a 206 on id 26, and PGT106's 0.309 a
SEICENTO on 18 (`crew_height`, *Three cars of their own*).

## The car select's ring

The car select draws the menu's photos round a ring, the chosen one in
front: `0x10009380` a photo on the one-player screens, `0x100030c0` on
the two-player one (its builder `0x10002a80`). The k-th photo stands at
the angle `[+0x44] - [+0x4c] * k`, in 0x10000 a turn, where `+0x4c` is
0x10000 over the count (`0x10008de4`) and `+0x44` turns to the chosen
car; sine and cosine come from the table at `0x10031260` (`0x1001e930`,
`0x1001e950`).

The ring's shape is not a circle of fixed size but a polynomial of the
count: with `u = (count - 8) / 11` (the count from `+0x34`, `+0x1c` on
the two-player screen, `0x10031184` 8.0 and `0x10031180` 1/11),
`s` the sine and `c` the cosine,

    z = 50 - 40c
    q = (z + 90) / 180
    w = (c + 1) / 2                      (c + 2) / 3 on the two-player screen
    x = -300 s (u/q + 1 - u) (((u - 0.5) 0.6 + w) u + 1 - u) (1 - 1.2 u (u - 1))
    y = 0.25714 x - 1.3 z + 10

x from the screen's centre (320.0, `0x10031124`), y before the
screen's own offsets. `u` is 0 at 8 cars and 1.0 at
19, the most the stock menu shows; past 19 the last factor shrinks the
ring, reaching 0 at 25 cars and turning it round beyond. The nearest
photos on a one-player screen, x off the chosen one's:

| Count | u | Next | Second | Third |
| --- | --- | --- | --- | --- |
| 19 | 1.0 | 218 | 365 | 411 |
| 22 | 1.27 | 153 | 265 | 315 |
| 22 at u = 1.0 | 1.0 | 192 | 335 | 404 |

The three slots make the menu 22, and its photos draw in. `tools/carslot.py`
keeps `u` at 1.0 whatever the count: at both sites (`0x100030e1`,
`0x100093a1`) `fild count; add esp, 8; fsub 8.0; fmul 1/11` becomes
three nops, `add esp, 8; fld 11.0` (`0x10031130`) and the same `fmul`, so
the ring is the stock 19's and only the step between photos shrinks. The
step and the turning still take the count, so the wrap at the ends is
unchanged.

## The car select's reflection

Under the car select's 3D car stands its reflection, a model of its
own in `MISC\B_REFMDL.BIN`, by MSelect's `0x100b9780` ({offset, size}
a car, 0 for 18, 26 and 29, which then have none). It is not a scaled
car: its width and length are the car's, to the third decimal (the
Lancer's x -0.914 to 0.914, z -2.188 to 2.187), and its height runs
-0.706 to 0.654 against the car's -0.318 to 1.421. Nor is it one of the
folder's models: the Lancer's has 557 vertices as `l_lancer.mdl`'s body,
but not its positions or faces.

Every PC reflection is one node with one mesh, the same in all 27:
texture -1 (untextured), one material (`ffffffff 00000000`, 0.9, 2.0),
draw options `3, 0, 0.5 x4`, the model pointers' `0x18` 10, and the UVs
0, 1 in most (a few keep real ones, unused). The faces are a list of
16-bit indices, three a triangle, wound so that a triangle's normal
agrees with its vertices'. The file runs header, material (`0x20`),
vertices, faces padded to 0x20, model pointers, draw options, the
node's transform and relation.

### The Dreamcast's

The Dreamcast keeps the car select in three files under `MISC`, each
with a table of 27 {offset, size} (ids 0-26) in `RALLY2.EXE`, and the
same tables again in the Japanese `MSELECT.DLL`:

| File | Japanese `RALLY2.EXE` | Japanese `MSELECT.DLL` | US `RALLY2.EXE` |
| --- | --- | --- | --- |
| `B_CAR_MODEL.BIN` | `0xa5614` (`0xb7a14`) | `0x30cb4` (`0x100332b4`) | `0xb2250` (`0xc3a50`) |
| `B_CAR_TEXTURE.BIN` | `0xa56ec` (`0xb7aec`) | `0x30d8c` (`0x1003338c`) | `0xb2328` (`0xc3b28`) |
| `B_CAR_REFLECTIONMODEL.BIN` | `0xa57c4` (`0xb7bc4`) | `0x30e64` (`0x10033464`) | `0xb2400` (`0xc3c00`) |

File offsets, the addresses in brackets. The Japanese `RALLY2.EXE` is
SHA-1 ba6a9810d5bcd44cfedc5dddf6824357411baafa, its `MSELECT.DLL`
118ff3e322a26df7a852e802b83fd3976cc39d63; the US `RALLY2.EXE`
530c36da06f0663663420e454c1588f3253f2621. The US build has the same
ids with two cars changed: 2 is the Peugeot 206 in the Escort's place,
12 the Fiat Seicento in the 106's.

The textures: the Japanese file's 27 are 21 compressed `RTXR` and six
`RTEX` as the PC's (the Escort's among them, 143360 bytes, the same as
a PC entry); the US file's are all `MTEX`, compressed (yakuza) ARGB1555
that decodes to the same 256² body and 64² tyre, and turns into the
PC's RTEX as RGB565. The bodies are the PC folders' `body.txr` pixel for
pixel; of the slots' three cars only the Escort's tyre differs.

The models share the PC's header and node layout but not the mesh: a
vertex is the position, the normal, a colour (`0xffffffff`) and 0, the
UVs stand in a table of their own (the model pointers' `0x18`), and a
face is a 32-byte record of four indices, the face normal and the
material's index. Four different indices are a quad in strip order
(abc, bdc); a triangle repeats its third (c, c). The Lancer's body has
13 materials, its reflection two, the second translucent
(`ffffffd2`).

### A Dreamcast reflection on the PC

PC and Dreamcast reflections have the same extents but not the same
mesh: of the Dreamcast Lancer's 385 positions 204 are in the PC's, and
the PC's has 567 triangles to the Dreamcast's 528. The PC's were made
again, not converted, and the node is the same but for the texture
index (0 on the Dreamcast).

One converts all the same: the vertices' positions and normals kept and
their UVs 0, 1; each quad two triangles (abc, bdc) and each triangle
one, which keeps the PC's winding; one material, the draw options and
the pointers' `0x18` as every PC reflection's; the node's texture -1;
the PC's file layout. The Dreamcast's translucent material is lost and
the whole reflection drawn as one. The Japanese Escort's (390 vertices,
502 triangles), the US 206's (434, 492) and Seicento's (447, 523) were
converted so and stand under the three slots in the game (`model`'s
`reflection`, *Three cars of their own*), each seen right on the car
select. Of the Seicento's 523 triangles one, a sliver of area 0.0015 that
the Dreamcast's own face normal also has reversed, disagrees with its
vertices' normals; nothing of it shows.

A Dreamcast reflection put on the PC unconverted cannot draw right (not
tried in the game): the PC reads the face count as that many 16-bit
indices, and a 32-byte record read so is 10, 0, 7, 0, 9, 0, 8, 0 and
then the face normal's floats as indices far past the vertices; the
colour in the UVs' place reads as NaN, and texture 0 has the body's
texture put on with them.

PC id 2's reflection, 117 vertices and 210 triangles, is the KEROLLA's
that took the Escort's place on the PC, and nothing of the Escort's.

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
| `spec` | the spec block from a JSON file `--spec ID` writes: 170 values, floats as numbers, the rest as hex; see *The spec block*, and every car's in [CARS_SPECS.md](CARS_SPECS.md) |
| `desert` | the lamp kit on desert courses (`0x4cd3c8`, model numbers into `0x4cc410`): `true` desert.mdl, de_light.mdl and normal.mdl, `false` normal.mdl alone (as the 306, 106 and MEGANE), a car id for that car's list and glow offset (`0x4cd2cc`) |
| `rival` | a car id the rotation starts at: the id becomes its own base car (`0x4b1074`) and gets a set from 8 on that starts there (`0x49afd0`), the slot's own set if it does; see *The rivals* |
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
| `crew_height` | where the podium's two sit: a float into Champagn's `0x1001c254`, or a car id for where that car's sit (ESCORT's 1.1 taken in): *The podium* |
| `podium_run` | the car's run on the podium: that car's byte of `0x10005808` (*The podium*) |
| `replay` | `CAR\<car>.REP` from that car's replay, for the narration |
| `model` | `r_<car>.mdl`, `body.txr` and `ta_tire.txr` of the id's folder appended to `B_CARMDL.BIN` and `B_CARTEX.BIN`, their offsets in MSelect's table and the exe's copy of it; or named one by one (`mdl`, `texture`, an RTEX of the two), with a `reflection`: a car's entry of `0x100b9780`, or an MDL appended to `B_REFMDL.BIN` |

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
- the glow kind and the colours;
- the shadow: one mesh (`0x4cc490`, node `0x4cceb0`) for every car,
  drawn at scale 1 and placed by the car's position and angles, not by
  its `l_` wheels or body. Only car id 2(`ESCORT`), is scaled, by
  (1, 1, 0.4) — two hard-coded `cmp ..., 2` on the player's car id
  (`[0x50b108] + 0x100 + player*0x30`) at `0x44c198` and `0x44de21`.
  Ids 18, 26 and 29 get the plain shadow.

## The rivals

The modes with opponents (`[0x50b108]+0x38` 1 and 2) make an object
(vtable `0x49b17c`) whose `+4` (`0x41b350`) fills a list of 15 cars
from the player's car id, and whose `+0xc` (`0x41b4b0`) names the rival:

- the base car (`0x4b1074`), its set (`0x49afd0`, 0-21) and the set's
  first place (`0x49b0a4`, 0-7) in the rotation `0x49b048`: CELICA,
  DELTA, IMP_99, STRATOS0, COROLLA, ESCORT, LANEVO6, PGT306, and the
  player's own car ninth for the sets from 8 on. The list takes the
  rotation from that place on and round, skipping the cars not open
  (`[0x50b108]+0x68`); COROLLA, STRATOS0, ST185 and LANEVO6 become the
  player's car when it is their variant (COR_TEIN; STR19750 or
  STR19751; REPST185; LANCER);
- `+8` (`0x41b440`) puts the opponents in from player 2's place: in
  mode 2 the list's first alone; in mode 1 up to six (fewer by the
  difficulty, `0x49b0fc`), the ones before the place `+4` counts to;
- `0x41b4b0` reads the set from the id itself, not its base car, and the
  race (`0x4126d0`) marks an opponent of that car as the rival. Stock,
  only ESCORT's two differ: its opponent is STRATOS0 (COROLLA's set),
  the car marked PGT306.

The stock rivals of the slots' ids: 18 IMP_99 (the Lancer's set 19),
26 STRATOS0 (the 205's set 15), 29 PGT306 (set 21, its own). No set
starts at ESCORT, so it is no one's rival. Mode 4 (vtable `0x49b18c`)
goes round the whole 22 of `0x49b048` from the course's place plus the
base car's set, so a new set changes that order too.

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

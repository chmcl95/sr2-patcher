# Network

How the game's multiplayer works and the plan for taking it off DirectPlay.
Read off the European Pentium III exe and the `MGNetWk.dll` every release
ships (one build, MD5 `0a9f86f5…`), with pefile and capstone; nothing here
has run yet. Addresses are VAs: exe base `0x400000`, DLL base `0x10000000`.

## What ships

Three layers:

1. **The exe** owns the lobby screens, the team room, the chat and its own
   message protocol above the transport (`0x435000`–`0x440400`), and the
   race-time exchange of car states (`0x437ed0`–`0x4383d0`, `0x417bd0`).
   `MainMode.dll` never touches the network: the exe's race object calls
   MainMode's Exec and then polls and sends around it (`0x417d87`).
2. **`MUSASHI\MGNetWk.dll`** ("MGameNetwork", Musashi SDK 0.9), a COM server
   with CLSID `{0D5837F0-3E3C-11D2-924E-00A0C9697E45}` and one extra export
   `_CreateGameNetwork@4`. It wraps DirectPlay into three objects the exe
   uses through vtables. No thread, no timer, no critical section: everything
   runs inside the exe's per-frame `Poll`.
3. **DirectPlay 3/4** (`DPLAYX.dll`, created with `CoCreateInstance`;
   `DirectPlayCreate` is used once, to list modems). Service providers
   TCP/IP, IPX, modem and serial, chosen by compound address. Sessions are
   `DPSESSION_MIGRATEHOST | KEEPALIVE`.

The exe also imports four WSOCK32 functions, only to print its own address
on the team room's status line (`0x436038`).

### The network object

Created at `0x43ff70` (`CoCreateInstance`, IID `{0D5837F1-…}`), kept at
`0x4eac0c`. Vtable `0x10015270`; the exe calls:

| Slot | Address | Call | Does |
| --- | --- | --- | --- |
| `+0x0c` | `0x10002550` | `SetAppGuid(struct)` | copies the 16-byte application GUID; the struct at `0x4b5338` is `{GUID 6A470280-0790-11D3-9E1B-00A0C9A0F04F, latency 5000, "157.109.86.141"}` |
| `+0x10` | `0x10002600` | `EnumModems(cb, ctx)` | modem names through `DirectPlayCreate` + `EnumAddress` |
| `+0x14` | `0x10002770` | `EnumConnections(cb, ctx)` | `IDirectPlay3::EnumConnections`; never called by the exe |
| `+0x18` | `0x10002a50` | `OpenConnection(struct)` | `{kind, arg1, arg2}`: 1 TCP/IP with `arg1` the IP string (empty = broadcast), 2 IPX, 3 modem (`arg1` device, `arg2` phone), 4 serial (`DPCOMPORTADDRESS` at `arg1`), 5 a raw compound address. Builds the address and `InitializeConnection`s a fresh `IDirectPlay3A` at `0x1001c69c` |
| `+0x1c` | `0x10002af0` | `SelectConnection(index)` | from the `EnumConnections` list; unused |
| `+0x20` | `0x10002950` | `ConnectViaLobby(params, &session, &player)` | `IDirectPlayLobby3::GetConnectionSettings` / `ConnectEx`: the game was launched by a DirectPlay lobby (HEAT). Tried at startup (`0x437cb0`) and on the connection screen (`0x43c198`); fails on any machine today |
| `+0x24` | `0x10002b70` | `EnumSessions(cb, ctx)` | `IDirectPlay::EnumSessions(ASYNC \| AVAILABLE)`; the callback gets a 0x60-byte record per session: `+4` max players, `+8` current, `+0xc` join disabled, `+0x10` instance GUID, `+0x20` name[64] |
| `+0x28` | `0x10002db0` | `JoinSession(record, &session)` | `Open(JOIN)`, looping on `DPERR_CONNECTING` |
| `+0x2c` | `0x10002ee0` | `CreateSession(record, &session)` | `Open(CREATE)`, flags `0x44` |
| `+0x30` | `0x10003020` | `GetCaps(caps, flags)` | `IDirectPlay::GetCaps`; the exe keeps `dwLatency` at `0x4b5348` (10000 for modem) and uses it as the session-search window |

### The session object

0x1260 bytes, vtable `0x10015320`, returned by the three calls above; the
exe keeps it at `0x4eac10`. Fields: `+8` the DirectPlay object, `+0x14` the
host's player ID, `+0x18` "I am host" (`DPCAPS_ISHOST`), `+0x24`/`+0x28` the
player list and count, `+0x2c` a 16-byte event FIFO, `+0x54` the reserved
slot table, `+0x60` the session description, `+0x26c` a 4 KB receive
buffer. The exe calls:

| Slot | Address | Call | Does |
| --- | --- | --- | --- |
| `+0x14` | `0x10004650` | `SetOpen(bool)` | clears or sets `DPSESSION_JOINDISABLED \| NEWPLAYERSDISABLED` and `SetSessionDesc`s. 1 on entering the team room (`0x436035`), 0 at START (`0x4376ae`) |
| `+0x18` | `0x10003cf0` | `CreatePlayer(name, &player)` | `IDirectPlay::CreatePlayer`; wraps it in a player object; the host assigns it an index (`0x10004960`: the lowest free, unreserved slot) and broadcasts the roster; a joiner's index stays −1 until the roster arrives |
| `+0x24` | `0x10004110` | `FindPlayerByIndex(idx, &player)` | AddRef'd |
| `+0x28` | `0x100041c0` | `GetPlayerCounts(&max, &current)` | |
| `+0x2c` | `0x100044f0` | `Poll()` | drains `Receive(DPRECEIVE_ALL)`; system messages (`CREATEPLAYERORGROUP`, `DESTROYPLAYERORGROUP`, `SESSIONLOST`, `HOST`) and the DLL's own control messages keep the player list and push events; every 32nd call re-checks the list against `EnumPlayers`. Returns `DPERR_SESSIONLOST` when the session is gone |
| `+0x30` | `0x100050a0` | `PopEvent(evt)` | `{type, dpid, index, 0}`; 0 if one was there, 1 if none |
| `+0x38` | `0x100047b0` | `IsSlotReserved(idx, &v)` | the team room's OPEN/CLOSE rows |
| `+0x3c` | `0x10004800` | `SetSlotReserved(idx, bool)` | host only; broadcasts the table, kicks a player sitting in the slot |
| `+0x08` | `0x10003ca0` | `Release` | the destructor `Close`s and releases DirectPlay |

Events the exe handles (`0x438c68`): **0** host identified (`+8` = the
host's index; if mine, `0x4eac20` = 1), **1** player created (`+8` = index),
**2** player destroyed, **3** session lost. Types 4–7 (the DLL's lockstep
layer and slot changes) are ignored.

### The player object

0x80 bytes, vtable `0x100152e0`; its record is 0x60 bytes: `+4` DirectPlay
ID, `+8` index (0–3, −1 unassigned), `+0x10` flags (bit 0 host, bit 1 local,
bit 2 ready, bit 31 destroyed), `+0x20` name[64]. The exe keeps its own at
`0x4eac14` and calls:

| Slot | Address | Call | Does |
| --- | --- | --- | --- |
| `+0x14` | `0x10003610` | `GetName(&str)` | `IDirectPlay::GetPlayerName` |
| `+0x18` | `0x100036a0` | `GetInfo(record)` | copies the record |
| `+0x20` | `0x10003720` | `GetFlags(&flags)` | |
| `+0x28` | `0x10003920` | `SendTo(target, data, len, guaranteed)` | `Send(from me, to target's ID or `DPID_ALLPLAYERS`, guaranteed ? `DPSEND_GUARANTEED` : 0)` with a 2-byte header `[0][?]` before the data. The exe's wrapper `0x438050` retries on `DPERR_BUSY` when guaranteed |
| `+0x2c` | `0x10003a60` | `PopUnsequenced(&tag, buf, &len)` | the next message for this player, header stripped, `tag` = the sender's index; `DPERR_NOMESSAGES` (`0x887700be`) when empty, `DPERR_BUFFERTOOSMALL` with `*len` = needed when it doesn't fit |
| `+0x08` | `0x10003480` | `Release` | a local player's destructor `DestroyPlayer`s |

The DLL's own wire format is one byte of type before the payload: 0 a game
message, 2 the roster (`{dpid, index}` pairs, from the host, guaranteed), 3
a player removed, 4 a new host, 0xe the reserved-slot table, and types 1 and
5–9 for a sequenced lockstep mode (`SendSequenced`, `SetReady`,
`ReadCurrent`) the exe never uses. Nothing else is added; there is no
keep-alive of the DLL's own - loss detection was DirectPlay's.

### The exe's protocol

Every message the exe sends goes through `SendTo` with the type in byte 0
and the sender's index in byte 1; received ones are dispatched by type at
`0x438922` through the table at `0x438c78`. The receive loop `0x438720`
(`Poll`, the events, then `PopUnsequenced` until `NOMESSAGES`) runs every
frame in the team room, during the MSelect screens and in the race.

| Type | Size | Guaranteed | Meaning |
| --- | --- | --- | --- |
| `0x1b` | 5+text | yes | chat line, shown as `entry>text` |
| `0x28` | 4 | yes / no | my state: 0 left, 1 in the team room, 0xa race setup begun, 0x10 setup done, 0x81 race scene loaded; the periodic resends before the start are unguaranteed |
| `0x27` | 4 | no | "what state are you in" - answered with `0x28` |
| `0x29` | 2 | no | on entering the room: the host answers `0x31`, everyone `0x2a` |
| `0x2a` | 0x48 | yes | my entry: status, car, variant, name, setup, spectator flag, races/wins/retired |
| `0x31` / `0x2d` | 0x134 | yes | the host's settings block: max players, host index, course, stage, laps, time-diff, boost, the four entries. `0x2d` at START |
| `0x2c` | 2 | no | "your block disagrees with my entry, resend" |
| `0x2e` / `0x2f` | 2 | yes | a guest leaving for a select screen and the host's acknowledgement |
| `0x30` | 2 | yes | a slot was opened or closed |
| `0x20` / `0x21` | 2 / 12 | no | clock sync: the host's base and now; the client sets its base with RTT/2 |
| `0x25` / `0x26` | 8 / 2 | first yes | the race start time (host clock + 2 s) and the request for it |
| `0x23` | 0x24 | no | **car state**: index, frame lead, position, three words the MainMode physics fills, the sender's frame counter |
| `0x24` | 8 | yes | finish time |
| `0x2b` | 8 | no | split time |

Race setup (`0x438dc0`, before MainMode loads): state 0xa, wait up to 15 s
for every racer; clients sync the clock against the host; state 0x10, wait
again. At the start line (`0x41c8d0`): state 0x81, the host sends the start
time when every racer is loaded (or after 30 s) and all count down to the
same host-clock instant.

**The race is not lockstep.** Each machine simulates its own car and sends
`0x23` unguaranteed on a cycle of `[2,3,5,7,…][players]+1` frames, staggered
by index: every 6 frames with two players (10 Hz), every 11 with four.
A received state is applied to a remote car (`0x4261e0`) by re-simulating
the frame gap - clamped to 24 frames - and blending over up to 32 frames.
A late or lost packet leaves the car on its extrapolated path; a machine
that finds itself 3.5 frames behind the others steps its simulation once
extra (`0x4eaca8`, consumed at `0x42887c`). Nothing waits for anyone. A
dropped player's car becomes a passive base car (`0x417c16`); a lost
session (event 3) releases everything and restarts the multiplayer mode at
the connection screens. Host migration is accepted (event 0 at any time)
but nothing is re-sent; only start time, settings and slot reservation
need a host.

Nothing is persisted but `MPDATA.DAT`: a 0x80-byte header (connection
type, COM settings, the IP string, the modem name) and the driver
profiles (0x44 bytes each: name, races, wins, retired, last race
settings). `MPDATA.TMP` is the lobby's surface backup for ALT+TAB.

### The screens

Multiplayer is main mode 0xa; the lobby object (`0x439230`) runs a task
list where a task's `+0xc` is its state function. In order: driver name or
profile list, the **connection screen** `0x43c160` (`CONNECT.BMP`, rows IPX
/ TCP-IP / MODEM / SERIAL; a fifth row OTHER is drawn but the cursor wraps
in 0–3 at `0x43bf55` and `0x43bf75`; the choice goes to `0x4eace6`), then
the **session list** `0x43f380` (JOIN / CREATE / SHOWTEAM / CANCEL).
SHOWTEAM dispatches on the type through `0x43efd8`: IPX opens the
connection and searches at once, TCP/IP first puts up the **IP entry**
popup `0x43cd30` (`IP_ENTRY.BMP`; the text goes verbatim to `0x4eacec`,
16 bytes, empty meaning "broadcast"). The search calls `EnumSessions`
every frame for 30 s while it returns `DPERR_CONNECTING`, then for
`latency` ms more. JOIN → `JoinSession` + `CreatePlayer`, then a loop with
no timeout until the index is known (`0x4402a0`). CREATE → the team name
entry → `OpenConnection`, `CreateSession`, `CreatePlayer`. Both go on to
MSelect's car select and then the **team room** `0x435b90`, whose status
strip prints `IP Address : %d.%d.%d.%d` from `gethostbyname` when the type
is TCP/IP (`0x436038`). The lobby's art is `BINDATA\connect\` and
`BINDATA\chat\`, and a loose file there overrides the cabinet.

## The plan

Replace `MUSASHI\MGNetWk.dll` with one of our own, same CLSID, same three
vtables, over plain UDP - the shape of v-on-patcher's `dpctrl.dll`, but
the job is smaller: there is no lockstep, no input delay and no frame ring
to reproduce, only a session/player model and messages with a reliable
and an unreliable class. The exe, its lobby and its protocol stay as they
are; the manifests already point the CLSID at the file.

**Topology.** A star: guests talk to the host only, the host forwards
between guests. One NAT pair per guest instead of one per pair of
players, the host is the one place the player list is decided (as the
stock DLL already had it: the host assigns indices and broadcasts the
roster), and a guest-to-guest car state costs one extra hop, which at
10 Hz dead reckoning does not matter.

**Two ways in, one code path.**

- *Direct*: the host opens a UDP port; a guest types its address in the
  IP entry, or nothing and the search broadcasts on the LAN. What TCP/IP
  did, without DirectPlay.
- *Internet*: as v-on-patcher - the host registers with a rendezvous
  server and gets a code like `EU-ABCDE`; the guest types the code in the
  same entry box (it fits the 16-byte field). The server gives each side
  the other's public endpoint, both punch, and if nothing gets through in
  four seconds the server relays. `net/rendezvous.py` from v-on-patcher
  is the starting point; it pairs one host with one guest per code and
  needs a guest slot per code for four players.

Whether the DLL takes the entry as an address or a code can be decided
from the text (a dotted quad or a name against `XX-XXXXX`), so the exe
could offer a single row. The connection screen has room for two, which
reads better; see the decisions below.

**What the DLL implements.**

- The class factory, `_CreateGameNetwork@4`, and the network object's
  slots `+0x0c`–`+0x30`. `EnumModems`/`EnumConnections` list nothing.
  `OpenConnection` binds the socket (any port for a guest, the fixed one
  for a host) and remembers the address or code; `GetCaps` reports a
  latency that makes the search window sensible (a second or two).
- `EnumSessions`: a query to the address, the LAN broadcast, or the
  endpoint the rendezvous handed over; hosts answer with their record
  (max, current, join disabled, instance GUID, name). `DPERR_CONNECTING`
  while nothing has answered, so the exe's 30 s search runs as it does.
- `CreateSession` / `JoinSession` and the session object: a hello with
  the instance GUID and the player's name, the host's accept with an
  index and the roster, events 0 and 1 in the order the exe expects
  (`0x4402a0` spins until the index is known). `SetOpen` and the reserved
  slots decide whether a hello is accepted; a full or closed session is
  refused.
- `SendTo`: a per-link sequence number, acks and retransmits for the
  guaranteed class, straight through for the rest; the receiver hands
  messages up with the sender's index, as `PopUnsequenced` did. Guaranteed
  traffic is the lobby's and a few race events; the only stream is `0x23`
  at 10 Hz and 36 bytes.
- `Poll`: drain the socket, run the timers, keep the player list. A
  heartbeat each way and a few seconds of silence is event 2 for a guest
  (the host tells the others) and event 3 for a lost host. No host
  migration: the exe already handles event 3 by going back to the
  connection screens.
- `Release`: a leave message so the others see event 2 at once.
- Not reproduced: the lockstep methods, `ConnectViaLobby` (returns
  failure, as it does today), `EnumConnections`, modem and serial.

Written in C, built with `i686-w64-mingw32-gcc` into `net/`, checked into
the repository with its hash as v-on-patcher does, installed by the
patcher beside the stock DLL (kept as `.stock`). The core is plain sockets
under a thin Winsock/BSD shim, so a host and a guest can be run against
each other on Linux in one process for the checks, the way the other
patches run under Unicorn.

**What the exe needs.** Small patches, in the annex as the others:

- the connection screen's cursor limited to the rows that work (`0x43bf55`,
  `0x43bf75`);
- the SHOWTEAM dispatch (`0x43efd8`) sending both working rows through the
  entry popup, and `OpenConnection` given the entry text for both (the IPX
  case at `0x44000a` passes none);
- the team room's status line asking the DLL for what to show - the code,
  or the address and port - through one added vtable slot on the network
  object, in place of the `gethostbyname` composition at `0x43604b`;
- the modem and serial rows' art replaced or left dark, and `CONNECT_IPX` /
  `CONNECT_TCPIP` relabelled, as loose BMPs in `BINDATA\connect\` made from
  the originals at patch time.

## Decisions to take

1. **Rows.** Two rows, INTERNET (code) and DIRECT IP (address, or blank for
   the LAN), in place of IPX and TCP/IP, with MODEM and SERIAL gone; or
   one row that takes either. Two needs the button BMPs relabelled; one
   needs none.
2. **The rendezvous.** Extend v-on-patcher's server for several guests per
   code and run it for both games on the same hosts (`segaonline.net` and
   the two others, another port), or a copy for SR2 alone.
3. **Port.** UDP 47624 as v-on-patcher, or one of SR2's own so both games
   can host on one machine.

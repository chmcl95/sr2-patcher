# net

The replacement `MUSASHI\MGNetWk.dll`: the stock DLL's three COM objects
over plain UDP. What the exe asks of it and why is in
[docs/NETWORK.md](../docs/NETWORK.md).

```
sr2net.h, sr2net.c   the core: sessions, players, reliable and unreliable messages; no Windows in it
sock.h               the little of UDP it needs, Winsock or BSD
com.c                the COM shell the game loads: the class factory, the vtables
mgnetwk.def          the exports, as the stock DLL has them
build.py             compiles with i686-w64-mingw32-gcc and bakes the DLL into sr2-patcher.py
directory.py         the directory server for INTERNET: sessions listed, joins introduced, relayed when they must be
directory.service    its systemd unit; tools/directory-install.sh puts both in place
```

`tools/nettest.c` runs a host and five guests in one process over
loopback, a third of the datagrams dropped, and is the `nettest` check;
`net/build.py --check` is the `net` check. `python3 net/build.py --out DIR`
also drops a fresh `MGNetWk.dll` in `DIR` to try by hand.

The patcher installs it with the `netplay` key, the stock DLL kept as
`.bak`; `lobby` and `netplay` need each other.

## The wire

Every datagram is a 16-byte header - `SR2N`, type, flags, from, to, a
reliable sequence number and the last one taken from the peer - and a
payload. Guests have one link, to the host; the host one per guest and
forwards between them. Reliable messages are numbered per link,
acknowledged on arrival, sent again every 250 ms until they are, and
delivered in order through a 64-deep window; the others go as they are.
A keep-alive every 500 ms; six seconds of silence, or six seconds with
nothing acknowledged, is a dead link: a guest dropped by the host, or the
session lost for a guest. The host owns the player list: it assigns
indices (the lowest free, unreserved slot, as the stock DLL did) and
sends the roster on every change.

A search is a `QUERY` to the LAN broadcast or the address typed, answered
with the session record; a join is `JOIN` with the session's id, answered
with `WELCOME` (the index, the reserved slots, the roster) or `REFUSE`.
`sr2-net.log` beside the exe, created empty, turns on a log of what the
core did.

## The directory

INTERNET goes through `net/directory.py`, UDP 47627, one on each of
v-on-patcher's three machines: `segaonline.net`, `us.segaonline.net`,
`jp.segaonline.net`. A host registers its session with all three every
second (`H`: the session's id and the record the list shows) and it
expires after five seconds without; a guest asks all three (`L`) and
merges the answers, so a host anywhere is seen from anywhere. JOIN names
the session at the server the guest heard it from (`J`); the server tells
each side the other's public address and port, the host sends a few
packets to open its NAT, the guest's joins arrive, and the link is direct
from there. When nothing has got through after four seconds the guest
sends its traffic through that server (`R`), which forwards it to the host
as `D` with the guest's address as the token the host's replies carry
back; the host follows the guest onto the relay the moment a relayed
packet arrives, and a join that reaches the host by both roads is one
guest, told apart by the nonce in it. The relay is per guest, so a session
can have one guest direct and another relayed.

What the server refuses is what v-on's rendezvous refuses: unknown
sessions asked for too often (joins from that address ignored for ten
minutes), more than eight sessions from one address, relayed datagrams
over the game's size, more than 300 a second per guest each way. It
forwards only between a session's host and the guests that joined it
there.

```bash
sudo tools/directory-install.sh install     # /opt/sr2-netplay, sr2-directory.service, udp/47627
sudo tools/directory-install.sh update      # after a git pull
     tools/directory-install.sh status      # the last week's sessions from the journal
```

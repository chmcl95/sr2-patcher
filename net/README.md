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

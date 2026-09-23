# Documentation map

The root [README](../README.md) is for playing: installing, what each
patch does, the window, the pad, the music, the terminal. Everything here
is for working on the patcher.

| Read | For |
| --- | --- |
| [NOTES.md](NOTES.md) | how the game works and what each patch changes: the patch table with every site, the builds and Sega's updates, the executable, Musashi, startup and files, a section per patch, the two discs |
| [WIDESCREEN.md](WIDESCREEN.md) | the widescreen patch: the setting, the 3D, the 2D and its exceptions (the HUD's frame, the side bars, the `.bg` screens, the lobby, the device viewport), the sea, the credits, the Graphic Settings page |
| [NETWORK.md](NETWORK.md) | the multiplayer: what ships (MGNetWk, DirectPlay, the exe's protocol, the race data path, the screens) and what replaces it - the UDP DLL, the three rows, the directory and the relay, what is and is not reproduced |
| [MAP.md](MAP.md) | where things are: the repository, the regions of `sr2-patcher.py`, the addresses mapped in the exe and six of the DLLs, then the sites by patch |
| [DEVELOPING.md](DEVELOPING.md) | setup, the daily loop, the checks and what each catches, adding a patch or a build, the diagnostics and reading a Wine log, releasing |
| [../asm/README.md](../asm/README.md) | the assembly sources: how they become bytes in the patcher, a line per file in a table and a section on each |
| [../net/README.md](../net/README.md) | the replacement `MGNetWk.dll`: its files, building and testing it, the wire format, the directory server and how to run one |

Where something lives, by question:

- *What is at this address, or where does patch X write?* MAP.md.
- *What does patch X change?* NOTES.md's table, then its section under
  *How each patch works*; WIDESCREEN.md for the four widescreen patches.
- *Which builds are there and how do their offsets map?* NOTES.md,
  *Builds*.
- *How do I rebuild after editing assembly?* asm/README.md.
- *How do I run the checks, or one of them?* DEVELOPING.md, *The
  checks*.
- *How do I trace what the game is doing?* DEVELOPING.md,
  *Diagnostics*.
- *How does multiplayer work, and what replaces DirectPlay?* NETWORK.md;
  the wire and the server, net/README.md.
- *What is in `data1.cab` and how is it read?* NOTES.md, *The install
  disc*.
- *How do I cut a release?* DEVELOPING.md, *Releasing*.

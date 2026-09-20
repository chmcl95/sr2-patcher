# SR2 Patcher

Gets *SEGA RALLY 2* (PC, 1999) running on a modern PC. It installs the
game straight from your disc images - no installer, no registry, no disc
in the drive - fixes the crashes, keeps the picture through ALT+TAB,
brings the music back, makes an XInput pad work out of the box with the
controls rebindable in-game, renders at your monitor's size, and plays
online without DirectPlay. Windows 10 and 11, Wine and Proton.

**Work in progress.** The game plays start to finish on all three
releases, but this is a hobby project poking at a 27-year-old binary, and
things will turn up. [Reporting a bug](#reporting-a-bug) says what helps.
The latest release is on the
[releases page](https://github.com/pairomaniac/sr2-patcher/releases);
the script here is that release plus whatever has landed since.

<h4 align="center">
  <a href="#quick-start">Quick start</a> &nbsp;·&nbsp;
  <a href="#disc-images">Disc images</a> &nbsp;·&nbsp;
  <a href="#builds">Builds</a> &nbsp;·&nbsp;
  <a href="#playing">Playing</a> &nbsp;·&nbsp;
  <a href="#what-the-patches-do">Patches</a> &nbsp;·&nbsp;
  <a href="#from-a-terminal">Terminal</a> &nbsp;·&nbsp;
  <a href="#reporting-a-bug">Bugs</a> &nbsp;·&nbsp;
  <a href="#known-issues">Known issues</a> &nbsp;·&nbsp;
  <a href="#planned">Planned</a>
</h4>

## Quick start

There is no exe yet. The patcher is a single Python script with a window.

1. **Install Python** from [python.org](https://www.python.org/downloads/),
   3.8 or newer. On the installer's first page, tick **Add python.exe to
   PATH**. Tk, which draws the window, comes with it. On Linux, see
   [From a terminal](#from-a-terminal).
2. **Get the script.** Download
   [`sr2-patcher.py`](https://raw.githubusercontent.com/pairomaniac/sr2-patcher/main/sr2-patcher.py)
   (right-click, *Save link as*), or use *Code → Download ZIP* on this
   page. That one file is all you need.
3. **Run it.** Double-click `sr2-patcher.py`, or open a terminal in its
   folder and run `py sr2-patcher.py`.
4. **Fill in the window from the top:**
   - **Disc 1 image** - the install disc's `.cue` (or `.iso`).
   - **Disc 2 cue** - the play disc's `.cue`. The music lives here.
   - **Install to** - an empty folder. The game takes about 800 MB.
   - **Language** - one of the six the disc carries.
5. **Install**, then **Rip soundtrack**. The pane at the bottom reports
   progress; each takes a minute or two. Install applies every patch as
   it goes. On Windows the **dgVoodoo 2** box is ticked: the wrapper is
   downloaded from its GitHub release and put in place, see
   [Playing](#playing).
6. Run `SEGA RALLY 2.exe` from that folder.

Already have the game installed from the original discs? Point
**Install to** at it and press **Patch**; put the play disc's `.cue` in
**Disc 2 cue** and press **Rip soundtrack** for the music. Only an
unmodified Pentium III install is accepted; see [Builds](#builds).
**Restore original** puts the game's own files back if you change your
mind, and takes dgVoodoo 2 out with them.

## Disc images

The patcher reads the images itself. Nothing to mount, no virtual drive.

You need both discs: the game is on the first, the music on the second.

- **Disc 1**, the install disc: a `.cue` with its `.bin` beside it, or an
  `.iso`. The `.cue` is the small text file, not the `.bin`.
- **Disc 2**, the play disc: a `.cue` with its `.bin` file or files. An
  `.iso` won't do here - it drops the audio tracks, and those are the
  music.

If you have the discs but no images, image them once:

- **Windows** - [ImgBurn](https://www.imgburn.com) in *Read* mode, with the
  output set to **BIN/CUE** rather than ISO.
- **Linux** - `cdrdao`, then its own `toc2cue`:

  ```bash
  cdrdao read-cd --driver generic-mmc-raw --datafile sr2-disc2.bin sr2-disc2.toc /dev/sr0
  toc2cue sr2-disc2.toc sr2-disc2.cue
  ```

## Builds

The patcher knows the European, American and Australian releases, told
apart automatically, each in its Pentium III build - the one the original
installer chose on any CPU of the last twenty-five years, and the one
Install always picks. The Japanese releases (Sega's HCJ-0145, DigiCube's,
MediaKite's, the I-O DATA bundle) are not known: no verified dump of any
of them has been seen, and one would be welcome. Sega's own updates for
the Japanese release are documented in [docs/NOTES.md](docs/NOTES.md);
the European release already carries their final files.

It tells them apart by the exe's checksum and then checks the thirteen
files of that build by size and checksum before it writes anything: the
nine it patches and the four other files the Pentium III set replaced.
If one doesn't match you get a line naming it, such as
`MUSASHI\MGAudio.dll is not the European build's`, and nothing is
touched. That means a modified game, a previous patcher's work, or a
mixed install; the fix is to install afresh from the disc.

Each patched file gets a `.bak` beside it, the untouched original. Patch
starts from those every time, so patching twice is the same as once, and
**Restore original** is just putting them back.

## Playing

**The window.** The game runs in a borderless window on the monitor it
starts on, 4:3 with black bars until you pick a widescreen size.
**ALT+ENTER** switches to a framed window you can move, resize or
maximise. ALT+TAB works either way.

**Widescreen.** **Options → Graphic Settings** has an **Aspect Ratio**
row - 4:3, 16:10, 16:9, 21:9, 32:9 - and its **Resolution** row lists
that aspect's sizes, 640x480 to 3840x2160 and 5120x1440. The picture
takes the new size at the next screen change and is stretched to the
window. On Windows without the dgVoodoo 2 add-on the list stops at 2048
a side, see [Known issues](#known-issues).

On a wide screen the race shows more at the sides. The menus and HUD
keep their shape in the middle, with the tiled backgrounds carried out
to the edges; the picture screens - the title, the mode select - stay
4:3 with the picture itself stretched, blurred and dimmed behind them to
fill the sides; the loading, game-over and logo screens, pictures on a
plain background, get that background.

**Controls.** An XInput pad works as it is: stick to steer, triggers for
the pedals, Start to pause. In the menus the D-pad or stick moves, A and
Start choose, B goes back; in the multiplayer team room Back switches
between the slot list and the MENU row, as TAB does. **Options →
Device Settings** shows both players' controls, keyboard and pad side by
side; press a key or button to rebind any of them. The controls are
saved as plain text in `SR2.CFG` next to the game.

**Music.** It plays from the `music\` folder, ripped from the play disc.
The three volume sliders share one scale, so equal settings are equally
loud.

**Multiplayer.** The connection screen offers three rows in place of
IPX, TCP/IP, modem and serial:

- **INTERNET** - **SHOW TEAMS** lists the teams open anywhere; joining
  needs no port forwarding.
- **DIRECT IP** - type the host's address, or `host:port`. The host
  forwards UDP 47626.
- **LAN** - searches the local network.

The team room, the chat, the car and course selection and the race are
the game's own. Up to four players; everyone needs the same patcher
version. If something goes wrong online, `sr2-net.log` (create the
empty file beside the exe first) from each machine is the report to
send.

## What the patches do

**Install** and **Patch** apply every patch. The **Diagnostics** boxes
add the logging patches of [docs/DEVELOPING.md](docs/DEVELOPING.md),
which write to `logs\\` in the game folder for a report; off unless
asked for. The offsets and internals are in
[docs/NOTES.md](docs/NOTES.md).

| Patch | Without it |
| --- | --- |
| **No disc required** | An "insert the play disc" box, and a menu with everything but multiplayer greyed out. |
| **Windows 9x check** | The Australian release refuses to start. |
| **Video card warning** | An OK/Cancel box on every start saying your card isn't certified, judged against a 1999 list and 4 MB of video memory. |
| **Startup crash** | Under Proton, the game closes before its window appears. |
| **Mode check** | "Failed to initialize. Error code 80004005" at start when DirectDraw doesn't list 640x480 at 16 bits - the game asked for that mode before opening its window, though the window needs no mode. |
| **Crash after the logos** | On Windows, sometimes: the logo screen releases a texture that doesn't exist, a read past a table. |
| **Crash after saving a replay** | On Windows, back at the menu: the replay gallery frees a buffer that isn't its own, and the heap since Windows 8 ends the process for it. |
| **Legacy DirectInput** | Some starts hang on a white window (RGB controllers, some keyboards): Windows' legacy `dinput.dll` scanning every HID device. The game now goes through `dinput8.dll`, and devices that are neither keyboard, mouse nor controller are left out of its list. |
| **Borderless window** | The game takes over the display at 640x480 and comes back from ALT+TAB on the wrong monitor. |
| **ALT+TAB** | Switching away and back leaves a blank screen. |
| **ALT+ENTER** | No windowed mode at all. |
| **Widescreen** | 640x480 stretched to the monitor. The game renders at the size you choose; see [Playing](#playing). |
| **Missing lettering** | The black lettering on the 2D screens - SELECT GAME, SELECT CAR - drawn as outlines. |
| **Invisible lobby text** | In multiplayer, the name you type, the team list and the chat never appear. |
| **Gauge over the lake** | On Mountain the tachometer's plate blanks the water behind it. |
| **Credits** | The ten-year championship's credits on a wide screen: the replay window beside its black frame, and the picture showing at the sides. |
| **Loading screens** | The stage's card - its artwork and name - is gone the moment the course has loaded, well under a second on a machine of today. It stays at least three seconds. |
| **Music** | Silence: the music was audio tracks on the play disc. The patcher rips them to `music\` and the game plays them from there. |
| **The mix** | Each volume slider followed a curve of its own, so a step meant something different on each, and the Australian release ran its effects at a fraction of the others'. All three now follow one curve, and the two musics are matched so equal sliders are equally loud. |
| **Gamepad** | Pads are DirectInput only, set up in a Control Panel applet that no longer installs; an XInput pad does nothing. |
| **Device Settings** | No way to see or change the controls from inside the game. |
| **Connection rows** | The connection screen offers IPX, TCP/IP, modem and serial, two of which no longer exist and none of which cross the internet. It offers INTERNET, DIRECT IP and LAN. |
| **Network DLL** | The game's networking is DirectPlay, gone from Windows since Vista and never able to cross a router. `MUSASHI\MGNetWk.dll` is replaced by one that speaks plain UDP: a directory server lists the open teams and gets the players through their routers, or relays for those it cannot. See [docs/NETWORK.md](docs/NETWORK.md). |
| **Pad on the multiplayer screens** | The team room takes nothing from an XInput pad, and its MENU row opens on TAB and nothing else. The pad works there as the keyboard does, Back as TAB. |

Everything else is the game as it shipped.

**Add-ons** are files beside the game, not edits to it. **dgVoodoo 2**
is [dege's](https://github.com/dege-diosg/dgVoodoo2) DirectDraw on
Direct3D 11/12, ticked by default on Windows and not under Wine or
Proton, which have no need of it. Windows' own DirectDraw refuses a
picture over 2048 a side and has grown slow and erratic with this game
on some machines; dgVoodoo's has neither problem. Patch downloads the
latest release and puts its `ddraw.dll` and config in `MUSASHI\` and
`D3DImm.dll` beside the exe, with fast video memory access on, the
watermark off and ALT+ENTER left to the game. Untick the box and Patch
to take it out again, the config kept; Restore original takes the
config out as well.

The `.exe.manifest` the patcher writes declares the game DPI-aware, so
Windows neither scales its window nor puts up the
compatibility-assistant box about it.

## From a terminal

Everything the window does, without the window:

```
python3 sr2-patcher.py --install "Sega Rally 2 (Disc 1).cue" ~/games/sr2 English
python3 sr2-patcher.py --rip "Sega Rally 2 (Disc 2).cue" ~/games/sr2
python3 sr2-patcher.py --patch ~/games/sr2
python3 sr2-patcher.py --restore ~/games/sr2
```

`--patch` applies every patch unless you name some: by name to apply only
those (the names are listed at the top of `sr2-patcher.py`), or with a
leading minus to leave them out, as in `--patch ~/games/sr2 -music`.
Leaving a patch out also leaves out whatever needs it; `windowed` and
`borderless` are the game's mode and cannot be left out. The `dgvoodoo`
add-on is on by default on Windows: `-dgvoodoo` leaves it out, and
naming it puts it in elsewhere.

On Linux the terminal commands need nothing extra; the window needs Tk:

```bash
sudo apt install python3-tk        # Debian, Ubuntu, Mint
sudo dnf install python3-tkinter   # Fedora
sudo pacman -S tk                  # Arch
```

Under Wine or Proton the patched folder runs as it is. The manifests
beside the exe stand in for the COM registration the installer used to
do.

## Reporting a bug

Open an [issue](https://github.com/pairomaniac/sr2-patcher/issues). Say
which release you have (European, American, Australian), whether you are
on Windows or Wine/Proton, and what you were doing just before. For a
crash on Windows, the entry under Event Viewer → Windows Logs →
Application names the faulting module and offset, which is usually enough
to find it. For a disc image of a release the patcher doesn't know, or
anything that doesn't fit an issue: pairo@segaonline.net.

## Known issues

- **The replay's keys have no pad equivalent.** Enter hides and shows
  the overlay; Up and Down cycle the camera (live, around, driver,
  side); Left and Right move it (around orbits, driver goes to third
  person, side switches sides); Page Up and Page Down change the field
  of view in the around view. Reported by
  [@chmcl95](https://github.com/chmcl95).
- **The alternative colours have no pad equivalent.** Page Up held
  while choosing the Stratos, Corolla, Impreza, Lancer Evo VI or ST185
  picks the car's other colour. Reported by
  [@chmcl95](https://github.com/chmcl95).
- **The team room's address line** shows the machine's own address,
  which is only the one to give out on a LAN.
- **Split screen: no lake on Mountain** - the game does not draw the
  water in split screen (its draw skips itself there); the same on the
  Dreamcast. Not a patcher issue.
- **Windows: the game does not start with an 8BitDo pad plugged in**,
  on one machine - it exits to the desktop before the renderer comes
  up, so no log is written. Not traced yet; the faulting module from
  Event Viewer would help.
- **Windows: a start that hangs on a white window** with the keyboard
  connected was traced, on one machine, to the MSI Mystic Light HID
  device and Windows' legacy DirectInput. The `dinput8` patch takes the
  game off that DLL; if a start still hangs with it on, please report it
  with the device.
- **Windows without dgVoodoo 2: nothing larger than 2048 a side.**
  Windows' own Direct3D refuses a picture wider or taller than 2048 as
  a drawing target ("Failed to initialize. Error code 80004005"), on
  NVIDIA and AMD alike, so with the add-on unticked Patch writes a list
  that stops at 1920x1200, with the halves of the 21:9 and 32:9 sizes
  (1280x540, 1720x720, 1920x540) for those screens, and the picture is
  stretched to the window. A larger size left in `SR2.CFG` is ignored
  and the game starts at 640x480. Wine and dgVoodoo 2 have no such
  limit and get the full list.
- **Windows: error 80004005 at start.** One cause is fixed (the mode
  check, above). If it still happens, tick `d3dinit` under Diagnostics,
  Patch, start, and send `logs\d3dinit.log` with the card and driver.

## Planned

In no particular order:

- **A Windows exe** of the patcher, so Python isn't needed - built on
  GitHub from this repository, as v-on-patcher's is.
- **A better-looking patcher window and README**, on the lines of v-on-patcher's.
- **The Japanese releases** - once a verified dump turns up. The
  European exe is Sega's UPDATE250 exe byte for byte, so the 2.50-patched
  original is probably a small row; the unpatched original and the two
  rereleases are unknown builds.

## Working on it

[docs/](docs/README.md) covers how the game works and how the patches are
made; `tools/check.py` runs every check.

## AI disclaimer

LLMs are part of the toolchain, alongside pefile, capstone, unshield,
Unicorn, Wine's tracing and WinDbg on the running game. Scope, testing and
debugging are human: every change is read before it goes in and played
before it ships. Offsets are verified against the originals before
anything is written, and the patcher refuses any file that isn't an
unmodified build it has tables for.

## Credits and licence

Successor to [v-on-patcher](https://github.com/pairomaniac/v-on-patcher).
The game is SEGA's. `LICENSE` (MIT) covers the patcher, its tools and its
documentation, not the game or the bytes quoted from it.

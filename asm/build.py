#!/usr/bin/env python3
"""Build the blob in ../sr2-patcher.py from asm/, or check that it still matches.

    python3 asm/build.py            # assemble and write
    python3 asm/build.py --check    # verify only, writes nothing

sr2-patcher.py carries the assembled bytes because it ships as one file that
runs from a fresh checkout with nothing installed. Never edit the hex by
hand; this overwrites it. The placeholders the patcher fills at apply time
are listed in MAGICS; the music blob must hold each of MUSIC_MAGICS at
least once, and each exe stub each of its EXE_MAGICS exactly once.
"""
import os
import re
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET = os.path.join(ROOT, 'sr2-patcher.py')

BLOBS = [('MUSIC_BLOB', 'music.asm', ()), ('ACTIVATE_BLOB', 'activate.asm', ()),
         ('RESTORE_BLOB', 'restore.asm', ()), ('TEXTCOLOR_BLOB', 'textcolor.asm', ()),
         ('BGROW_BLOB', 'bgrow.asm', ()), ('TITLEROW_BLOB', 'bgrow.asm', ('-DTITLE',)),
         ('FULLWIN_BLOB', 'fullwin.asm', ()), ('TEXRANGE_BLOB', 'texrange.asm', ()), ('REPLAYFREE_BLOB', 'replayfree.asm', ()), ('ALTENTER_BLOB', 'altenter.asm', ()),
         ('MIX_BLOB', 'mix.asm', ()), ('VOLTRACE_BLOB', 'voltrace.asm', ()), ('FRAMETRACE_BLOB', 'frametrace.asm', ()),
         ('DEVICES_BLOB', 'devices.asm', ()), ('PADINPUT_BLOB', 'padinput.asm', ()), ('DINPUT8_BLOB', 'dinput8.asm', ()), ('NOGENERIC_BLOB', 'nogeneric.asm', ()),
         ('WIDE_BLOB', 'wide.asm', ()), ('WIDE_US_BLOB', 'wide.asm', ('-DUS',)),
         ('WIDE2D_BLOB', 'wide2d.asm', ()), ('WIDEGL_BLOB', 'widegl.asm', ()), ('RESOLUTION_BLOB', 'resolution.asm', ()),
         ('LOADHOLD_BLOB', 'loadhold.asm', ()), ('HUDLAST_BLOB', 'hudlast.asm', ())]

MAGICS = {
    'MAGIC_ORIGENTRY': 0xE1E1E1E1,
    'MAGIC_IATMCI': 0xE2E2E2E2,
    'MAGIC_LOADLIB': 0xE3E3E3E3,
    'MAGIC_GETPROC': 0xE4E4E4E4,
    'MAGIC_GETMODFN': 0xE5E5E5E5,
}

# The exe stubs' placeholders, filled with absolute addresses from the
# build's row; the two IAT ones share their values with MAGICS.
EXE_MAGICS = {
    'GAMED3D': 0xEAEAEAEA,
    'RESUME': 0xEBEBEBEB,
    'HANDLER': 0xECECECEC,
    'LOADLIB': 0xE3E3E3E3,
    'GETPROC': 0xE4E4E4E4,
    'HWND': 0xEDEDEDED,
    'WIDTH': 0xEEEEEEEE,
    'HEIGHT': 0xEFEFEFEF,
    'LOCKDESC': 0xF1F1F1F1,
    'SETTEXTCOLOR': 0xF2F2F2F2,
    'RUNNING': 0xF3F3F3F3,
    'PAUSED': 0xF4F4F4F4,
    'DEBUGDLL': 0xF5F5F5F5,
    'CATCHUP': 0xF6F6F6F6,
    'MODE': 0xF7F7F7F7,
    'GETPPS': 0xF8F8F8F8,
    'GETMODFN': 0xF9F9F9F9,
    'HIRES': 0xFAFAFAFA,
    'SETTINGS': 0xFBFBFBFB,
    'SETTER': 0xFCFCFCFC,
    'LOADPIC': 0xC1C1C1C1,
    'GETTICK': 0xC2C2C2C2,
    'HUDLO': 0xC9C9C9C9,
    'HUDHI': 0xCACACACA,
    'WALKRESUME': 0xCBCBCBCB,
    'RENDERER': 0xC3C3C3C3,
    'SETVIEWPORT': 0xC4C4C4C4,
    'VPRECTS': 0xC5C5C5C5,
    'HUDDRAW': 0xC6C6C6C6,
    'TREEDRAW': 0xC7C7C7C7,
    'HUDRESET': 0xC8C8C8C8,
    'LATEFLAG': 0xCCCCCCCC,
    'FADEDRAW': 0xCDCDCDCD,
}
EXE_BLOB_MAGICS = {
    'ACTIVATE_BLOB': ('GAMED3D', 'RESUME'),
    'ALTENTER_BLOB': ('HANDLER', 'LOADLIB', 'GETPROC', 'HWND', 'WIDTH', 'HEIGHT'),
    'BGROW_BLOB': ('LOCKDESC', 'GAMED3D'),
    'TITLEROW_BLOB': ('GAMED3D',),
    'WIDE_BLOB': ('MODE',) * 2 + ('WIDTH',) * 3 + ('HEIGHT',) * 3 + ('GETPPS', 'GETMODFN') + ('SETTINGS',) * 2 + ('SETTER', 'GAMED3D', 'HUDLO', 'HUDHI', 'WALKRESUME'),
    'WIDE_US_BLOB': ('MODE',) * 2 + ('WIDTH',) * 4 + ('HEIGHT',) * 4 + ('GETPPS', 'GETMODFN', 'HIRES') + ('SETTINGS',) * 2 + ('SETTER', 'GAMED3D', 'HUDLO', 'HUDHI', 'WALKRESUME'),
    'TEXTCOLOR_BLOB': ('SETTEXTCOLOR',),
    'VOLTRACE_BLOB': ('LOADLIB', 'GETPROC'),
    'FRAMETRACE_BLOB': ('LOADLIB', 'GETPROC', 'RUNNING', 'PAUSED', 'DEBUGDLL', 'CATCHUP'),
    'LOADHOLD_BLOB': ('LOADPIC',) * 2 + ('GETTICK',) * 2 + ('LOADLIB', 'GETPROC'),
    'HUDLAST_BLOB': ('LATEFLAG', 'RUNNING') + ('HUDDRAW',) * 2 + ('TREEDRAW', 'FADEDRAW') + ('RENDERER',) * 3 + ('VPRECTS', 'SETVIEWPORT', 'HUDRESET'),
}

# devices.asm's placeholders: RVAs in Options.dll from the build's row,
# and the blob's own RVA and its data's, from the patcher.
DEVICES_MAGICS = {
    'SELFRVA': 0xD1D1D1D1,
    'EPILOGUE': 0xD2D2D2D2,
    'BINDPAGE': 0xD3D3D3D3,
    'DRAW': 0xD4D4D4D4,
    'PLAYSOUND': 0xD5D5D5D5,
    'INPUT': 0xD6D6D6D6,
    'SOUNDOBJ': 0xD7D7D7D7,
    'HANDLES': 0xD8D8D8D8,
    'PAGEHDR': 0xD9D9D9D9,
    'DRAWLIST': 0xDADADADA,
    'TEXT': 0xDBDBDBDB,
    'GLYPHS': 0xDCDCDCDC,
    'ROWS': 0xDDDDDDDD,
    'BINDDATA': 0xDEDEDEDE,
    'PADPOLL': 0xDFDFDFDF,              # an absolute exe address
}

# resolution.asm's placeholders: RVAs in Options.dll, from the build's row
# and from the page's own code, and the blob's RVA.
RESOLUTION_MAGICS = {
    'SETTINGS': 0xD3D3D3D3,
    'VALTAB': 0xD4D4D4D4,
    'TEXT': 0xDBDBDBDB,
    'GLYPHS': 0xDCDCDCDC,
    'LOADLIB': 0xE3E3E3E3,
    'GETPROC': 0xE4E4E4E4,
    'GETMODFN': 0xE5E5E5E5,
    'DRAW': 0xD6D6D6D6,
    'PLATES': 0xD7D7D7D7,
}

# padinput.asm's placeholders: offsets from the blob to MGInput.dll's IAT
# slots and to the two sites' continuations, filled by the patcher.
PADINPUT_MAGICS = {
    'LOADLIB': 0xE3E3E3E3,
    'GETPROC': 0xE4E4E4E4,
    'UPDATE': 0xE6E6E6E6,
    'POLL': 0xE8E8E8E8,
    'CARS': 0xE9E9E9E9,                 # an absolute exe address, not an offset
    'KBDPOLL': 0xECECECEC,
    'PUBLISH': 0xEDEDEDED,              # an absolute exe address
}

# dinput8.asm's placeholders: offsets from the blob to MGInput.dll's IAT
# slots and to the create site's continuation, filled by the patcher.
DINPUT8_MAGICS = {
    'LOADLIB': 0xE3E3E3E3,
    'GETPROC': 0xE4E4E4E4,
    'CONT': 0xE6E6E6E6,
}

# nogeneric.asm's placeholders: offsets from the blob to the site's
# continuation and to the loop's skip target, filled by the patcher.
NOGENERIC_MAGICS = {
    'CONT': 0xE6E6E6E6,
    'SKIP': 0xE7E7E7E7,
}

# An exe stub's source must not name an exe address: every one moves
# between builds and belongs in the row. Comments may.
EXE_ADDRESS = re.compile(r'^[^;]*\b0x[4-6][0-9a-fA-F]{5}\b', re.M)

# fullwin.asm finds the image base from its own RVA, which the patcher
# fills in over this.
SELF_MAGIC = 0xE7E7E7E7

BEGIN = '# --- GENERATED by asm/build.py: BEGIN (do not edit) ---\n'
END = '# --- GENERATED by asm/build.py: END ---\n'


def assemble(src, defines=()):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'blob.bin')
        subprocess.check_call(['nasm', '-f', 'bin', '-i', HERE + os.sep, *defines, '-o', out, os.path.join(HERE, src)])
        with open(out, 'rb') as fh:
            return fh.read()


def hexblob(name, raw):
    text = raw.hex()
    lines = ["    '%s'\n" % text[i:i + 64] for i in range(0, len(text), 64)]
    return '%s = bytes.fromhex(\n%s)\n' % (name, ''.join(lines))


def generated(check=False):
    out = [BEGIN]
    for name, src, defines in BLOBS:
        raw = assemble(src, defines)
        if name in ('FULLWIN_BLOB', 'TEXRANGE_BLOB', 'WIDE2D_BLOB', 'WIDEGL_BLOB', 'RESOLUTION_BLOB') and raw.count(struct.pack('<I', SELF_MAGIC)) != 1:
            raise SystemExit('%s: MAGIC_SELFRVA must occur exactly once' % src)
        if name == 'REPLAYFREE_BLOB' and raw.count(struct.pack('<I', SELF_MAGIC)) != 2:
            raise SystemExit('%s: MAGIC_SELFRVA must occur exactly once' % src)
        if name == 'MUSIC_BLOB':
            for magic, value in MAGICS.items():
                if struct.pack('<I', value) not in raw:
                    raise SystemExit('%s: %s does not occur in %s' % (src, magic, name))
        elif name == 'DEVICES_BLOB':
            for magic, value in DEVICES_MAGICS.items():
                if struct.pack('<I', value) not in raw:
                    raise SystemExit('%s: %s does not occur in %s' % (src, magic, name))
        elif name == 'PADINPUT_BLOB':
            for magic, value in PADINPUT_MAGICS.items():
                if struct.pack('<I', value) not in raw:
                    raise SystemExit('%s: %s does not occur in %s' % (src, magic, name))
        elif name == 'DINPUT8_BLOB':
            for magic, value in DINPUT8_MAGICS.items():
                if raw.count(struct.pack('<I', value)) != 1:
                    raise SystemExit('%s: %s must occur exactly once in %s' % (src, magic, name))
        elif name == 'NOGENERIC_BLOB':
            for magic, value in NOGENERIC_MAGICS.items():
                if raw.count(struct.pack('<I', value)) != 1:
                    raise SystemExit('%s: %s must occur exactly once in %s' % (src, magic, name))
        elif name == 'RESOLUTION_BLOB':
            for magic, value in RESOLUTION_MAGICS.items():
                if struct.pack('<I', value) not in raw:
                    raise SystemExit('%s: %s does not occur in %s' % (src, magic, name))
        else:
            for magic, value in EXE_MAGICS.items():
                want = EXE_BLOB_MAGICS.get(name, ()).count(magic)
                if raw.count(struct.pack('<I', value)) != want:
                    raise SystemExit('%s: %s should occur %d time(s) in %s' % (src, magic, want, name))
            if name in EXE_BLOB_MAGICS:
                with open(os.path.join(HERE, src)) as fh:
                    hit = EXE_ADDRESS.search(fh.read())
                if hit:
                    raise SystemExit('%s: an exe address in the source (%s); put it in the row' % (src, hit.group(0).strip()))
        out.append(hexblob(name, raw))
    out.append('MUSIC_MAGICS = {\n%s}\n' % ''.join("    '%s': 0x%08X,\n" % kv for kv in MAGICS.items()))
    out.append('EXE_MAGICS = {\n%s}\n' % ''.join("    '%s': 0x%08X,\n" % kv for kv in EXE_MAGICS.items()))
    out.append('FULLWIN_MAGIC = 0x%08X\n' % SELF_MAGIC)
    out.append('DEVICES_MAGICS = {\n%s}\n' % ''.join("    '%s': 0x%08X,\n" % kv for kv in DEVICES_MAGICS.items()))
    out.append('PADINPUT_MAGICS = {\n%s}\n' % ''.join("    '%s': 0x%08X,\n" % kv for kv in PADINPUT_MAGICS.items()))
    out.append('RESOLUTION_MAGICS = {\n%s}\n' % ''.join("    '%s': 0x%08X,\n" % kv for kv in RESOLUTION_MAGICS.items()))
    out.append('DINPUT8_MAGICS = {\n%s}\n' % ''.join("    '%s': 0x%08X,\n" % kv for kv in DINPUT8_MAGICS.items()))
    out.append('NOGENERIC_MAGICS = {\n%s}\n' % ''.join("    '%s': 0x%08X,\n" % kv for kv in NOGENERIC_MAGICS.items()))
    out.append(END)
    return ''.join(out)


def main(argv):
    check = '--check' in argv
    with open(TARGET, encoding='utf-8') as fh:
        text = fh.read()
    pattern = re.compile(re.escape(BEGIN) + '.*?' + re.escape(END), re.S)
    if not pattern.search(text):
        raise SystemExit('no GENERATED region in sr2-patcher.py')
    new = generated(check)
    if check:
        if pattern.search(text).group(0) == new:
            print('blobs match')
            return 0
        print('blobs differ: run asm/build.py')
        return 1
    text = pattern.sub(lambda _m: new, text)
    with open(TARGET, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    print('wrote %d blob(s) into sr2-patcher.py' % len(BLOBS))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

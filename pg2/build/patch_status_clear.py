#!/usr/bin/env python3
"""patch_status_clear.py -- fix Chinese status-bar RESIDUE by enlarging the field-erase
RECT height for the status-bar text fields.

Root cause (RE-confirmed): the status bar draws each cell via a descriptor table at
VA 0x4acd68 (file 0xabb68), 15-byte records [left,top,right,bottom(words) ...]. Before
drawing a name the engine Blts the mainbutn.shp background over that RECT to erase the old
text. The RECTs are only 7px tall (native 8px font); text is drawn TOP-ALIGNED at `top`
(main at top, shadow at top+1). A CJK glyph spans top..top+fontH-1, so the erase
(top..top+6) leaves the bottom rows as a ghost when the name changes/clears. This is
independent of font size -- shrinking the font does NOT fix it (even 12px still leaves
~4px of residue) -- the clear-box height must be widened to match the glyph height.

Fix: raise each cell's `bottom` word so the erase RECT covers the CJK cell height:
    bottom = top + fontH + 1   (fontH rows of glyph + 1 row of shadow drop)
`top` is left unchanged (it drives penY and the blit source-Y anchor), and left/right are
unchanged (horizontal centering unaffected). This is a pure data patch, size of file
unchanged. Because the erase is a Blt from mainbutn.shp (source-Y anchored to top),
extending `bottom` re-blits additional atlas rows just below the field -> MUST be verified
in-game (fields 4/5/6 share one bar-background strip so it is expected clean).

Fields patched: 1,2,3,8 (top bar, T=11) + 4,5,6 (bottom bar, T=457). Field 7 (T=360,
h=23) is already tall and untouched; field 0 is unused. File offsets of the patched
`bottom` word (BASE_FILE + fid*STRIDE + 6): field1=0xabb7d field2=0xabb8c field3=0xabb9b
field8=0xabbe6 field4=0xabbaa field5=0xabbb9 field6=0xabbc8.

This is a pure data patch at a FIXED file offset inside the original (unmoved) .data
section, so it is safe to run as the LAST step of the build chain regardless of how many
PE sections (.cjk / .ctyp / null-guard stub slack) were appended earlier -- appended
sections only grow the file at the END, never shifting existing offsets.

Usage: patch_status_clear.py <exe_in> <exe_out> <fontH> [comma-field-ids]
"""
import struct, sys

BASE_FILE = 0xabb68        # descriptor table file offset (VA 0x4acd68); unchanged by appended sections
STRIDE = 15
DEFAULT_FIELDS = [1, 2, 3, 4, 5, 6, 8]

def build(exe_in, exe_out, fontH, fields):
    d = bytearray(open(exe_in, "rb").read())
    clearH = fontH + 1
    print(f"[status-clear] fontH={fontH} -> bottom=top+{clearH}")
    for fid in fields:
        o = BASE_FILE + fid*STRIDE
        L, T, R, B = struct.unpack_from('<hhhh', d, o)
        newB = T + clearH
        struct.pack_into('<h', d, o+6, newB)
        print(f"  field {fid}: RECT [{L},{T},{R},{B}] h={B-T} -> bottom {newB} (h={newB-T})  @file {o+6:#x}")
    open(exe_out, "wb").write(d)
    print(f"[status-clear] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    exe_in, exe_out, fontH = sys.argv[1], sys.argv[2], int(sys.argv[3])
    fields = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else DEFAULT_FIELDS
    build(exe_in, exe_out, fontH, fields)

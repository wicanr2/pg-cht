#!/usr/bin/env python3
"""patch_purchase_cell_clip.py -- fix the PROCUREMENT-screen unit-name cell labels being
vertically clipped to ~9px (14px CJK cut at the bottom stroke).

=== Root cause (dynamic-trace confirmed, 2026-07-19) ===
The procurement screen's control-paint method @0x42c302 (the render callback stored at
+0x14 of every entry of the ONE control array 0x4a1e08 -- stride 0x24; no other array or
screen registers 0x42c302) draws each control's text label into a STACK-LOCAL clip view
built by initView @0x45ecdc at 0x42c749 with:
      x0 = desc[+2]           (cell left)
      y0 = desc[+8] + 2       (0x42c739: add eax,2)
      x1 = desc[+6]           (cell right)
      y1 = desc[+8] + 10      (0x42c726: add eax,0xa)  <-- clip window only 8px tall
The label string is then drawn at local y=0 (screen row y0). glyph-blit @0x41b033 clips the
14px CJK glyph to the view's clipY1 (= y1 = cellTop+10), so only ~9px shows. Dynamic backtrace
(hook @0x41b033) proved the clipped draws come EXACTLY through this path (V = the stack view,
clip window [cellTop+2 .. cellTop+10]); forcing the glyph-blit clip to bufH (the "E2" probe)
made the labels full-height, and this per-caller offset patch reproduces that result WITHOUT
touching the shared glyph-blit or initView (initView has ~9 other callers).

=== Fix (scoped, single byte, parametrized) ===
Widen ONLY this call site's y1 offset so the clip window fits an FONT_H-px glyph:
      y1 = desc[+8] + (2 + FONT_H)      (0x42c728: 0x0a -> 0x02+FONT_H)
The original 0x0a == 2 + 8 (the native 8px font height), so `2 + FONT_H` is the exact
generalization. For FONT_H=14 -> 0x10. y0 (+2) is unchanged, so the label keeps its top
position and only grows downward into the (previously empty) gap above the cell's box.

Blast radius: exactly the labels painted by 0x42c302 (the procurement control array). The
shared glyph-blit @0x41b033, initView @0x45ecdc, drawStringCore/drawTextField/drawWrappedText
are byte-untouched. Verified in wine: labels full-height, box below untouched, 0 page faults.

This is a fixed .text-offset byte patch, so it is safe to run at any point in the build chain
(appended sections only grow the file end and never shift .text).

Usage: patch_purchase_cell_clip.py <exe_in> <exe_out> <fontH>
"""
import struct, sys

VA_ADD  = 0x42c726                 # `add eax,0xa`  (83 c0 0a)
FILE_ADD = VA_ADD - 0x401000 + 0x400
EXPECT  = bytes.fromhex("83c00a")  # add eax, 0x0a

def build(exe_in, exe_out, fontH):
    d = bytearray(open(exe_in, "rb").read())
    cur = bytes(d[FILE_ADD:FILE_ADD+3])
    assert cur == EXPECT, f"@0x42c726 not `add eax,0xa`: {cur.hex()} (expected 83c00a)"
    new_off = 2 + fontH                      # y1 = cellTop + 2 + FONT_H (was 2+8=0x0a)
    assert 0 < new_off <= 0x7f, f"clip offset {new_off} out of byte range"
    old = d[FILE_ADD+2]
    d[FILE_ADD+2] = new_off
    open(exe_out, "wb").write(d)
    print(f"[cell-clip] procurement label clip @0x42c726 (0x42c302 render method): "
          f"y1 = cellTop + {old} -> cellTop + {new_off}  (2+FONT_H, FONT_H={fontH})  @file {FILE_ADD+2:#x}")
    print(f"[cell-clip] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], int(sys.argv[3]))

#!/usr/bin/env python3
"""patch_briefing_font12.py -- render the on-map CAMPAIGN/SCENARIO BRIEFING prose at a
SMALLER font (default 12px) while every other screen stays 14px, AND fix the briefing
box HEIGHT so the whole paragraph fits.

=== Two independent defects this fixes (both briefing-only, zero blast radius) ===

(1) BOX TOO SHORT (paragraph clipped ~7 of ~11 lines).  The two on-map briefing box
    drawers 0x456d32 / 0x456efb size the panel HEIGHT as  boxH = countLines(N) * 10
    (`lea eax,[eax+eax*4]; add eax,eax`, i.e. the native 8px-font 10px line pitch) and
    center it on y=240.  But the CJK prose is rendered by WWSTUB at line pitch
    font_h+2 (16px at 14px).  So the drawn box is 10/16 of the height the text needs ->
    only ~62% of the lines fit before the box bottom clips them.  Fix: patch the ×10 in
    BOTH drawers to ×(brief_font_h+2) so the box matches the actual rendered line pitch.
    countLines still measures at the global 14px width, so N >= the 12px render line
    count -> the box is always >= the text height (a little slack, like the hero shot).

(2) FONT TOO BIG (user wants the briefing prose smaller).  The briefing prose goes
    through drawWrappedText (WWSTUB @0x43e955), which is SHARED by 11 callers (advisor
    tips, help/message boxes, ...).  To shrink ONLY the briefing and nothing else we:
      * append a second, 12px atlas (identical dense mapping to the 14px atlas -- built
        from the same char set, so the dense-encoded *.TXT data is reused unchanged);
      * install a flag-dispatched WWSTUB: reads a 1-byte flag -> if set, draw with the
        12px atlas + 12px advance + 14px line pitch; else the byte-for-byte original
        14px behaviour (atlas 0x57f200, 14px advance, 16px pitch);
      * wrap ONLY the two briefing render calls (0x456e8d, 0x45706b -> 0x460193) with a
        caller-specific trampoline that sets the flag, calls 0x460193, clears the flag.
    The other 9 drawWrappedText callers still call 0x460193 directly (flag stays 0) ->
    they keep 14px.  drawStringCore (STUB1, all single-line UI: menus/lists/status bar/
    purchase/unit-info) is a different hook entirely and is untouched.

Everything new lives in one appended, writable+exec PE section (.b12); no existing
section, the shared WWSTUB, countLines, or any of the 7 prior patches is disturbed.

Usage: patch_briefing_font12.py <exe_in> <atlas12.dat> <exe_out> <scratch> [brief_font_h=12]
"""
import struct, subprocess, os, sys

IMAGE_BASE = 0x400000
SECT_ALIGN = 0x1000
FILE_ALIGN = 0x200
TEXT_VA, TEXT_RAW = 0x401000, 0x400

# --- shared contract with build_hooked_exe_pg2.py ---
ATLAS14_VA    = 0x57f200            # the 14px atlas inside .cjk (main + non-briefing WWSTUB)
VA_DRAWGLYPH  = 0x41b033
VA_WW_HOOK    = 0x43e955            # e9 rel32 (+2 nop) -> old WWSTUB; we repoint the rel32
VA_WW_BACKEDGE= 0x43e804
VA_WW_ASCII   = 0x43e95c
WW_DBCS_FLAG  = 0x4ba744           # replayed `cmp dword[0x4ba744],1` on the ASCII path
LEAD0, TRAIL0, TRAILW = 0x81, 0xA1, 94

# briefing box-drawers: box-height `lea eax,[eax+eax*4]; add eax,eax` (=N*10) sites
BOXH_SITES    = [0x456e1d, 0x45701c]
BOXH_ORIG     = bytes.fromhex("8d048003c0")
# briefing render calls `call 0x460193` to wrap with the flag trampoline
RENDER_CALLS  = [0x456e8d, 0x45706b]
VA_460193     = 0x460193

def va2file(va): return va - TEXT_VA + TEXT_RAW

def nasm(asm, scratch, tag):
    src = os.path.join(scratch, f"{tag}.asm"); binf = os.path.join(scratch, f"{tag}.bin")
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    return open(binf, "rb").read()

def ww_body(va, atlas_va, font_h, maxlead, count):
    """Byte-for-byte the shipping WWSTUB, parametrized by atlas VA + font_h (advance) +
    lineh (font_h+2). Local labels are unique per assembly (assembled standalone)."""
    lineh = font_h + 2
    return f"""bits 32
org {va:#x}
    movsx eax, word [ebp-0x1c]
    mov ecx, [ebp+0x10]
    movzx edx, byte [ecx+eax]
    cmp dl, {LEAD0:#x}
    jb .ascii
    cmp dl, {maxlead:#x}
    ja .ascii
    movzx eax, byte [ecx+eax+1]
    cmp al, {TRAIL0:#x}
    jb .ascii
    cmp al, 0xfe
    ja .ascii
    sub edx, {LEAD0:#x}
    imul edx, edx, {TRAILW}
    sub eax, {TRAIL0:#x}
    add edx, eax
    cmp edx, {count}
    jae .ascii
    movsx eax, word [ebp-0x14]
    add eax, {font_h}
    movsx ecx, word [ebp-0x28]
    cmp eax, ecx
    jle .nowrap
    mov word [ebp-0x14], 0
    movsx eax, word [ebp-0x18]
    add eax, {lineh}
    mov [ebp-0x18], ax
    inc word [ebp-0x20]
.nowrap:
    push dword [ebp+0xc]
    push edx
    push {atlas_va:#x}
    movsx eax, word [ebp-0x18]
    push eax
    movsx eax, word [ebp-0x14]
    push eax
    push dword [ebp+0x14]
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    mov ax, [ebp-0x14]
    add ax, {font_h}
    mov [ebp-0x14], ax
    inc word [ebp-0x1c]
    jmp {VA_WW_BACKEDGE:#x}
.ascii:
    cmp dword [{WW_DBCS_FLAG:#x}], 1
    jmp {VA_WW_ASCII:#x}
"""

def build(exe_in, atlas12_path, exe_out, scratch, brief_font_h=12, box_pitch=None):
    # box_pitch = the per-line multiplier used to size the briefing box HEIGHT
    # (box = countLines * box_pitch). It is DECOUPLED from the render line pitch
    # (brief_font_h+2) because countLines under-counts vs the actual atlas render for CJK
    # (its word-wrap classifies/measures differently), so a box_pitch == render pitch still
    # clips the last line(s). Default gives generous slack; the exact value is calibrated in
    # wine against the longest opening briefing (see make_full_release.py / §7.13).
    if box_pitch is None:
        box_pitch = brief_font_h + 6
    d = bytearray(open(exe_in, "rb").read())
    atlas12 = open(atlas12_path, "rb").read()
    a12_count = struct.unpack('<I', atlas12[4:8])[0]
    a12_h     = struct.unpack('<I', atlas12[8:12])[0]

    # --- sanity: patch sites are pristine ---
    for va in BOXH_SITES:
        assert bytes(d[va2file(va):va2file(va)+5]) == BOXH_ORIG, f"box-height @{va:#x} unexpected"
    for va in RENDER_CALLS:
        f = va2file(va); assert d[f] == 0xE8
        assert va + 5 + struct.unpack_from('<i', d, f+1)[0] == VA_460193, f"render call @{va:#x} not ->0x460193"
    f = va2file(VA_WW_HOOK); assert d[f] == 0xE9 and d[f+5:f+7] == b"\x90\x90", "ww-hook not e9+2nop"

    # --- the 14px atlas in .cjk must match atlas12's dense count (same encoding) ---
    e = struct.unpack_from('<I', d, 0x3c)[0]; coff = e + 4
    nsec = struct.unpack_from('<H', d, coff+2)[0]; osz = struct.unpack_from('<H', d, coff+16)[0]
    opt = coff + 20; st = opt + osz
    soi = struct.unpack_from('<I', d, opt+56)[0]; hdrs = struct.unpack_from('<I', d, opt+60)[0]
    cjk = next(st+i*40 for i in range(nsec) if d[st+i*40:st+i*40+8].rstrip(b'\0') == b'.cjk')
    cjk_ro = struct.unpack_from('<I', d, cjk+20)[0]
    a14_count = struct.unpack_from('<I', d, cjk_ro+0x200+4)[0]
    assert a14_count == a12_count, f"atlas14 count {a14_count} != atlas12 count {a12_count}"
    maxlead = LEAD0 + (a12_count - 1)//TRAILW

    # --- new .b12 section geometry ---
    hdr_off = st + nsec*40
    assert hdr_off + 40 <= hdrs, "no header room"
    assert all(x == 0 for x in d[hdr_off:hdr_off+40]), "header slot not zero"
    new_rva = (soi + SECT_ALIGN - 1) & ~(SECT_ALIGN - 1)
    base = IMAGE_BASE + new_rva
    raw_off = len(d)
    assert raw_off % FILE_ALIGN == 0

    FLAG_VA    = base + 0
    atlas12_va = base + 0x10
    code_off   = (0x10 + len(atlas12) + 15) & ~15
    code_va    = base + code_off

    # measure ww bodies (length is org-independent), then place at final VAs
    L_main = len(nasm(ww_body(0, ATLAS14_VA, 14, maxlead, a12_count), scratch, "wwm0"))
    L_brief= len(nasm(ww_body(0, atlas12_va, brief_font_h, maxlead, a12_count), scratch, "wwb0"))
    wwmain_va  = code_va + 13                 # after dispatch (cmp[7] + jne rel32[6])
    wwbrief_va = wwmain_va + L_main
    tramp_va   = wwbrief_va + L_brief

    dispatch = nasm(f"""bits 32
org {code_va:#x}
    cmp byte [{FLAG_VA:#x}], 0
    jne {wwbrief_va:#x}
""", scratch, "b12_disp")
    assert len(dispatch) == 13, f"dispatch {len(dispatch)}B != 13"
    wwmain = nasm(ww_body(wwmain_va, ATLAS14_VA, 14, maxlead, a12_count), scratch, "b12_wwm")
    wwbrief= nasm(ww_body(wwbrief_va, atlas12_va, brief_font_h, maxlead, a12_count), scratch, "b12_wwb")
    assert len(wwmain) == L_main and len(wwbrief) == L_brief
    tramp = nasm(f"""bits 32
org {tramp_va:#x}
    mov byte [{FLAG_VA:#x}], 1
    call {VA_460193:#x}
    mov byte [{FLAG_VA:#x}], 0
    ret
""", scratch, "b12_tramp")
    code = dispatch + wwmain + wwbrief + tramp

    # assemble section body: [flag+pad][atlas12][pad][code]
    body = bytearray(code_off)
    body[0] = 0                                # flag init 0
    body[0x10:0x10+len(atlas12)] = atlas12
    body[code_off:code_off+len(code)] = code
    vsize = len(body)
    raw_size = (vsize + FILE_ALIGN - 1) & ~(FILE_ALIGN - 1)
    body += bytes(raw_size - vsize)

    # append section header (WRITE|EXECUTE|READ -- writable for the flag)
    new_hdr = b".b12".ljust(8, b"\0") + struct.pack('<IIII', vsize, new_rva, raw_size, raw_off) \
              + struct.pack('<IIHHI', 0, 0, 0, 0, 0xE0000020)
    d[hdr_off:hdr_off+40] = new_hdr
    struct.pack_into('<H', d, coff+2, nsec + 1)
    new_soi = new_rva + ((vsize + SECT_ALIGN - 1) & ~(SECT_ALIGN - 1))
    struct.pack_into('<I', d, opt+56, new_soi)
    d += body

    # (a) repoint the WWSTUB hook rel32 -> dispatch
    f = va2file(VA_WW_HOOK)
    d[f+1:f+5] = struct.pack('<i', code_va - (VA_WW_HOOK + 5))
    # (b) redirect the two briefing render calls -> trampoline
    for va in RENDER_CALLS:
        fo = va2file(va)
        d[fo+1:fo+5] = struct.pack('<i', tramp_va - (va + 5))
        assert va + 5 + struct.unpack_from('<i', d, fo+1)[0] == tramp_va
    # (c) box-height ×10 -> ×box_pitch in both drawers (imul eax,eax,box_pitch ; nop ; nop).
    #     box_pitch is a byte immediate (1..127); assert it fits.
    assert 1 <= box_pitch <= 127, f"box_pitch {box_pitch} out of imm8 range"
    newboxh = bytes([0x6b, 0xc0, box_pitch, 0x90, 0x90])   # imul eax,eax,box_pitch ; nop ; nop
    for va in BOXH_SITES:
        d[va2file(va):va2file(va)+5] = newboxh

    open(exe_out, "wb").write(d)
    print(f"[b12] .b12 RVA {new_rva:#x} (VA {base:#x}) vsz {vsize:#x} raw@{raw_off:#x}  SizeOfImage {soi:#x}->{new_soi:#x}")
    print(f"[b12] atlas12 {len(atlas12)}B @{atlas12_va:#x} (count={a12_count}, H={a12_h}, maxlead 0x{maxlead:02x})")
    print(f"[b12] FLAG @{FLAG_VA:#x}  dispatch @{code_va:#x}  ww_main(14px) @{wwmain_va:#x}  ww_brief({brief_font_h}px) @{wwbrief_va:#x}  tramp @{tramp_va:#x}")
    print(f"[b12] WWSTUB hook @{VA_WW_HOOK:#x} -> dispatch;  render calls {[hex(v) for v in RENDER_CALLS]} -> tramp")
    print(f"[b12] box-height ×10 -> ×{box_pitch} @ {[hex(v) for v in BOXH_SITES]} "
          f"(render line pitch = {brief_font_h+2}; extra slack for countLines under-count)")
    print(f"[b12] wrote {exe_out} ({len(d)} bytes)  md5={__import__('hashlib').md5(d).hexdigest()}")


if __name__ == "__main__":
    exe_in, atlas12, exe_out = sys.argv[1], sys.argv[2], sys.argv[3]
    scratch = sys.argv[4] if len(sys.argv) > 4 else "/tmp"
    bfh = int(sys.argv[5]) if len(sys.argv) > 5 else 12
    bpitch = int(sys.argv[6]) if len(sys.argv) > 6 else None
    build(exe_in, atlas12, exe_out, scratch, brief_font_h=bfh, box_pitch=bpitch)

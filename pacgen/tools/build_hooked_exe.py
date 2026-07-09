#!/usr/bin/env python3
"""build_hooked_exe.py — append a .cjk PE section (2 hook stubs + atlas) to
PACGEN.EXE and patch the two custom-bitmap-font draw paths for 2-byte CJK.

Path 1 — drawString @ 0x428312 (menus/buttons/short strings). Loop head
0x428322 `movzx eax,[esi]` overwritten with jmp STUB1. STUB1: lead byte
0x81-0x86 -> dense atlas index -> drawGlyph(font=atlas), esi+=2; else replay
original ASCII drawGlyph, esi+=1; both jmp back to terminator test 0x42833e.

Path 2 — word-wrap RENDER loop @ 0x4ac2e9 (multi-line briefings/unit info,
0x4abf46). Reads a 2D char grid 0x4e1a60 (stride 258). Loop head 0x4ac2e9
`xor eax,eax; mov al,[ebp-0xc]` (5 bytes) overwritten with jmp STUB2. STUB2
re-reads grid[line*258+col]; 0 -> end-of-line 0x4ac38a; lead 0x81-0x86 -> read
next cell as trail, dense, set color, drawGlyph(font=atlas), col+=2, loop;
else fall through to original ASCII draw at 0x4ac30d.

Layout of .cjk (VA 0x603000): STUB1 @0x603000, XLAT_BUF @0x603300, STUB2 @0x603200,
atlas @0x603400. Fixed-base EXE -> absolute immediates need no relocations.

xlat handling (drawGlyph writes xlat[pixel] unless it is 0xff = transparent). The atlas
uses the NATIVE TFONT1 convention: glyph strokes (fg) = pixel 0x00, empty (bg) = 0xff.
Every game caller sets xlat[0x00] = text color and leaves xlat[0xff] = 0xff, so the
atlas renders like the game's own text through any caller's xlat.
  * drawString path: pass the caller's xlat straight through (fg 0x00 -> xlat[0x00] =
    color, bg 0xff -> transparent). No private xlat needed.
  * word-wrap path: its font uses fg pixel 0x01 (game writes color into xlat[0x01]),
    not 0x00, so STUB2 builds a private XLAT_BUF with [0x00] = the per-cell grid color
    (atlas fg) and [0xff] = 0xff (prefill, transparent bg). The .cjk section is writable
    because STUB2 rewrites XLAT_BUF[0x00] on every glyph.
"""
import struct, subprocess, os, sys

VA_HOOK      = 0x428322       # drawString loop head (overwrite 5 bytes)
VA_TERMTEST  = 0x42833e       # drawString `cmp [esi],0` — STUB1 returns here
VA_DRAWGLYPH = 0x42817f       # drawGlyph(dest,x,y,font,ch,xlat)

# word-wrap RENDER path
VA_WW_HOOK   = 0x4ac2e9       # render loop head (overwrite 5 bytes: 33 c0 8a 45 f4)
VA_WW_ASCII  = 0x4ac30d       # original single-byte draw path (fall through)
VA_WW_ENDLN  = 0x4ac38a       # end-of-line (char == 0)
GRID_CHAR    = 0x4e1a60       # 2D char grid base (stride 258)
GRID_COLOR   = 0x4e1ae0       # 2D color grid base
WW_COLOR_SET = 0x5e5b61       # current color byte
WW_XLAT      = 0x5e5b60       # xlat table arg
WW_DEST      = 0x5e5c70       # dest surface

TEXT_VA_BASE = 0x401000
TEXT_RAW     = 0x400          # file = VA - 0x401000 + 0x400

IMAGE_BASE   = 0x400000
SECT_ALIGN   = 0x1000
FILE_ALIGN   = 0x200
CJK_RVA      = 0x203000       # new section RVA (VA 0x603000); == old SizeOfImage
STUB1_OFF    = 0x000
STUB2_OFF    = 0x200
XLAT_OFF     = 0x300         # 256-byte custom xlat (0x00->transparent, 0xff->text color)
ATLAS_OFF    = 0x400
STUB1_VA     = IMAGE_BASE + CJK_RVA + STUB1_OFF   # 0x603000
STUB2_VA     = IMAGE_BASE + CJK_RVA + STUB2_OFF   # 0x603200
XLAT_VA      = IMAGE_BASE + CJK_RVA + XLAT_OFF    # 0x603300
ATLAS_VA     = IMAGE_BASE + CJK_RVA + ATLAS_OFF   # 0x603400

LEAD0, TRAIL0, TRAILW = 0x81, 0xA1, 94

def va2file(va):
    return va - TEXT_VA_BASE + TEXT_RAW

def nasm(asm, scratch, tag):
    src = os.path.join(scratch, f"{tag}.asm"); binf = os.path.join(scratch, f"{tag}.bin")
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    return open(binf, "rb").read()

def assemble_stub1(scratch):
    asm = f"""bits 32
org {STUB1_VA:#x}
    movzx eax, byte [esi]
    cmp al, {LEAD0:#x}
    jb .ascii
    cmp al, {LEAD0 + 5:#x}
    ja .ascii
    movzx ebx, al
    sub ebx, {LEAD0:#x}
    imul ebx, ebx, {TRAILW}
    movzx eax, byte [esi+1]
    sub eax, {TRAIL0:#x}
    add eax, ebx                    ; eax = dense
    ; The atlas now uses the native font convention (fg pixel 0x00, bg pixel 0xff),
    ; so passing the caller's own xlat straight through renders CJK exactly like the
    ; game's own text: fg 0x00 -> xlat[0x00] = text color, bg 0xff -> xlat[0xff] = 0xff
    ; = transparent. Works for every drawString caller, no fixup / private xlat needed.
    push dword [ebp+0x1c]           ; xlat (caller's, pass-through)
    push eax                        ; ch = dense
    push {ATLAS_VA:#x}
    push dword [ebp+0x10]
    push edi
    push dword [ebp+0x8]
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    add edi, eax
    add esi, 2
    jmp {VA_TERMTEST:#x}
.ascii:
    push dword [ebp+0x1c]
    push eax
    push dword [ebp+0x14]
    push dword [ebp+0x10]
    push edi
    push dword [ebp+0x8]
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    add edi, eax
    inc esi
    jmp {VA_TERMTEST:#x}
"""
    stub = nasm(asm, scratch, "stub1")
    assert len(stub) <= STUB2_OFF, f"stub1 {len(stub)}B exceeds {STUB2_OFF}B"
    return stub

def assemble_stub2(scratch):
    # ecx = line*258, eax = col; grid char at [eax+ecx+GRID_CHAR]
    asm = f"""bits 32
org {STUB2_VA:#x}
    xor eax, eax
    mov al, [ebp-0xc]              ; col
    xor ecx, ecx
    mov cl, [ebp-0x18]            ; line
    mov edx, ecx
    shl ecx, 8
    add ecx, edx
    add ecx, edx                  ; ecx = line*258
    xor edx, edx
    mov dl, [eax+ecx+{GRID_CHAR:#x}]   ; char
    test edx, edx
    je .endline
    cmp dl, {LEAD0:#x}
    jb .ascii
    cmp dl, {LEAD0 + 5:#x}
    ja .ascii
    ; --- CJK: dense = (dl-0x81)*94 + (trail-0xA1) ---
    movzx ebx, dl
    sub ebx, {LEAD0:#x}
    imul ebx, ebx, {TRAILW}
    mov dl, [eax+ecx+{GRID_CHAR + 1:#x}]   ; trail (col+1)
    movzx edx, dl
    sub edx, {TRAIL0:#x}
    add ebx, edx                  ; ebx = dense
    mov dl, [eax+ecx+{GRID_COLOR:#x}]      ; grid color byte = text palette index
    ; The atlas fg pixel is 0x00 and bg is 0xff. Map atlas fg -> this glyph's color via
    ; XLAT_BUF[0x00]; XLAT_BUF[0xff] stays 0xff (prefill) so atlas bg 0xff -> transparent.
    mov [{XLAT_VA:#x}], dl
    ; drawGlyph(dest, x=[ebp-0x1c], y=[ebp-0x10], font=atlas, ch=dense, xlat=XLAT_BUF)
    push {XLAT_VA:#x}
    push ebx
    push {ATLAS_VA:#x}
    mov eax, [ebp-0x10]
    and eax, 0xffff
    push eax
    mov eax, [ebp-0x1c]
    and eax, 0xffff
    push eax
    push {WW_DEST:#x}
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    mov ecx, [ebp-0x1c]
    and ecx, 0xffff
    add eax, ecx
    mov [ebp-0x1c], ax
    inc byte [ebp-0xc]
    inc byte [ebp-0xc]
    jmp {VA_WW_HOOK:#x}
.ascii:
    jmp {VA_WW_ASCII:#x}
.endline:
    jmp {VA_WW_ENDLN:#x}
"""
    stub = nasm(asm, scratch, "stub2")
    assert len(stub) <= ATLAS_OFF - STUB2_OFF, f"stub2 {len(stub)}B too big"
    return stub

def build(exe_in, atlas_path, exe_out, scratch, ww_hook=True):
    d = bytearray(open(exe_in, "rb").read())
    atlas = open(atlas_path, "rb").read()
    stub1 = assemble_stub1(scratch)
    stub2 = assemble_stub2(scratch) if ww_hook else b""

    e_lfanew = struct.unpack('<I', d[0x3c:0x40])[0]
    coff = e_lfanew + 4
    nsec = struct.unpack('<H', d[coff+2:coff+4])[0]
    opt_size = struct.unpack('<H', d[coff+16:coff+18])[0]
    opt = coff + 20
    size_of_image = struct.unpack('<I', d[opt+56:opt+60])[0]
    sect_table = opt + opt_size
    assert CJK_RVA == size_of_image, f"CJK_RVA {CJK_RVA:#x} != SizeOfImage {size_of_image:#x}"

    sect = bytearray(ATLAS_OFF)
    sect[STUB1_OFF:STUB1_OFF+len(stub1)] = stub1
    if stub2:
        sect[STUB2_OFF:STUB2_OFF+len(stub2)] = stub2
    sect[XLAT_OFF:XLAT_OFF+256] = b"\xff" * 256   # custom xlat: bg->transparent (both stubs use it)
    sect += atlas
    vsize = len(sect)
    raw_off = len(d)
    assert raw_off % FILE_ALIGN == 0
    raw_size = (vsize + FILE_ALIGN - 1) & ~(FILE_ALIGN - 1)
    sect += bytes(raw_size - vsize)

    hdr_off = sect_table + nsec * 40
    assert hdr_off + 40 <= struct.unpack('<I', d[opt+60:opt+64])[0], "no header room"
    # CODE|EXEC|READ|WRITE (0xE0000020): stubs write the current text color into
    # the custom xlat buffer each glyph, so the section must be writable.
    new_hdr = b".cjk".ljust(8, b"\0") + struct.pack('<IIII', vsize, CJK_RVA, raw_size, raw_off) \
              + struct.pack('<IIHHI', 0, 0, 0, 0, 0xE0000020)
    d[hdr_off:hdr_off+40] = new_hdr
    struct.pack_into('<H', d, coff+2, nsec + 1)
    new_size_of_image = CJK_RVA + ((vsize + SECT_ALIGN - 1) & ~(SECT_ALIGN - 1))
    struct.pack_into('<I', d, opt+56, new_size_of_image)

    # patch 1: drawString loop head
    hf = va2file(VA_HOOK)
    assert bytes(d[hf:hf+5]) == bytes.fromhex("0fb606ff75"), bytes(d[hf:hf+5]).hex()
    d[hf:hf+5] = b"\xe9" + struct.pack('<i', STUB1_VA - (VA_HOOK + 5))

    # patch 2: word-wrap RENDER loop head
    if ww_hook:
        wf = va2file(VA_WW_HOOK)
        assert bytes(d[wf:wf+5]) == bytes.fromhex("33c08a45f4"), bytes(d[wf:wf+5]).hex()
        d[wf:wf+5] = b"\xe9" + struct.pack('<i', STUB2_VA - (VA_WW_HOOK + 5))

    d += sect
    open(exe_out, "wb").write(d)
    print(f"[hook] STUB1 {len(stub1)}B @{STUB1_VA:#x}  STUB2 {len(stub2)}B @{STUB2_VA:#x}  atlas {len(atlas)}B @{ATLAS_VA:#x}")
    print(f"[hook] .cjk RVA {CJK_RVA:#x} VSize {vsize:#x}  SizeOfImage {size_of_image:#x}->{new_size_of_image:#x}")
    print(f"[hook] drawString hook @{VA_HOOK:#x}" + (f" + word-wrap hook @{VA_WW_HOOK:#x}" if ww_hook else ""))
    print(f"[hook] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    exe_in, atlas, exe_out = sys.argv[1], sys.argv[2], sys.argv[3]
    scratch = sys.argv[4] if len(sys.argv) > 4 else "/tmp"
    ww = "--no-ww" not in sys.argv
    build(exe_in, atlas, exe_out, scratch, ww_hook=ww)

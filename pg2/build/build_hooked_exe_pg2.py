#!/usr/bin/env python3
"""build_hooked_exe_pg2.py — append a .cjk PE section (STUB1 + CJK atlas) to
PANZER2.EXE, patch the drawStringCore loop for 2-byte CJK, and flip the language
default byte to French (so the game loads *.fra data + fontfra font slot).

drawStringCore @0x43e612 loop (index-based, ebp-relative):
  i=[ebp-0x10](word), str=[ebp+0x14], penX=[ebp+8](word), y=[ebp+0xc](word),
  xlat=[ebp+0x10], dest=[ebp+0x18].  Native reads str[i] with movsx (sign-extend),
  so bytes 0x80-0xFF are < 0x20 (signed) and never drawn -> 2-byte hook is safe.
Hook site 0x43e699 (`0f bf 45 f0 8b 4d 14`): overwrite first 5 bytes with jmp STUB1.
  CJK (lead 0x81..maxlead): dense atlas index -> drawGlyph(font=atlas), penX +=
    glyphWidth(atlas,dense), inc i once, jmp back-edge 0x43e685 (its own inc => i+=2).
  ASCII (else): eax = movsx(str[i]); jmp 0x43e6a4 (rejoin native path, zero change).
drawGlyph(dest,x,y,font,ch,xlat) @0x41b033 ; glyphWidth(font,ch) @0x41b013.
Stub uses only eax/ecx/edx (ebx/esi/edi hold the caller's saved regs, restored at
the function epilogue, so they must NOT be clobbered).
"""
import struct, subprocess, os, sys

# --- drawStringCore contract ---
VA_HOOK       = 0x43e699      # overwrite 5 bytes (0f bf 45 f0 8b)
VA_ASCII      = 0x43e6a4      # ASCII rejoin (cmp eax,0x20)
VA_BACKEDGE   = 0x43e685      # inc word [ebp-0x10]; then loop test
VA_DRAWGLYPH  = 0x41b033
VA_GLYPHWIDTH = 0x41b013

# --- PE geometry (ImageBase 0x400000, DYNAMICBASE off) ---
IMAGE_BASE = 0x400000
SECT_ALIGN = 0x1000
FILE_ALIGN = 0x200
CJK_RVA    = 0x17f000         # == SizeOfImage of stock PANZER2.EXE
STUB1_OFF  = 0x000
GWCLAMP_OFF= 0x180
ATLAS_OFF  = 0x200
STUB1_VA   = IMAGE_BASE + CJK_RVA + STUB1_OFF   # 0x57f000
GWCLAMP_VA = IMAGE_BASE + CJK_RVA + GWCLAMP_OFF # 0x57f180
ATLAS_VA   = IMAGE_BASE + CJK_RVA + ATLAS_OFF   # 0x57f200
VA_GLYPHWIDTH_HOOK = 0x41b013                   # glyphWidth entry (55 8b ec 53 56)
TEXT_VA_BASE = 0x401000
TEXT_RAW     = 0x400
LANG_FILE_OFF = 0xa32a0       # .data byte, 0x09(EN)->0x0C(FR)

LEAD0, TRAIL0, TRAILW = 0x81, 0xA1, 94

# measure char-read (movsx eax, byte ...) sites that feed a glyphWidth width-measure whose
# function then DRAWS via drawStringCore (my hook). Flipping these to movzx de-crashes CJK.
MEASURE_FIX_VAS = [0x43eb6d, 0x43eca4, 0x43fd1d, 0x43ff3c, 0x44001e]

# --- word-wrap (drawWrappedText @0x43e752, the briefing/multi-line path) 2-byte hook ---
# The render loop processes str[i] one byte at a time (i = word[ebp-0x1c]); it draws via
# drawGlyph(dest,x,y,[0x4d74c4],ch,color) at 0x43e9e1 and advances x by glyphWidth.  We hook
# the per-char classify/render entry 0x43e955 (`cmp dword[0x4ba744],1`, 7 bytes, a clean
# branch target): a CJK lead byte -> draw the dense atlas glyph, advance x by the fixed 16px
# atlas width, wrap at the rect edge, and skip the trail byte; anything else replays the
# overwritten cmp and rejoins the native ASCII path at 0x43e95c.  Frame (ebp-relative):
#   i=[ebp-0x1c]  str=[ebp+0x10]  penX=[ebp-0x14]  penY=[ebp-0x18]  line=[ebp-0x20]
#   rectWidth=[ebp-0x28]  lineHeight=[ebp-0xc]  dest=[ebp+0x14]  color=[ebp+0xc]
VA_WW_HOOK        = 0x43e955   # overwrite 7 bytes (83 3d 44 a7 4b 00 01)
VA_WW_ASCII       = 0x43e95c   # rejoin (jle 0x43e983) after replaying the cmp
VA_WW_BACKEDGE    = 0x43e804   # inc word[ebp-0x1c]; loop test
WW_G_0x4ba744     = 0x4ba744   # DBCS-mode flag read by the replayed cmp

# --- scenario-list TITLE truncation fix (readScenarioTitle @0x43dd0c) ---
# Its per-byte classifier at 0x43dde0..0x43de39 (both the DBCS _isctype path and the direct
# _pctype-table path) terminates the title's first line at the first byte whose ctype class
# (& 0x157) is 0.  A high byte gets a nonsense class via a signed-char table underflow, so many
# dense 2-byte CJK codes read as "class 0" and cut the title to 1-3 chars.  Fix: overwrite the
# classifier with one that yields class 0 ONLY for the real line terminators \0 / \r / \n, so no
# high byte ever truncates.  Stop test kept at 0x43de3a: `cmp [ebp-0x118],0 ; je end`.
# Frame: i=word[ebp-0x10c], title buffer base=[ebp-8], class out dword[ebp-0x118].
VA_TITLECLASS  = 0x43dde0
TITLECLASS_LEN = 0x43de3a - VA_TITLECLASS   # 90 bytes (up to, not incl, the stop test)
TITLECLASS_ORIG_HEAD = bytes.fromhex("833d44a74b00010f")  # cmp [0x4ba744],1 ; jle ...

def va2file(va): return va - TEXT_VA_BASE + TEXT_RAW

def assemble_titleclass(scratch):
    asm = f"""bits 32
org {VA_TITLECLASS:#x}
    movsx eax, word [ebp-0x10c]     ; eax = i
    mov   ecx, [ebp-8]              ; ecx = title buffer base
    movzx eax, byte [ecx+eax]       ; al = str[i] (unsigned)
    mov   dword [ebp-0x118], 1      ; class = 1 (keep) by default
    test  al, al                    ; NUL?
    jz    .stop
    cmp   al, 0x0d                  ; CR?
    jz    .stop
    cmp   al, 0x0a                  ; LF?
    jz    .stop
    jmp   .done
.stop:
    mov   dword [ebp-0x118], 0      ; class = 0 -> terminate the line
.done:
"""
    return nasm(asm, scratch, "titleclass_pg2")

def nasm(asm, scratch, tag):
    src = os.path.join(scratch, f"{tag}.asm"); binf = os.path.join(scratch, f"{tag}.bin")
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    return open(binf, "rb").read()

def assemble_stub1(scratch, maxlead, count):
    asm = f"""bits 32
org {STUB1_VA:#x}
    movsx eax, word [ebp-0x10]        ; i
    mov ecx, [ebp+0x14]               ; str base
    movzx edx, byte [ecx+eax]         ; lead = str[i] (unsigned)
    cmp dl, {LEAD0:#x}
    jb .ascii
    cmp dl, {maxlead:#x}
    ja .ascii
    ; --- trail guard: a lone/split 0x81 (game-truncated label, stray high byte) must
    ;     NOT be treated as CJK; the native loop skipped such bytes via movsx. edx holds
    ;     the lead and survives this load, so no recompute is needed.
    movzx eax, byte [ecx+eax+1]       ; eax = trail = str[i+1]  (edx still = lead)
    cmp al, {TRAIL0:#x}               ; trail < 0xA1 -> invalid
    jb .ascii
    cmp al, 0xfe                      ; trail > 0xFE -> invalid
    ja .ascii
    ; --- CJK draw: dense = (lead-0x81)*94 + (trail-0xA1) ---
    sub edx, {LEAD0:#x}
    imul edx, edx, {TRAILW}
    sub eax, {TRAIL0:#x}
    add edx, eax                      ; edx = dense
    cmp edx, {count}                  ; dense-bound guard (out-of-atlas -> ascii)
    jae .ascii
    push dword [ebp+0x10]             ; xlat (caller pass-through)
    push edx                          ; ch = dense
    push {ATLAS_VA:#x}                ; font = atlas
    movsx eax, word [ebp+0xc]
    push eax                          ; y
    movsx eax, word [ebp+8]
    push eax                          ; x = penX
    push dword [ebp+0x18]             ; dest
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    ; --- penX += glyphWidth(atlas, dense) ; recompute dense (regs clobbered) ---
    movsx eax, word [ebp-0x10]
    mov ecx, [ebp+0x14]
    movzx edx, byte [ecx+eax]
    movzx eax, byte [ecx+eax+1]
    sub edx, {LEAD0:#x}
    imul edx, edx, {TRAILW}
    sub eax, {TRAIL0:#x}
    add edx, eax                      ; dense
    push edx
    push {ATLAS_VA:#x}
    call {VA_GLYPHWIDTH:#x}
    add esp, 8
    movsx eax, ax                     ; width
    movsx ecx, word [ebp+8]           ; penX
    add eax, ecx
    mov [ebp+8], ax                   ; penX += width
    inc word [ebp-0x10]               ; consume 1 byte; back-edge consumes the 2nd
    jmp {VA_BACKEDGE:#x}
.ascii:
    movsx eax, word [ebp-0x10]
    mov ecx, [ebp+0x14]
    movsx eax, byte [ecx+eax]         ; eax = signed str[i] (native semantics)
    jmp {VA_ASCII:#x}
"""
    stub = nasm(asm, scratch, "stub1_pg2")
    assert len(stub) <= ATLAS_OFF, f"stub1 {len(stub)}B exceeds {ATLAS_OFF}B"
    return stub

def assemble_gwclamp(scratch):
    # glyphWidth(font, ch): callers that measure width read the char with movsx, so a high
    # byte -> negative ch -> font+0x10+ch*4 reads below the font table -> fault @0x41b02b.
    # Hook the entry, mask ch to a byte (in-range), replay the 5 overwritten bytes, continue.
    asm = f"""bits 32
org {GWCLAMP_VA:#x}
    and dword [esp+8], 0xff       ; clamp ch arg to 0..255 (esp still at ret; +4=font,+8=ch)
    push ebp
    mov ebp, esp
    push ebx
    push esi
    jmp {VA_GLYPHWIDTH_HOOK+5:#x}
"""
    return nasm(asm, scratch, "gwclamp")

def assemble_wwstub(scratch, va, maxlead, count):
    # va = absolute VA where this stub is placed (after the atlas). All atlas glyphs are 16px
    # wide, so advance is a fixed +16 (no glyphWidth call -> immune to the gw-clamp byte-mask).
    asm = f"""bits 32
org {va:#x}
    movsx eax, word [ebp-0x1c]        ; i
    mov ecx, [ebp+0x10]               ; str base
    movzx edx, byte [ecx+eax]         ; lead = str[i]
    cmp dl, {LEAD0:#x}
    jb .ascii
    cmp dl, {maxlead:#x}
    ja .ascii
    movzx eax, byte [ecx+eax+1]       ; trail = str[i+1]
    cmp al, {TRAIL0:#x}
    jb .ascii
    cmp al, 0xfe
    ja .ascii
    sub edx, {LEAD0:#x}
    imul edx, edx, {TRAILW}
    sub eax, {TRAIL0:#x}
    add edx, eax                      ; edx = dense
    cmp edx, {count}
    jae .ascii
    ; wrap: if penX + 16 > rectWidth -> new line (penX=0, penY+=lineHeight, line++)
    movsx eax, word [ebp-0x14]
    add eax, 16
    movsx ecx, word [ebp-0x28]
    cmp eax, ecx
    jle .nowrap
    mov word [ebp-0x14], 0
    movsx eax, word [ebp-0x18]
    add eax, 18                       ; CJK line height (16px glyph + 2px lead); the native
    mov [ebp-0x18], ax                ; lineHeight [ebp-0xc]=~10 is for the 8px game font
    inc word [ebp-0x20]
.nowrap:
    push dword [ebp+0xc]              ; color
    push edx                          ; ch = dense
    push {ATLAS_VA:#x}                ; font = atlas
    movsx eax, word [ebp-0x18]
    push eax                          ; y = penY
    movsx eax, word [ebp-0x14]
    push eax                          ; x = penX
    push dword [ebp+0x14]             ; dest
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    mov ax, [ebp-0x14]
    add ax, 16                        ; penX += 16 (fixed atlas advance)
    mov [ebp-0x14], ax
    inc word [ebp-0x1c]              ; consume trail; back-edge consumes lead
    jmp {VA_WW_BACKEDGE:#x}
.ascii:
    cmp dword [{WW_G_0x4ba744:#x}], 1 ; replay the overwritten instruction
    jmp {VA_WW_ASCII:#x}
"""
    return nasm(asm, scratch, "wwstub_pg2")


def build(exe_in, atlas_path, exe_out, scratch, lang_patch=True, ww_safe=False, measure_fix=False, gw_clamp=False, ww_hook=False, title_fix=True):
    d = bytearray(open(exe_in, "rb").read())
    atlas = open(atlas_path, "rb").read()
    atlas_count = struct.unpack('<I', atlas[4:8])[0]
    maxlead = LEAD0 + (atlas_count - 1) // TRAILW
    assert maxlead <= 0xFE
    stub1 = assemble_stub1(scratch, maxlead, atlas_count)
    gwclamp = assemble_gwclamp(scratch) if gw_clamp else b""

    e_lfanew = struct.unpack('<I', d[0x3c:0x40])[0]
    coff = e_lfanew + 4
    nsec = struct.unpack('<H', d[coff+2:coff+4])[0]
    opt_size = struct.unpack('<H', d[coff+16:coff+18])[0]
    opt = coff + 20
    size_of_image = struct.unpack('<I', d[opt+56:opt+60])[0]
    size_of_headers = struct.unpack('<I', d[opt+60:opt+64])[0]
    sect_table = opt + opt_size
    assert CJK_RVA == size_of_image, f"CJK_RVA {CJK_RVA:#x} != SizeOfImage {size_of_image:#x}"

    sect = bytearray(ATLAS_OFF)
    sect[STUB1_OFF:STUB1_OFF+len(stub1)] = stub1
    if gwclamp:
        assert GWCLAMP_OFF + len(gwclamp) <= ATLAS_OFF and GWCLAMP_OFF >= STUB1_OFF + len(stub1)
        sect[GWCLAMP_OFF:GWCLAMP_OFF+len(gwclamp)] = gwclamp
    sect += atlas
    wwstub = b""
    if ww_hook:
        ww_off = (len(sect) + 15) & ~15          # 16-align after the atlas
        sect += bytes(ww_off - len(sect))
        WWSTUB_VA = IMAGE_BASE + CJK_RVA + ww_off
        wwstub = assemble_wwstub(scratch, WWSTUB_VA, maxlead, atlas_count)
        sect += wwstub
        print(f"[ww-hook] WWSTUB {len(wwstub)}B @{WWSTUB_VA:#x} (off {ww_off:#x})")
    vsize = len(sect)
    raw_off = len(d)
    assert raw_off % FILE_ALIGN == 0, f"raw_off {raw_off:#x} not file-aligned"
    raw_size = (vsize + FILE_ALIGN - 1) & ~(FILE_ALIGN - 1)
    sect += bytes(raw_size - vsize)

    hdr_off = sect_table + nsec * 40
    assert hdr_off + 40 <= size_of_headers, "no room for new section header"
    # CODE|EXEC|READ (0x60000020). Read-only is enough: STUB1 passes the caller's xlat
    # through and never writes into .cjk (unlike PacGen's word-wrap stub).
    new_hdr = b".cjk".ljust(8, b"\0") + struct.pack('<IIII', vsize, CJK_RVA, raw_size, raw_off) \
              + struct.pack('<IIHHI', 0, 0, 0, 0, 0x60000020)
    d[hdr_off:hdr_off+40] = new_hdr
    struct.pack_into('<H', d, coff+2, nsec + 1)
    new_size_of_image = CJK_RVA + ((vsize + SECT_ALIGN - 1) & ~(SECT_ALIGN - 1))
    struct.pack_into('<I', d, opt+56, new_size_of_image)

    # patch 1: drawStringCore hook
    hf = va2file(VA_HOOK)
    assert bytes(d[hf:hf+5]) == bytes.fromhex("0fbf45f08b"), bytes(d[hf:hf+5]).hex()
    d[hf:hf+5] = b"\xe9" + struct.pack('<i', STUB1_VA - (VA_HOOK + 5))

    # patch GW-CLAMP: hook glyphWidth entry so any negative ch is masked to a byte (universal
    # crash guard for every measure loop, no per-site movsx patching needed).
    if gwclamp:
        gf = va2file(VA_GLYPHWIDTH_HOOK)
        assert bytes(d[gf:gf+5]) == bytes.fromhex("558bec5356"), bytes(d[gf:gf+5]).hex()
        d[gf:gf+5] = b"\xe9" + struct.pack('<i', GWCLAMP_VA - (VA_GLYPHWIDTH_HOOK + 5))
        print(f"[gw-clamp] glyphWidth entry @{VA_GLYPHWIDTH_HOOK:#x} -> clamp stub @{GWCLAMP_VA:#x} ({len(gwclamp)}B)")

    # patch WW-SAFE: neutralize the word-wrap function's crash on high bytes so navigation
    # doesn't die. Its 10 char reads use `movsx eax,byte[eax+ecx]` (0f be 04 08); a high byte
    # -> negative -> glyphWidth(font,negative) faults @0x41b02b. Rewriting to movzx (0f b6 04 08)
    # keeps ch in 0..255 (in-range, no fault). CJK there renders as game-font glyphs (not CJK),
    # but this is only to keep the UI alive while proving the drawStringCore (main hook) path.
    if ww_safe:
        pat_from = bytes.fromhex("0fbe0408"); pat_to = bytes.fromhex("0fb60408")
        lo, hi = va2file(0x43e7f3), va2file(0x43ea60)
        n = 0
        i = lo
        while i < hi:
            if d[i:i+4] == pat_from:
                d[i:i+4] = pat_to; n += 1; i += 4
            else:
                i += 1
        print(f"[ww-safe] rewrote {n} movsx->movzx char reads in word-wrap 0x43e7f3..0x43ea60")

    # measure-fix: some text drawers MEASURE width with glyphWidth(font, movsx(char)) — which
    # faults on a high byte — but then DRAW via drawStringCore (which my hook already makes
    # CJK-aware). Flipping just the measure char-read movsx->movzx (0f be -> 0f b6) stops the
    # fault; centering is ~1px off but the drawStringCore draw renders proper CJK.
    if measure_fix:
        for va in MEASURE_FIX_VAS:
            fo = va2file(va)
            assert d[fo:fo+2] == b"\x0f\xbe", f"@{va:#x} not movsx: {d[fo:fo+2].hex()}"
            d[fo+1] = 0xb6
        print(f"[measure-fix] {len(MEASURE_FIX_VAS)} glyphWidth-measure movsx->movzx: "
              + ",".join(hex(v) for v in MEASURE_FIX_VAS))

    # patch WW-HOOK: overwrite the per-char classify/render entry with jmp WWSTUB (5 bytes)
    # + 2 nop (original `cmp dword[0x4ba744],1` is 7 bytes). Coexists with ww-safe: CJK is
    # handled by WWSTUB, ASCII replays the cmp and continues on the (movzx-safe) native path.
    if ww_hook:
        wf = va2file(VA_WW_HOOK)
        assert bytes(d[wf:wf+7]) == bytes.fromhex("833d44a74b0001"), bytes(d[wf:wf+7]).hex()
        d[wf:wf+5] = b"\xe9" + struct.pack('<i', WWSTUB_VA - (VA_WW_HOOK + 5))
        d[wf+5:wf+7] = b"\x90\x90"
        print(f"[ww-hook] drawWrappedText render hook @{VA_WW_HOOK:#x} -> WWSTUB @{WWSTUB_VA:#x}")

    # patch TITLE-FIX: kill readScenarioTitle's byte-value truncation (scenario list names)
    if title_fix:
        tf = va2file(VA_TITLECLASS)
        assert bytes(d[tf:tf+8]) == TITLECLASS_ORIG_HEAD, bytes(d[tf:tf+8]).hex()
        code = assemble_titleclass(scratch)
        assert len(code) <= TITLECLASS_LEN, f"titleclass {len(code)}B exceeds {TITLECLASS_LEN}B"
        d[tf:tf+TITLECLASS_LEN] = code + b"\x90" * (TITLECLASS_LEN - len(code))
        print(f"[title-fix] readScenarioTitle classifier @{VA_TITLECLASS:#x} -> \\0/\\r/\\n-only stop "
              f"({len(code)}B +{TITLECLASS_LEN-len(code)} nop)")

    # patch 2: language default byte 0x09 -> 0x0C (French slot) — optional
    if lang_patch:
        assert d[LANG_FILE_OFF] == 0x09, hex(d[LANG_FILE_OFF])
        d[LANG_FILE_OFF] = 0x0C

    d += sect
    open(exe_out, "wb").write(d)
    print(f"[hook] STUB1 {len(stub1)}B @{STUB1_VA:#x}  atlas {len(atlas)}B @{ATLAS_VA:#x} (count={atlas_count}, maxlead 0x{maxlead:02x})")
    print(f"[hook] .cjk RVA {CJK_RVA:#x} VSize {vsize:#x} raw@{raw_off:#x}  SizeOfImage {size_of_image:#x}->{new_size_of_image:#x}")
    print(f"[hook] drawString hook @{VA_HOOK:#x}; lang byte {'-> 0x0C (French)' if lang_patch else 'UNCHANGED (English)'}")
    print(f"[hook] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    exe_in, atlas, exe_out = sys.argv[1], sys.argv[2], sys.argv[3]
    scratch = sys.argv[4] if len(sys.argv) > 4 else "/tmp"
    lang = "--no-lang" not in sys.argv
    wws = "--ww-safe" in sys.argv
    mf = "--measure-fix" in sys.argv
    gwc = "--gw-clamp" in sys.argv
    wwh = "--ww-hook" in sys.argv
    tfx = "--no-title-fix" not in sys.argv
    build(exe_in, atlas, exe_out, scratch, lang_patch=lang, ww_safe=wws, measure_fix=mf, gw_clamp=gwc, ww_hook=wwh, title_fix=tfx)

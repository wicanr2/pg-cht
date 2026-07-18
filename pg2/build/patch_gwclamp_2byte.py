#!/usr/bin/env python3
"""patch_gwclamp_2byte.py -- make the width-measure 2-byte aware at ONE point.

Root cause of the 3 residual text bugs (main-menu tooltip off-screen, purchase unit
names crammed, status-bar name mis-centered): every width-MEASURE loop reads the string
byte-by-byte with `movsx` and sums glyphWidth([0x4d74c4]=game font, byte).  For a dense
2-byte CJK char that yields glyphWidth(fontpg,lead)+glyphWidth(fontpg,trail) -- NOT the
atlas's fixed 16px that the DRAW path (STUB1 drawStringCore / WWSTUB word-wrap) advances.
The measured width therefore disagrees with the drawn width, so every centered / right-
aligned / box-fit position computed from a measure loop is wrong.

The current GWCLAMP (installed by build_hooked_exe_pg2.py --gw-clamp) only masks ch to a
byte to stop the page fault; it still double-counts CJK.  This patch REPLACES the GWCLAMP
stub in place so it is 2-byte aware:

  glyphWidth(font, ch):
     if (signed)ch < 0:   -> a high byte read by a movsx measure loop -> return 8
                             (half of the uniform 16px atlas glyph; lead+trail = 16)
     else:                -> ASCII (0..0x7f) or atlas dense (STUB1 pushes a POSITIVE
                             dense) -> mask to byte + fall through to real glyphWidth.

Why the sign test is a reliable discriminator: EVERY measure loop reads the char with
`movsx` (0f be ...), so a high CJK byte arrives sign-extended (negative).  The ONLY caller
that passes a positive value >= 0x81 is STUB1's atlas advance, which computes a positive
`dense`.  So negative ch == "measuring a raw CJK byte", unambiguously.

Single 4-region-agnostic point: this fixes measureWidth(0x43eb14, 28 callers, the tooltip
and status-bar centering), measureWidthMultiline(0x43eba0), the purchase inline measure
(0x43fd2b) and countLines(0x43fdd5) simultaneously -- no per-site patching.  Draw paths,
ASCII, digits, and the ctype/line-break classifiers are untouched.
"""
import struct, subprocess, os, sys

GWCLAMP_VA       = 0x57f180          # stub location inside .cjk (unchanged from build)
GLYPHWIDTH_ENTRY = 0x41b013          # real glyphWidth prologue
CJK_RAW          = 0xd0400           # .cjk raw file offset in the repoint EXE
GWCLAMP_FILE     = CJK_RAW + 0x180   # 0xd0580
ATLAS_FILE       = CJK_RAW + 0x200   # 0xd0600 -- must not overrun into atlas
SLOT             = ATLAS_FILE - GWCLAMP_FILE   # 0x80 bytes available

def va2file(va): return va - 0x401000 + 0x400

def nasm(asm, tag):
    src = f"/tmp/{tag}.asm"; binf = f"/tmp/{tag}.bin"
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    return open(binf, "rb").read()

NEW_GWCLAMP = f"""bits 32
org {GWCLAMP_VA:#x}
    cmp dword [esp+8], 0          ; ch arg (esp+0=ret, +4=font, +8=ch)
    jge .norm                    ; ch >= 0 -> ASCII (0..7f) or atlas dense (positive)
    mov eax, 8                   ; high byte via movsx -> negative -> half of 16px atlas
    ret                          ; cdecl: caller cleans font+ch
.norm:
    and dword [esp+8], 0xff       ; mask (harmless for ASCII; safety for dense>0xff)
    push ebp
    mov ebp, esp
    push ebx
    push esi
    jmp {GLYPHWIDTH_ENTRY+5:#x}
"""

def build(exe_in, exe_out):
    d = bytearray(open(exe_in, "rb").read())
    # sanity: entry hook already redirects glyphWidth -> GWCLAMP
    assert d[va2file(GLYPHWIDTH_ENTRY)] == 0xE9, "glyphWidth entry not hooked"
    rel = struct.unpack_from('<i', d, va2file(GLYPHWIDTH_ENTRY)+1)[0]
    tgt = GLYPHWIDTH_ENTRY + 5 + rel
    assert tgt == GWCLAMP_VA, f"entry jmp target {tgt:#x} != {GWCLAMP_VA:#x}"
    # sanity: existing stub begins with the old `and dword[esp+8],0xff`
    assert bytes(d[GWCLAMP_FILE:GWCLAMP_FILE+5]) == bytes.fromhex("8164240 8ff".replace(" ","")), \
        bytes(d[GWCLAMP_FILE:GWCLAMP_FILE+5]).hex()
    stub = nasm(NEW_GWCLAMP, "gwclamp2b")
    assert len(stub) <= SLOT, f"new stub {len(stub)}B exceeds slot {SLOT:#x}"
    # clear the whole slot then write (keeps any trailing bytes zero, no atlas overrun)
    d[GWCLAMP_FILE:ATLAS_FILE] = stub + bytes(SLOT - len(stub))
    open(exe_out, "wb").write(d)
    print(f"[gwclamp-2byte] new stub {len(stub)}B @ {GWCLAMP_VA:#x} (file {GWCLAMP_FILE:#x}); slot {SLOT:#x}")
    print(f"[gwclamp-2byte] disasm:\n" + subprocess.run(
        ["objdump","-D","-b","binary","-m","i386","-M","intel",
         f"--adjust-vma={GWCLAMP_VA:#x}","/tmp/gwclamp2b.bin"],
        capture_output=True, text=True).stdout.split("<.data>:")[-1])
    print(f"[gwclamp-2byte] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])

#!/usr/bin/env python3
"""build_hooked_exe.py — append a .cjk PE section (hook stub + atlas) to
PACGEN.EXE and patch drawString's loop head to jump into the stub.

Design (from static RE, docs/11-2byte-hook-re.md):
  drawString @ VA 0x428312 loops: 0x428322 `movzx eax,[esi]` ... call drawGlyph
  0x42817f ... `add edi,eax; inc esi; cmp [esi],0; jne 0x428322`.
  We overwrite the 5 bytes at 0x428322 with `jmp STUB`. The stub re-reads the
  char; if it's a custom CJK lead byte (0x81-0x86) it computes the dense atlas
  index and calls the SAME drawGlyph with font=ATLAS, ch=dense, advancing esi by
  2; otherwise it replays the original ASCII drawGlyph call (esi+1). Either way
  it jumps back to the terminator test at 0x42833e. One patch covers all 37
  drawString callers (menu/UI text). Height is memory-read from [font+8], so the
  16px atlas + a height-16 TFONT1.DAT render tall with no code change.

Layout of .cjk (VA 0x603000): stub at 0x603000 (256B reserved), atlas at 0x603100.
Fixed-base EXE -> absolute immediates need no relocations.
"""
import struct, subprocess, os, sys

VA_HOOK      = 0x428322       # drawString loop head (overwrite 5 bytes)
VA_TERMTEST  = 0x42833e       # drawString `cmp [esi],0` — stub returns here
VA_DRAWGLYPH = 0x42817f       # drawGlyph(dest,x,y,font,ch,xlat)
TEXT_VA_BASE = 0x401000       # .text VA
TEXT_RAW     = 0x400          # .text file offset  -> file = VA - 0x401000 + 0x400

IMAGE_BASE   = 0x400000
SECT_ALIGN   = 0x1000
FILE_ALIGN   = 0x200
CJK_RVA      = 0x203000       # new section RVA (VA 0x603000); == old SizeOfImage
STUB_OFF     = 0x000          # stub at section start
ATLAS_OFF    = 0x100          # atlas 256B into section
STUB_VA      = IMAGE_BASE + CJK_RVA + STUB_OFF   # 0x603000
ATLAS_VA     = IMAGE_BASE + CJK_RVA + ATLAS_OFF  # 0x603100

LEAD0, TRAIL0, TRAILW = 0x81, 0xA1, 94

def va2file(va):
    return va - TEXT_VA_BASE + TEXT_RAW

def assemble_stub(scratch):
    asm = f"""bits 32
org {STUB_VA:#x}
    movzx eax, byte [esi]
    cmp al, {LEAD0:#x}
    jb .ascii
    cmp al, {LEAD0 + 5:#x}          ; leads 0x81-0x86 only
    ja .ascii
    movzx ebx, al
    sub ebx, {LEAD0:#x}
    imul ebx, ebx, {TRAILW}
    movzx eax, byte [esi+1]
    sub eax, {TRAIL0:#x}
    add eax, ebx                    ; eax = dense index
    push dword [ebp+0x1c]           ; xlat
    push eax                        ; ch = dense
    push {ATLAS_VA:#x}              ; font = atlas
    push dword [ebp+0x10]           ; y
    push edi                        ; x (pen)
    push dword [ebp+0x8]            ; dest
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    add edi, eax                    ; pen += advance
    add esi, 2                      ; consumed lead+trail
    jmp {VA_TERMTEST:#x}
.ascii:
    push dword [ebp+0x1c]           ; xlat
    push eax                        ; ch (ascii)
    push dword [ebp+0x14]           ; font (original)
    push dword [ebp+0x10]           ; y
    push edi                        ; x
    push dword [ebp+0x8]            ; dest
    call {VA_DRAWGLYPH:#x}
    add esp, 0x18
    add edi, eax
    inc esi
    jmp {VA_TERMTEST:#x}
"""
    src = os.path.join(scratch, "stub.asm"); binf = os.path.join(scratch, "stub.bin")
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    stub = open(binf, "rb").read()
    assert len(stub) <= ATLAS_OFF, f"stub {len(stub)}B exceeds {ATLAS_OFF}B reservation"
    return stub

def build(exe_in, atlas_path, exe_out, scratch):
    d = bytearray(open(exe_in, "rb").read())
    atlas = open(atlas_path, "rb").read()
    stub = assemble_stub(scratch)

    # --- PE header locations ---
    e_lfanew = struct.unpack('<I', d[0x3c:0x40])[0]
    coff = e_lfanew + 4
    nsec = struct.unpack('<H', d[coff+2:coff+4])[0]
    opt_size = struct.unpack('<H', d[coff+16:coff+18])[0]
    opt = coff + 20
    size_of_image = struct.unpack('<I', d[opt+56:opt+60])[0]
    sect_table = opt + opt_size
    assert CJK_RVA == size_of_image, f"CJK_RVA {CJK_RVA:#x} != SizeOfImage {size_of_image:#x}"

    # --- section raw data: [stub | pad to ATLAS_OFF | atlas], file-aligned ---
    sect = bytearray(ATLAS_OFF)          # 256B, stub region (zero-padded)
    sect[:len(stub)] = stub
    sect += atlas
    vsize = len(sect)
    raw_off = len(d)
    assert raw_off % FILE_ALIGN == 0, f"file end {raw_off:#x} not FILE_ALIGN"
    raw_size = (vsize + FILE_ALIGN - 1) & ~(FILE_ALIGN - 1)
    sect += bytes(raw_size - vsize)      # pad raw to file alignment

    # --- new section header @ sect_table + nsec*40 ---
    hdr_off = sect_table + nsec * 40
    assert hdr_off + 40 <= struct.unpack('<I', d[opt+60:opt+64])[0], "no header room"
    name = b".cjk".ljust(8, b"\0")
    new_hdr = name + struct.pack('<IIII', vsize, CJK_RVA, raw_size, raw_off) \
              + struct.pack('<IIHHI', 0, 0, 0, 0, 0x60000020)  # CODE|EXEC|READ
    assert len(new_hdr) == 40
    d[hdr_off:hdr_off+40] = new_hdr

    # --- bump NumberOfSections and SizeOfImage ---
    struct.pack_into('<H', d, coff+2, nsec + 1)
    new_size_of_image = CJK_RVA + ((vsize + SECT_ALIGN - 1) & ~(SECT_ALIGN - 1))
    struct.pack_into('<I', d, opt+56, new_size_of_image)

    # --- patch hook site: 5 bytes at VA_HOOK -> jmp STUB ---
    hf = va2file(VA_HOOK)
    orig = bytes(d[hf:hf+5])
    assert orig == bytes.fromhex("0fb606ff75"), f"unexpected hook bytes {orig.hex()}"
    rel = STUB_VA - (VA_HOOK + 5)
    d[hf:hf+5] = b"\xe9" + struct.pack('<i', rel)

    # --- append section data ---
    d += sect
    open(exe_out, "wb").write(d)
    print(f"[hook] stub {len(stub)}B @ {STUB_VA:#x}, atlas {len(atlas)}B @ {ATLAS_VA:#x}")
    print(f"[hook] .cjk RVA {CJK_RVA:#x} VSize {vsize:#x} RawSize {raw_size:#x} RawPtr {raw_off:#x}")
    print(f"[hook] NumberOfSections {nsec}->{nsec+1}  SizeOfImage {size_of_image:#x}->{new_size_of_image:#x}")
    print(f"[hook] hook @ {VA_HOOK:#x} (file {hf:#x}): {orig.hex()} -> e9 {struct.pack('<i',rel).hex()}")
    print(f"[hook] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    exe_in  = sys.argv[1]
    atlas   = sys.argv[2]
    exe_out = sys.argv[3]
    scratch = sys.argv[4] if len(sys.argv) > 4 else "/tmp"
    build(exe_in, atlas, exe_out, scratch)

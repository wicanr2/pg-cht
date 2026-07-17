#!/usr/bin/env python3
"""Inspect PANZER2.EXE PE header + disassemble the draw pipeline to confirm hook contract."""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = sys.argv[1] if len(sys.argv) > 1 else \
    "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/build_poc/PANZER2.EXE.orig"
d = open(EXE, "rb").read()

e_lfanew = struct.unpack_from('<I', d, 0x3c)[0]
assert d[e_lfanew:e_lfanew+4] == b'PE\0\0'
coff = e_lfanew + 4
nsec = struct.unpack_from('<H', d, coff+2)[0]
opt_size = struct.unpack_from('<H', d, coff+16)[0]
opt = coff + 20
magic = struct.unpack_from('<H', d, opt)[0]
image_base = struct.unpack_from('<I', d, opt+28)[0]
sect_align = struct.unpack_from('<I', d, opt+32)[0]
file_align = struct.unpack_from('<I', d, opt+36)[0]
size_of_image = struct.unpack_from('<I', d, opt+56)[0]
size_of_headers = struct.unpack_from('<I', d, opt+60)[0]
dll_char = struct.unpack_from('<H', d, opt+70)[0]
print(f"e_lfanew=0x{e_lfanew:x} nsec={nsec} opt_size=0x{opt_size:x} magic=0x{magic:x}")
print(f"ImageBase=0x{image_base:x} SectAlign=0x{sect_align:x} FileAlign=0x{file_align:x}")
print(f"SizeOfImage=0x{size_of_image:x} SizeOfHeaders=0x{size_of_headers:x} DllChar=0x{dll_char:x} (DYNAMICBASE={'YES' if dll_char&0x40 else 'no'})")
sect_table = opt + opt_size
secs = []
print("\n== sections ==")
for i in range(nsec):
    b = sect_table + i*40
    name = d[b:b+8].split(b'\0')[0].decode('latin1')
    vsize = struct.unpack_from('<I', d, b+8)[0]
    vaddr = struct.unpack_from('<I', d, b+12)[0]
    rsize = struct.unpack_from('<I', d, b+16)[0]
    raw = struct.unpack_from('<I', d, b+20)[0]
    chars = struct.unpack_from('<I', d, b+36)[0]
    secs.append((name, vaddr, vsize, raw, rsize, chars))
    print(f"  {name:8s} VA=0x{image_base+vaddr:08x} RVA=0x{vaddr:06x} VSize=0x{vsize:06x} raw=0x{raw:06x} rsize=0x{rsize:06x} chars=0x{chars:08x}")
hdr_end = sect_table + nsec*40
print(f"\nsect_table=0x{sect_table:x} hdr_end=0x{hdr_end:x} room_to_headers=0x{size_of_headers - hdr_end:x} (bytes for new 40B entry)")
print(f"proposed .cjk RVA=0x17f000 vs SizeOfImage=0x{size_of_image:x} -> {'MATCH' if 0x17f000==size_of_image else 'MISMATCH!'}")

# find .text
text = [s for s in secs if s[0] == '.text'][0]
tva = image_base + text[1]
traw = text[3]
def va2file(va): return va - tva + traw
print(f"\n.text VA=0x{tva:x} raw=0x{traw:x}  va2file(0x43e699)=0x{va2file(0x43e699):x}  va2file(0x41b033)=0x{va2file(0x41b033):x}")

md = Cs(CS_ARCH_X86, CS_MODE_32)
def disasm(va, end, label):
    print(f"\n== {label}  VA 0x{va:x}..0x{end:x} ==")
    f = va2file(va)
    code = d[f:f + (end-va)]
    for ins in md.disasm(code, va):
        raw = ins.bytes.hex()
        mark = ""
        if ins.address == 0x43e699: mark = "   <== MAIN HOOK (overwrite here)"
        if ins.address == 0x43e685: mark = "   <== back-edge target"
        if ins.address == 0x43e6a4: mark = "   <== ascii rejoin target"
        print(f"  0x{ins.address:x}: {raw:24s} {ins.mnemonic} {ins.op_str}{mark}")

disasm(0x43e612, 0x43e6c0, "drawStringCore main loop")
disasm(0x41b013, 0x41b040, "glyphWidth entry")
disasm(0x41b033, 0x41b070, "drawGlyph entry")

# confirm hook bytes
hf = va2file(0x43e699)
print(f"\nbytes @0x43e699 (file 0x{hf:x}): {d[hf:hf+7].hex()}  expect: 0fbf45f08b4d14")

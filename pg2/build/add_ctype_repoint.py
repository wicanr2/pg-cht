#!/usr/bin/env python3
"""add_ctype_repoint.py -- GLOBAL _pctype fix via pointer repoint (single data patch that
replaces the 5 per-site classifier code patches).

Root cause: the 5 title/campaign classifiers (and the requisition family 0x43ff02/0x43ffc5,
etc.) read char via `movsx` (sign-extend) then `_pctype[ch]` where _pctype = *[0x4ba538] =
0x4ba542.  A high byte 0x80-0xFF -> negative index -> reads the 256 bytes BEFORE the table
(0x4ba442..0x4ba540), which are LIVE STRING DATA ("melerror.txt","language","%s%d",...) -> the
class word `& 0x157` is mostly 0 -> the byte reads as class-0 -> the line terminates -> CJK
truncates.

Fix (this script): build a fabricated ctype table in a new .ctyp section and repoint the
POINTER at 0x4ba538 to it.  Layout: [128 words negative shadow = 0x0100 each][256 words copy
of the ORIGINAL _pctype[0..0xFF] read out of this same EXE].  Pointer -> &positive[0].
  * Positive indices 0..0xFF are byte-identical to the stock table (ASCII ctype + CRT movzx
    high-byte behavior unchanged) -> minimal blast radius.
  * Negative indices -128..-1 (what movsx high bytes hit) now all read 0x0100 (_ALPHA): the
    `& 0x157` mask is nonzero -> "keep", so NO high byte ever terminates a line.  0x0100 has
    no _DIGIT(4)/_SPACE(8)/_CNTRL(0x20) bit, so isdigit/isspace/iscntrl of a high byte stay
    false (correct for CJK); only isalpha/isalnum become true.
This one 4-byte pointer patch fixes EVERY movsx-`[0x4ba538]` classifier at once (all 5 title
siblings + the requisition family + any undiscovered site), with the live-string shadow left
untouched.
"""
import struct, sys

PTR_VA   = 0x4ba538          # _pctype pointer (value 0x4ba542)
DATA_VA  = 0x49c000; DATA_RAW = 0x9ae00   # .data (for reading original table + patching ptr)
HIGH_CLASS = 0x0100          # _ALPHA: keeps line, no digit/space/cntrl side effects
SHADOW_WORDS = 128           # indices -128..-1
POS_WORDS    = 256           # indices 0..255

def data_file(va): return va - DATA_VA + DATA_RAW

def build(exe_in, exe_out):
    d = bytearray(open(exe_in, "rb").read())
    e = struct.unpack_from('<I', d, 0x3c)[0]; coff = e + 4
    nsec = struct.unpack_from('<H', d, coff+2)[0]; osz = struct.unpack_from('<H', d, coff+16)[0]
    opt = coff + 20; st = opt + osz
    soi = struct.unpack_from('<I', d, opt+56)[0]; hdrs = struct.unpack_from('<I', d, opt+60)[0]
    salign = struct.unpack_from('<I', d, opt+32)[0]; falign = struct.unpack_from('<I', d, opt+36)[0]

    # original _pctype pointer value + table
    pctype_val = struct.unpack_from('<I', d, data_file(PTR_VA))[0]
    assert pctype_val == 0x4ba542, hex(pctype_val)
    pos = bytearray()
    for b in range(POS_WORDS):
        w = struct.unpack_from('<H', d, data_file(pctype_val + 2*b))[0]
        pos += struct.pack('<H', w)
    shadow = struct.pack('<H', HIGH_CLASS) * SHADOW_WORDS
    table = shadow + pos                       # pointer -> table + len(shadow)
    tbl_size = len(table)

    # new .ctyp section
    hdr_off = st + nsec*40
    assert hdr_off + 40 <= hdrs, "no room for section header"
    new_rva = (soi + salign - 1) & ~(salign - 1)     # next free RVA
    raw_off = len(d)
    assert raw_off % falign == 0, "file not aligned"
    vsize = tbl_size
    raw_size = (vsize + falign - 1) & ~(falign - 1)
    body = table + bytes(raw_size - vsize)
    # section header: INITIALIZED_DATA | READ | WRITE (0xC0000040) -- ctype table is read-mostly
    new_hdr = b".ctyp".ljust(8, b"\0") + struct.pack('<IIII', vsize, new_rva, raw_size, raw_off) \
              + struct.pack('<IIHHI', 0, 0, 0, 0, 0xC0000040)
    d[hdr_off:hdr_off+40] = new_hdr
    struct.pack_into('<H', d, coff+2, nsec + 1)
    new_soi = new_rva + ((vsize + salign - 1) & ~(salign - 1))
    struct.pack_into('<I', d, opt+56, new_soi)
    d += body

    # repoint 0x4ba538 -> &positive[0] = section_base + shadow_bytes
    new_ptr = 0x400000 + new_rva + len(shadow)
    struct.pack_into('<I', d, data_file(PTR_VA), new_ptr)

    open(exe_out, "wb").write(d)
    print(f"[repoint] .ctyp @ RVA {new_rva:#x} (VA {0x400000+new_rva:#x}) vsize {vsize:#x} raw@{raw_off:#x}")
    print(f"[repoint] table = {SHADOW_WORDS}w shadow(0x{HIGH_CLASS:04x}) + {POS_WORDS}w copy of _pctype[0..0xff]")
    print(f"[repoint] _pctype ptr @0x4ba538: 0x{pctype_val:x} -> 0x{new_ptr:x}  (SizeOfImage {soi:#x}->{new_soi:#x})")
    print(f"[repoint] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])

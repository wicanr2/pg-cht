#!/usr/bin/env python3
"""從 PE32 exe 抓可翻譯字串。輸出 TSV: file_offset<TAB>va<TAB>section<TAB>len<TAB>text"""
import struct
import sys
import re

def parse_pe(data):
    pe_off = struct.unpack('<I', data[0x3c:0x40])[0]
    nsec = struct.unpack('<H', data[pe_off+6:pe_off+8])[0]
    opt_sz = struct.unpack('<H', data[pe_off+20:pe_off+22])[0]
    image_base = struct.unpack('<I', data[pe_off+24+28:pe_off+24+32])[0]
    sec_off = pe_off + 24 + opt_sz
    sections = []
    for i in range(nsec):
        o = sec_off + i*40
        name = data[o:o+8].rstrip(b'\x00').decode('latin1')
        va = struct.unpack('<I', data[o+12:o+16])[0] + image_base
        rp = struct.unpack('<I', data[o+20:o+24])[0]
        rs = struct.unpack('<I', data[o+16:o+20])[0]
        sections.append((name, va, rp, rs))
    return image_base, sections

def fo_to_va_section(fo, sections):
    for name, va, rp, rs in sections:
        if rp <= fo < rp + rs:
            return va + (fo - rp), name
    return 0, "?"

def is_printable_ascii(s):
    return all(0x20 <= b < 0x7f or b in (0x09, 0x0a, 0x0d) for b in s)

def scan_strings(data, min_len=4, max_len=256):
    """抓 null-terminated ASCII strings"""
    out = []
    i = 0
    n = len(data)
    while i < n:
        if 0x20 <= data[i] < 0x7f:
            j = i
            while j < n and (0x20 <= data[j] < 0x7f or data[j] in (0x09,)):
                j += 1
            if j < n and data[j] == 0 and (j - i) >= min_len and (j - i) <= max_len:
                out.append((i, data[i:j]))
            i = j + 1
        else:
            i += 1
    return out

def main():
    if len(sys.argv) < 3:
        print("Usage: dump_pe_strings.py PACGEN.EXE out.tsv", file=sys.stderr)
        sys.exit(1)
    inpath, outpath = sys.argv[1], sys.argv[2]
    data = open(inpath, 'rb').read()
    image_base, sections = parse_pe(data)
    strings = scan_strings(data, min_len=4)
    # xref 資料: 掃全 exe 找 4-byte little-endian VA 指到 string
    string_va = {}
    for fo, s in strings:
        va, sec = fo_to_va_section(fo, sections)
        string_va[fo] = (va, sec, s)
    # 為每個 string 找 xref count (快版: build a set of VAs, one pass through .text/.rdata)
    va_by_fo = {fo: va for fo, (va, _, _) in string_va.items()}
    va_set = set(va_by_fo.values())
    xref_count = {va: 0 for va in va_set}
    # 掃 .text
    for name, va_base, rp, rs in sections:
        if name in ('.text', '.rdata', '.data'):
            blob = data[rp:rp+rs]
            for i in range(0, len(blob) - 4):
                v = struct.unpack('<I', blob[i:i+4])[0]
                if v in xref_count:
                    xref_count[v] += 1
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write("file_off\tva\tsection\txref\tlen\ttext\n")
        for fo, (va, sec, s) in sorted(string_va.items()):
            txt = s.decode('latin1').replace('\t', '\\t').replace('\n', '\\n')
            f.write(f"0x{fo:x}\t0x{va:x}\t{sec}\t{xref_count.get(va,0)}\t{len(s)}\t{txt}\n")
    print(f"[dump] wrote {len(string_va)} strings to {outpath}", file=sys.stderr)

if __name__ == "__main__":
    main()

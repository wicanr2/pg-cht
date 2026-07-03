#!/usr/bin/env python3
"""apply_2byte_equip.py — translate matching unit names in PACEQUIP.TXT to the
custom dense 2-byte codes. PACEQUIP.TXT is CRLF-delimited, one unit name per
record (1096 records); the game reads a whole record, so records are free-form
(no byte-length constraint). We only touch records whose exact text is a key in
glossary_equip.tsv — the ~1000 proper-noun unit names not in the glossary stay
English (that is a translation-content task, not engine work).
"""
import sys, csv, json, os

ROOT = "/home/anr2/game/Panzer_General/pg-cht/pacgen"

def load_glossary(charmap):
    gl = {}
    for row in csv.DictReader(open(os.path.join(ROOT, "translations/glossary_equip.tsv"), encoding="utf-8"),
                              delimiter="\t"):
        en, zh = (row.get("english") or "").strip(), (row.get("chinese") or "").strip()
        if en and zh and all((ch in charmap) or ord(ch) < 0x80 for ch in zh):
            gl[en] = zh
    return gl

def encode(s, charmap):
    out = bytearray()
    for ch in s:
        if ord(ch) < 0x80:
            out.append(ord(ch))
        else:
            out += bytes(charmap[ch])
    return bytes(out)

def apply(src, dst, charmap_path):
    charmap = json.load(open(charmap_path, encoding="utf-8"))
    gl = load_glossary(charmap)
    data = open(src, "rb").read()
    recs = data.split(b"\r\n")
    n = 0
    for i, r in enumerate(recs):
        t = r.decode("latin1").strip()
        if t in gl:
            recs[i] = encode(gl[t], charmap)
            n += 1
    open(dst, "wb").write(b"\r\n".join(recs))
    print(f"[equip] {n} unit names -> custom 2-byte ({len(gl)} glossary entries) -> {dst}")

if __name__ == "__main__":
    src = sys.argv[1]; dst = sys.argv[2]
    cm = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "build/atlas/charmap.json")
    apply(src, dst, cm)

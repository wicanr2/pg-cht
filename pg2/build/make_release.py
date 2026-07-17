#!/usr/bin/env python3
"""make_release.py — full (release) PG2 CJK build.

Stands on the proven POC pipeline (中文化規劃 §7.5). Difference vs make_poc_en.py:
  * atlas built from the COMPLETE translated char set (all 翻譯/out/ masters), not a
    handful of test lines;
  * ALL English-slot loose data files re-encoded to dense 2-byte CJK
    (GUI97/EQUIP97/MISC/NAMES + the 53 translated SCENARIO/*.TXT);
  * hooked EXE = main draw hook + glyphWidth clamp + word-wrap movsx->movzx safety
    (the game_nav recipe), NO language byte patch (English is the default slot).

Nothing in the repo or the original game tree is modified. Everything lands under
build_release/. Hardlinked loose files are removed before a fresh encoded file is
written, so the shared source inode is never truncated.
"""
import os, sys, json, subprocess, shutil, struct, glob

HERE   = os.path.dirname(os.path.abspath(__file__))
REL    = os.path.dirname(HERE)                       # build_release/
SP_PG2 = os.path.dirname(REL)                        # scratchpad/pg2/
SRC_GAME = os.path.join(SP_PG2, "Panzer2")           # extracted original (do NOT modify)
MASTERS  = os.path.join(SP_PG2, "翻譯", "out")        # UTF-8 translated masters
GAME   = os.path.join(REL, "game")
BUILD  = os.path.join(REL, "build")
ATLAS_DIR = os.path.join(BUILD, "atlas")
EXE_ORIG  = os.path.join(REL, "PANZER2.EXE.orig")

# master files that become dense-encoded loose TXT in the game dir
TOP_FILES = ["GUI97.TXT", "MISC.TXT", "EQUIP97.TXT", "NAMES.TXT"]

SIZE_LIMITS = {   # 中文化規劃 §4.4 (bytes)
    "GUI97.TXT": 64*1024, "EQUIP97.TXT": 64*1024,
    "NAMES.TXT": 32*1024, "MISC.TXT": 64*1024, "_SCENARIO": 32*1024,
}


def master_files():
    files = [os.path.join(MASTERS, f) for f in TOP_FILES]
    files += sorted(glob.glob(os.path.join(MASTERS, "SCENARIO", "*.TXT")))
    return files


def collect_strings():
    """Every line of every master, for atlas char collection."""
    strings = []
    for f in master_files():
        raw = open(f, "rb").read()
        if raw.endswith(b"\x1a"):
            raw = raw[:-1]
        strings.extend(raw.decode("utf-8").split("\r\n"))
    return strings


def encode_master(src, dst, charmap):
    """Re-encode a UTF-8 master to dense 2-byte CJK, preserving exact byte structure
    (CRLF segmentation + optional 0x1A EOF marker + line count)."""
    raw = open(src, "rb").read()
    eof = raw.endswith(b"\x1a")
    if eof:
        raw = raw[:-1]
    segs = raw.split(b"\r\n")
    out = []
    for seg in segs:
        b = bytearray()
        for ch in seg.decode("utf-8"):
            o = ord(ch)
            if o < 0x80:
                b.append(o)
            elif ch in charmap:
                b += bytes(charmap[ch])
            else:
                raise ValueError(f"{os.path.basename(src)}: char {ch!r} U+{o:04X} not in atlas")
        out.append(bytes(b))
    data = b"\r\n".join(out)
    if eof:
        data += b"\x1a"
    if os.path.exists(dst):
        os.remove(dst)          # break hardlink so we never truncate the shared source inode
    open(dst, "wb").write(data)
    return len(data), len(segs)


def main():
    os.makedirs(BUILD, exist_ok=True)

    # 1. atlas from the complete master char set
    strings = collect_strings()
    strings_path = os.path.join(BUILD, "strings.json")
    json.dump(strings, open(strings_path, "w"), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(HERE, "build_atlas_pg2.py"),
                    strings_path, ATLAS_DIR], check=True)
    charmap = json.load(open(os.path.join(ATLAS_DIR, "charmap.json")))
    atlas_info = json.load(open(os.path.join(ATLAS_DIR, "atlas_index.json")))
    print(f"[atlas] {atlas_info['count']} glyphs, maxlead 0x{atlas_info['maxlead']:02x}")

    # 2. hooked EXE: main hook + gw-clamp + ww-safe + word-wrap 2-byte hook, NO lang flip
    #    (English slot). ww-hook makes the briefing/multi-line path render CJK; its ASCII
    #    branch replays the overwritten instruction, so English text is unaffected.
    hooked = os.path.join(BUILD, "PANZER2.EXE")
    subprocess.run([sys.executable, os.path.join(HERE, "build_hooked_exe_pg2.py"),
                    EXE_ORIG, os.path.join(ATLAS_DIR, "atlas_font.dat"), hooked, BUILD,
                    "--no-lang", "--gw-clamp", "--ww-safe", "--ww-hook"], check=True)

    # 3. game dir: fresh hardlink copy, swap in hooked EXE
    if os.path.exists(GAME):
        shutil.rmtree(GAME)
    subprocess.run(["cp", "-al", SRC_GAME, GAME], check=True)
    ge = os.path.join(GAME, "PANZER2.EXE")
    if os.path.exists(ge):
        os.remove(ge)
    shutil.copy(hooked, ge)

    # 4. encode all English-slot loose data files
    print("=== encoding loose data files ===")
    warnings = []
    for f in TOP_FILES:
        sz, n = encode_master(os.path.join(MASTERS, f), os.path.join(GAME, f), charmap)
        lim = SIZE_LIMITS.get(f, 32*1024)
        flag = "  !!OVER LIMIT" if sz > lim else ""
        if sz > lim:
            warnings.append(f"{f} {sz}B > {lim}")
        print(f"  {f:14s} {n:4d} lines  {sz:6d}B / {lim}B{flag}")
    scen_dir = os.path.join(GAME, "SCENARIO")
    scen_masters = sorted(glob.glob(os.path.join(MASTERS, "SCENARIO", "*.TXT")))
    scen_over = 0
    for sm in scen_masters:
        base = os.path.basename(sm)
        sz, n = encode_master(sm, os.path.join(scen_dir, base), charmap)
        if sz > SIZE_LIMITS["_SCENARIO"]:
            scen_over += 1
            warnings.append(f"SCENARIO/{base} {sz}B")
    print(f"  SCENARIO: {len(scen_masters)} files encoded, {scen_over} over 32KB limit")

    # 5. sanity
    d = open(ge, "rb").read()
    hf = 0x43e699 - 0x401000 + 0x400
    gf = 0x41b013 - 0x401000 + 0x400
    print("=== EXE sanity ===")
    print(f"  lang byte @0xa32a0 = 0x{d[0xa32a0]:02x} (want 09 English)")
    print(f"  main hook @0x43e699 = 0x{d[hf]:02x} (want e9)")
    print(f"  gwclamp   @0x41b013 = 0x{d[gf]:02x} (want e9)")
    print(f"  size = {len(d)} bytes")
    if warnings:
        print("!!! SIZE WARNINGS:", *warnings, sep="\n   ")
    else:
        print("[ok] all data files within size limits")
    print(f"[done] release game dir: {GAME}")


if __name__ == "__main__":
    main()

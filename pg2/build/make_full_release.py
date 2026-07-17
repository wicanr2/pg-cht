#!/usr/bin/env python3
"""make_full_release.py — COMPLETE (full) PG2 CJK build.

Extends build_release/tools/make_release.py from the round-1-only build (916 glyphs,
53 SCENARIO place-name files) to the COMPLETE Chinese build:

  * atlas built from the UNION of round-1 masters (翻譯/out: GUI97/MISC/EQUIP97/NAMES
    + 53 SCENARIO place-name lists) AND round-2 masters (翻譯/briefings/out/SCENARIO:
    249 campaign-briefing prose files)  ->  full 1,5xx-char atlas;
  * ALL 4 top data files + ALL 302 SCENARIO/*.TXT re-encoded to dense 2-byte CJK
    and written over the English-slot loose .TXT of a FRESH 7z-extracted game copy;
  * hooked EXE = main draw hook (0x43e699) + glyphWidth clamp (0x41b013) +
    word-wrap movsx->movzx safety + word-wrap 2-byte hook (0x43e955) +
    readScenarioTitle truncation fix (0x3d1e0, title_fix default) ; NO language byte
    patch (English is the default slot; the game reads loose *.TXT).

Nothing in the repo or the pristine game tree is modified. Everything lands under
build_final/. Hardlink/copy loose files are removed before a fresh encoded file is
written, so no shared source inode is ever truncated.
"""
import os, sys, json, subprocess, shutil, glob, struct

HERE   = os.path.dirname(os.path.abspath(__file__))       # build_final/
SP_PG2 = os.path.dirname(HERE)                            # scratchpad/pg2/
TOOLS  = os.path.join(SP_PG2, "build_release", "tools")

SRC_GAME   = os.path.join(HERE, "Panzer2")                # FRESH 7z extract (do NOT modify)
MASTERS1   = os.path.join(SP_PG2, "翻譯", "out")           # round-1 masters
MASTERS2   = os.path.join(SP_PG2, "翻譯", "briefings", "out", "SCENARIO")  # round-2 briefings
EXE_ORIG   = os.path.join(SRC_GAME, "PANZER2.EXE")        # stock (lang 0x09, 852992B)

GAME      = os.path.join(HERE, "game")
BUILD     = os.path.join(HERE, "build")
ATLAS_DIR = os.path.join(BUILD, "atlas")

TOP_FILES = ["GUI97.TXT", "MISC.TXT", "EQUIP97.TXT", "NAMES.TXT"]
SIZE_LIMITS = {"GUI97.TXT": 64*1024, "EQUIP97.TXT": 64*1024,
               "NAMES.TXT": 32*1024, "MISC.TXT": 64*1024, "_SCENARIO": 32*1024}


def round1_scen():
    return sorted(glob.glob(os.path.join(MASTERS1, "SCENARIO", "*.TXT")))

def round2_scen():
    return sorted(glob.glob(os.path.join(MASTERS2, "*.TXT")))

def all_masters():
    files = [os.path.join(MASTERS1, f) for f in TOP_FILES]
    files += round1_scen() + round2_scen()
    return files


def collect_strings():
    strings = []
    for f in all_masters():
        raw = open(f, "rb").read()
        if raw.endswith(b"\x1a"):
            raw = raw[:-1]
        # segment on whatever EOL the master uses; content chars are what matter for the atlas
        text = raw.decode("utf-8")
        strings.extend(text.replace("\r\n", "\n").split("\n"))
    return strings


def encode_master(src, dst, charmap):
    """Re-encode a UTF-8 master to dense 2-byte CJK, byte-faithful to the master's
    exact structure (CRLF or bare-LF segmentation + optional 0x1A EOF marker)."""
    raw = open(src, "rb").read()
    eof = raw.endswith(b"\x1a")
    if eof:
        raw = raw[:-1]
    b = bytearray()
    for ch in raw.decode("utf-8"):
        o = ord(ch)
        if o < 0x80:
            b.append(o)                       # ASCII incl \r \n structure -> single byte
        elif ch in charmap:
            b += bytes(charmap[ch])           # CJK/high char -> dense 2-byte
        else:
            raise ValueError(f"{os.path.basename(src)}: char {ch!r} U+{o:04X} not in atlas")
    data = bytes(b) + (b"\x1a" if eof else b"")
    if os.path.exists(dst):
        os.remove(dst)                        # break any hardlink; never truncate shared inode
    open(dst, "wb").write(data)
    return len(data)


def game_scen_map():
    """upper-base -> actual game/SCENARIO filename (preserve on-disk case)."""
    d = os.path.join(GAME, "SCENARIO")
    m = {}
    for f in os.listdir(d):
        if f.upper().endswith(".TXT"):
            m[f[:-4].upper()] = f
    return m


def main():
    os.makedirs(BUILD, exist_ok=True)
    r1, r2 = round1_scen(), round2_scen()
    print(f"[masters] round1 SCENARIO={len(r1)}  round2 SCENARIO={len(r2)}  total SCENARIO={len(r1)+len(r2)}")
    assert len(r1) + len(r2) == 302, f"expected 302 SCENARIO masters, got {len(r1)+len(r2)}"
    # disjoint check
    inter = {os.path.basename(p).upper() for p in r1} & {os.path.basename(p).upper() for p in r2}
    assert not inter, f"round1/round2 SCENARIO overlap: {inter}"

    # 1. atlas from the COMPLETE union char set
    strings = collect_strings()
    strings_path = os.path.join(BUILD, "strings.json")
    json.dump(strings, open(strings_path, "w"), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(TOOLS, "build_atlas_pg2.py"),
                    strings_path, ATLAS_DIR], check=True)
    charmap = json.load(open(os.path.join(ATLAS_DIR, "charmap.json")))
    ai = json.load(open(os.path.join(ATLAS_DIR, "atlas_index.json")))
    print(f"[atlas] {ai['count']} glyphs, maxlead 0x{ai['maxlead']:02x}, size {ai['atlas_size']}B")

    # 2. hooked EXE: main hook + gw-clamp + ww-safe + word-wrap 2-byte hook + title-fix,
    #    NO lang flip (English slot).
    hooked = os.path.join(BUILD, "PANZER2.EXE")
    subprocess.run([sys.executable, os.path.join(TOOLS, "build_hooked_exe_pg2.py"),
                    EXE_ORIG, os.path.join(ATLAS_DIR, "atlas_font.dat"), hooked, BUILD,
                    "--no-lang", "--gw-clamp", "--ww-safe", "--ww-hook"], check=True)

    # 3. game dir: fresh hardlink copy of the pristine extract, swap in hooked EXE
    if os.path.exists(GAME):
        shutil.rmtree(GAME)
    subprocess.run(["cp", "-al", SRC_GAME, GAME], check=True)
    ge = os.path.join(GAME, "PANZER2.EXE")
    os.remove(ge)
    shutil.copy(hooked, ge)

    # 4. encode ALL English-slot loose data files
    print("=== encoding loose data files ===")
    warnings = []
    for f in TOP_FILES:
        sz = encode_master(os.path.join(MASTERS1, f), os.path.join(GAME, f), charmap)
        lim = SIZE_LIMITS.get(f, 32*1024)
        flag = "  !!OVER" if sz > lim else ""
        if sz > lim: warnings.append(f"{f} {sz}B > {lim}")
        print(f"  {f:14s} {sz:7d}B / {lim}B{flag}")

    gmap = game_scen_map()
    n_enc = 0
    scen_over = 0
    for sm in r1 + r2:
        base = os.path.basename(sm)[:-4].upper()
        gfn = gmap.get(base)
        assert gfn is not None, f"no game SCENARIO file for master {base}"
        sz = encode_master(sm, os.path.join(GAME, "SCENARIO", gfn), charmap)
        n_enc += 1
        if sz > SIZE_LIMITS["_SCENARIO"]:
            scen_over += 1
            warnings.append(f"SCENARIO/{gfn} {sz}B > 32KB")
    print(f"  SCENARIO: {n_enc} files encoded, {scen_over} over 32KB")

    # 5. sanity
    d = open(ge, "rb").read()
    hf = 0x43e699 - 0x401000 + 0x400
    gf = 0x41b013 - 0x401000 + 0x400
    wf = 0x43e955 - 0x401000 + 0x400
    tf = 0x43dde0 - 0x401000 + 0x400
    print("=== EXE sanity ===")
    print(f"  lang byte @0xa32a0 = 0x{d[0xa32a0]:02x} (want 09 English)")
    print(f"  main hook @0x43e699 = 0x{d[hf]:02x} (want e9)")
    print(f"  gwclamp   @0x41b013 = 0x{d[gf]:02x} (want e9)")
    print(f"  ww-hook   @0x43e955 = 0x{d[wf]:02x} (want e9)")
    print(f"  title-fix @0x43dde0 = {d[tf:tf+4].hex()} (want NOT 833d44a7)")
    print(f"  size = {len(d)} bytes")
    # verify all 306 encoded loose files high-byte present where expected + count
    n_scen_game = len(glob.glob(os.path.join(GAME, "SCENARIO", "*.TXT"))) + \
                  len(glob.glob(os.path.join(GAME, "SCENARIO", "*.txt")))
    print(f"  game SCENARIO/*.TXT on disk = {n_scen_game}")
    if warnings:
        print("!!! SIZE WARNINGS:")
        for w in warnings: print("   ", w)
    else:
        print("[ok] all data files within size limits")
    print(f"[done] full release game dir: {GAME}")


if __name__ == "__main__":
    main()

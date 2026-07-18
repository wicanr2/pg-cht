#!/usr/bin/env python3
"""make_full_release.py — COMPLETE (full) PG2 CJK build, parametrized by font size.

Builds the COMPLETE Chinese release:
  * atlas built from the UNION of round-1 masters (翻譯/out: GUI97/MISC/EQUIP97/NAMES
    + 53 SCENARIO place-name files) AND round-2 masters (翻譯/briefings/out/SCENARIO:
    249 campaign-briefing prose files)  ->  full ~1,58x-char atlas;
  * ALL 4 top data files + ALL 302 SCENARIO/*.TXT re-encoded to dense 2-byte CJK
    and written over the English-slot loose .TXT of a FRESH pristine game copy;
  * hooked EXE = main draw hook (0x43e699) + glyphWidth clamp + word-wrap
    movsx->movzx safety + word-wrap 2-byte hook (0x43e955), WWSTUB advance/line-height
    parametrized by FONT_H ; NO language byte patch (English is the default slot, the
    game reads loose *.TXT) ; + global _pctype pointer repoint + _output NULL guard +
    2-byte-aware glyphWidth measure + status-bar clear-box residue fix (all below).

--- Font size / face (parametrized, chosen 2026-07-18 via a font-size/weight comparison) ---
Default: FONT_H=14, Noto Sans CJK **Medium**, TC face (index 3). Overridable via env
vars PG2_FONT_H / PG2_FONT_TTF / PG2_FONT_INDEX to rebuild the original 16px/Bold/
JP-face-by-omission recipe (778926f7: H=16, .../NotoSansCJK-Bold.ttc, index=0) or any
other size (12px was also prototyped). See build_atlas_pg2.py's docstring for why the
face index matters (JP vs TC punctuation-glyph placement) and patch_status_clear.py for
the clear-box residue fix (independent of font size choice, but needs fontH to size the
erase RECT).

--- Patch chain (validated end-to-end at H=14 before being folded into this script) ---
  atlas(H, font, face_index)
    -> hooked EXE: build_hooked_exe_pg2.build(--no-lang --gw-clamp --ww-safe --ww-hook,
       font_h=H, title_fix=False)                              [WWSTUB advance=H, lineheight=H+2]
    -> add_ctype_repoint.build                                 [global _pctype fix]
    -> patch_null_guard.build                                  [_output NULL guard]
    -> patch_gwclamp_2byte.build(font_h=H)                     [2-byte-aware width measure]
    -> patch_status_clear.build(fontH=H)                       [status-bar clear-box residue fix]
  => <out>/PANZER2.EXE

NOTE on title_fix / the "5 ctype classifier" patches: build_hooked_exe_pg2.py can patch
the readScenarioTitle classifier (title_fix=True) and extend_titlefix.py can patch its 4
siblings (campaign list etc) — the ORIGINAL per-site fix for scenario/campaign-list name
truncation. Root-cause tracing found the real cause is CRT `_pctype`: a signed-char
negative index into the ctype table on any high (CJK) byte yields a garbage class, so the
line "terminates" early. The GLOBAL pointer-repoint fix (add_ctype_repoint.py, applied
below) fixes this at its one true source and is a confirmed STRICT SUPERSET of the 5
per-site classifier patches — verified here by inspecting the H=14 reference build
(scratchpad `ctypefix/fontsize/exe14_med_sc.exe`): repoint IS applied, all 5 classifier
call sites are STILL byte-identical to stock (title_fix was never run on it), and the
scenario/campaign lists render fully un-truncated. Applying title_fix on top would be
harmless (disjoint bytes) but a redundant duplicate patch of an already-fixed root cause,
so this script leaves title_fix=False / does not call extend_titlefix.py — the
"5-classifier" fix IS present in the build, delivered via repoint instead of per-site code
patches.

--- Source layout (env-var overridable; defaults assume a repo-relative staging layout
    that must be populated BEFORE running -- the pristine game and translated masters are
    not committed to git: copyrighted binary assets / regenerable build products) ---
  PG2_SRC_GAME  default <pg2>/Panzer2            pristine 7z-extracted original game
                                                   (PANZER2.EXE + all loose data, incl. a
                                                   pristine, never-hand-edited SCENARIO/)
  PG2_MASTERS1  default <pg2>/翻譯/out            round-1 UTF-8 masters (apply_translations.py)
  PG2_MASTERS2  default <pg2>/翻譯/briefings/out/SCENARIO   round-2 masters (apply_briefings.py)
  PG2_OUT_DIR   default <pg2>/build/_out          where build/ and game/ land

Nothing in the repo or the pristine game tree is modified. Hardlink/copy loose files are
removed before a fresh encoded file is written, so no shared source inode is ever
truncated.
"""
import os, sys, json, subprocess, shutil, glob, struct, importlib.util

HERE   = os.path.dirname(os.path.abspath(__file__))       # pg2/build/
PG2    = os.path.dirname(HERE)                             # pg2/
TOOLS  = HERE                                               # all build_*.py / patch_*.py live here

SRC_GAME = os.environ.get("PG2_SRC_GAME", os.path.join(PG2, "Panzer2"))
MASTERS1 = os.environ.get("PG2_MASTERS1", os.path.join(PG2, "翻譯", "out"))
MASTERS2 = os.environ.get("PG2_MASTERS2", os.path.join(PG2, "翻譯", "briefings", "out", "SCENARIO"))
OUT_DIR  = os.environ.get("PG2_OUT_DIR", os.path.join(HERE, "_out"))
EXE_ORIG = os.path.join(SRC_GAME, "PANZER2.EXE")        # stock (lang 0x09, 852992B)

FONT_H     = int(os.environ.get("PG2_FONT_H", "14"))
FONT_TTF   = os.environ.get("PG2_FONT_TTF", "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc")
FONT_INDEX = int(os.environ.get("PG2_FONT_INDEX", "3"))    # 3 = Traditional Chinese face

GAME      = os.path.join(OUT_DIR, "game")
BUILD     = os.path.join(OUT_DIR, "build")
ATLAS_DIR = os.path.join(BUILD, "atlas")

TOP_FILES = ["GUI97.TXT", "MISC.TXT", "EQUIP97.TXT", "NAMES.TXT"]
SIZE_LIMITS = {"GUI97.TXT": 64*1024, "EQUIP97.TXT": 64*1024,
               "NAMES.TXT": 32*1024, "MISC.TXT": 64*1024, "_SCENARIO": 32*1024}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


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
    print(f"[cfg] FONT_H={FONT_H} FONT_TTF={FONT_TTF} FONT_INDEX={FONT_INDEX}")
    print(f"[cfg] SRC_GAME={SRC_GAME}")
    print(f"[cfg] MASTERS1={MASTERS1}")
    print(f"[cfg] MASTERS2={MASTERS2}")
    print(f"[cfg] OUT_DIR={OUT_DIR}")
    r1, r2 = round1_scen(), round2_scen()
    print(f"[masters] round1 SCENARIO={len(r1)}  round2 SCENARIO={len(r2)}  total SCENARIO={len(r1)+len(r2)}")
    assert len(r1) + len(r2) == 302, f"expected 302 SCENARIO masters, got {len(r1)+len(r2)}"
    # disjoint check
    inter = {os.path.basename(p).upper() for p in r1} & {os.path.basename(p).upper() for p in r2}
    assert not inter, f"round1/round2 SCENARIO overlap: {inter}"

    # 1. atlas from the COMPLETE union char set, at FONT_H / FONT_TTF / FONT_INDEX
    strings = collect_strings()
    strings_path = os.path.join(BUILD, "strings.json")
    json.dump(strings, open(strings_path, "w"), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(TOOLS, "build_atlas_pg2.py"),
                    strings_path, ATLAS_DIR, str(FONT_H), FONT_TTF, str(FONT_INDEX)], check=True)
    charmap = json.load(open(os.path.join(ATLAS_DIR, "charmap.json")))
    ai = json.load(open(os.path.join(ATLAS_DIR, "atlas_index.json")))
    print(f"[atlas] {ai['count']} glyphs, maxlead 0x{ai['maxlead']:02x}, size {ai['atlas_size']}B")

    # 2. hooked EXE: main hook + gw-clamp(placeholder) + ww-safe + word-wrap 2-byte hook,
    #    WWSTUB advance/lineheight = FONT_H/FONT_H+2, NO lang flip, NO per-site title_fix
    #    (superseded by the global ctype repoint applied in step 4 -- see module docstring).
    hooked = os.path.join(BUILD, "hooked.exe")
    subprocess.run([sys.executable, os.path.join(TOOLS, "build_hooked_exe_pg2.py"),
                    EXE_ORIG, os.path.join(ATLAS_DIR, "atlas_font.dat"), hooked, BUILD,
                    "--no-lang", "--gw-clamp", "--ww-safe", "--ww-hook", "--no-title-fix",
                    "--font-h", str(FONT_H)], check=True)

    # 3. global _pctype pointer repoint (fixes scenario/campaign list truncation at its root)
    repoint = os.path.join(BUILD, "repoint.exe")
    subprocess.run([sys.executable, os.path.join(TOOLS, "add_ctype_repoint.py"),
                    hooked, repoint], check=True)

    # 4. _output NULL guard (right-click info popup crash fix)
    guard = os.path.join(BUILD, "guard.exe")
    subprocess.run([sys.executable, os.path.join(TOOLS, "patch_null_guard.py"),
                    repoint, guard, BUILD], check=True)

    # 5. 2-byte-aware glyphWidth measure (replaces the simple byte-clamp with a real
    #    half-width for CJK so tooltip/status-bar/purchase-name centering is correct)
    gwclamped = os.path.join(BUILD, "gwclamp2b.exe")
    subprocess.run([sys.executable, os.path.join(TOOLS, "patch_gwclamp_2byte.py"),
                    guard, gwclamped, str(FONT_H)], check=True)

    # 6. status-bar clear-box residue fix (bottom = top + FONT_H + 1)
    hooked_final = os.path.join(BUILD, "PANZER2.EXE")
    subprocess.run([sys.executable, os.path.join(TOOLS, "patch_status_clear.py"),
                    gwclamped, hooked_final, str(FONT_H)], check=True)

    # 7. game dir: fresh hardlink copy of the pristine extract, swap in hooked EXE
    if os.path.exists(GAME):
        shutil.rmtree(GAME)
    subprocess.run(["cp", "-al", SRC_GAME, GAME], check=True)
    ge = os.path.join(GAME, "PANZER2.EXE")
    os.remove(ge)
    shutil.copy(hooked_final, ge)

    # 8. encode ALL English-slot loose data files
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

    # 9. sanity
    d = open(ge, "rb").read()
    hf = 0x43e699 - 0x401000 + 0x400
    gf = 0x41b013 - 0x401000 + 0x400
    wf = 0x43e955 - 0x401000 + 0x400
    print("=== EXE sanity ===")
    print(f"  lang byte @0xa32a0 = 0x{d[0xa32a0]:02x} (want 09 English)")
    print(f"  main hook @0x43e699 = 0x{d[hf]:02x} (want e9)")
    print(f"  gwclamp   @0x41b013 = 0x{d[gf]:02x} (want e9)")
    print(f"  ww-hook   @0x43e955 = 0x{d[wf]:02x} (want e9)")
    print(f"  size = {len(d)} bytes  md5={__import__('hashlib').md5(d).hexdigest()}")
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

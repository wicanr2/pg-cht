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
  atlas(H, font, face_index)  [+ atlas12(BRIEF_FONT_H) for step 8, same char set/dense map]
    -> hooked EXE: build_hooked_exe_pg2.build(--no-lang --gw-clamp --ww-safe --ww-hook,
       font_h=H, title_fix=False)                              [WWSTUB advance=H, lineheight=H+2]
    -> add_ctype_repoint.build                                 [global _pctype fix]
    -> patch_null_guard.build                                  [_output NULL guard]
    -> patch_gwclamp_2byte.build(font_h=H)                     [2-byte-aware width measure]
    -> patch_status_clear.build(fontH=H)                       [status-bar clear-box residue fix]
    -> patch_briefing_wrapcount_clone.build                    [briefing wrap/line-count clone -> orig ctype]
    -> patch_briefing_font12.build(BRIEF_FONT_H)               [briefing-only smaller font + full box]
  => <out>/PANZER2.EXE

--- Why the 8th patch (briefing-only smaller font, default 12px) ---
User (2026-07-19): the on-map campaign briefing prose is too big at 14px AND its box clips
the paragraph (only ~7 of ~11 lines shown). Two briefing-only defects, fixed together with
zero blast radius: (a) FONT TOO BIG -- the prose goes through the SHARED drawWrappedText
@0x43e752 (11 callers, verified by xref), so it can't be shrunk by swapping the atlas; step 8
appends a 2nd BRIEF_FONT_H atlas + a flag-dispatched WWSTUB and wraps ONLY the two on-map
briefing box-drawers so only the briefing is smaller. (b) BOX CLIPPED -- the drawer sizes the
box as countLines * 10 (native 8px-font pitch), but the CJK render pitch is FONT_H+2, so the
box was ~10/16 of the needed height; step 8 rescales the two box-height sites (0x456e1d/
0x45701c) to countLines * (BRIEF_FONT_H+2). countLines still measures at the (wider) FONT_H
width, so its line count >= the BRIEF_FONT_H render's -> the box is always tall enough. See
patch_briefing_font12.py.

--- Why the 7th patch (briefing wrap/line-count clone) ---
The step-3 _pctype repoint fixes scenario/campaign list truncation + status bar + the
requisition family at their root, but its blast radius reaches the on-map campaign/advisor
briefing panel, collapsing its tall full-text window (repo hero shot
evidence/pg2-campaign-briefing-cht.png) into a short box that spills onto the map. Wine A/B
localized the true cause to countLines @0x43fdd5 -- the wrap/line-count routine that sizes
the box HEIGHT -- NOT measureWidthMultiline @0x43eba0 (whose line count is '\n'-based and
ctype-independent; a clone of it was proven a no-op, and suppressing briefing_open @0x460f17
left the box intact). countLines classifies each byte via [0x4ba538] (0x43ff02/0x43ffc5);
post-repoint a CJK byte reads the 0x0100 (_ALPHA) shadow -> "unbreakable" -> the wrapper can
not break the CJK run -> few lines -> collapse. A global revert is wrong: countLines has 19
callers (the repoint doc's "requisition family" reads ARE these). So step 7 clones countLines
into a fresh .brm section, changes ONLY its two ctype-table bases back to the original
0x4ba542, and redirects ONLY the two on-map briefing box drawers (0x456e01 in fn 0x456d32,
0x457000 in fn 0x456efb). The shared routine and its other 17 callers are byte-untouched ->
zero blast radius. Proven in wine: tall full-text box restored, 0 page faults. See
patch_briefing_wrapcount_clone.py.

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

# Briefing prose font size (smaller than the 14px UI, per user request 2026-07-19). The
# on-map campaign/scenario briefing goes through a SHARED word-wrap routine (drawWrappedText
# @0x43e752, 11 callers), so it can NOT be shrunk by simply swapping the atlas. Step 8
# (patch_briefing_font12) appends a 2nd 12px atlas + a flag-dispatched WWSTUB and wraps ONLY
# the 2 on-map briefing box-drawers (0x456d32 / 0x456efb) so the briefing prose renders at
# BRIEF_FONT_H while every other drawWrappedText caller (advisor tips, help/message boxes)
# and all drawStringCore UI (menus/lists/status bar/purchase/unit-info) stay at FONT_H. It
# also fixes the briefing box HEIGHT (the drawer sizes it as countLines * native-10px-pitch,
# far too short for the CJK render pitch -> the paragraph clipped; step 8 rescales it to
# countLines * (BRIEF_FONT_H+2) so the whole paragraph fits). Set PG2_BRIEFING12=0 to skip
# (reproduces the pre-2026-07-19 all-14px build). The 12px atlas is built from the SAME
# char set as the main atlas, so its dense mapping is identical -> the dense-encoded *.TXT
# data files are reused verbatim; only the glyph pixels differ.
BRIEF_FONT12    = os.environ.get("PG2_BRIEFING12", "1") != "0"
BRIEF_FONT_H    = int(os.environ.get("PG2_BRIEF_FONT_H", "12"))
BRIEF_FONT_TTF  = os.environ.get("PG2_BRIEF_FONT_TTF", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BRIEF_FONT_INDEX= int(os.environ.get("PG2_BRIEF_FONT_INDEX", "3"))  # 3 = Traditional Chinese face
# Briefing box HEIGHT per-line pitch (box = countLines * BRIEF_BOX_PITCH). DECOUPLED from the
# render line pitch (BRIEF_FONT_H+2) because countLines under-counts vs the atlas render for CJK
# -> a pitch == render pitch still clips the last line(s). Calibrated in wine (2026-07-19) so
# the longest opening briefing shows in full; extra slack just leaves empty box below (matches
# the original tall-box look, evidence/pg2-campaign-briefing-cht.png). See §7.13.
BRIEF_BOX_PITCH = int(os.environ.get("PG2_BRIEF_BOX_PITCH", "24"))

GAME      = os.path.join(OUT_DIR, "game")
BUILD     = os.path.join(OUT_DIR, "build")
ATLAS_DIR = os.path.join(BUILD, "atlas")
ATLAS12_DIR = os.path.join(BUILD, "atlas12")   # briefing-only smaller atlas (step 8)

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

    # 1b. briefing-only smaller atlas from the SAME strings.json -> identical dense mapping
    #     (dense depends only on the sorted char set, not H/font), so the encoded *.TXT reuse
    #     unchanged and patch_briefing_font12 can share the main atlas's dense codes.
    if BRIEF_FONT12:
        subprocess.run([sys.executable, os.path.join(TOOLS, "build_atlas_pg2.py"),
                        strings_path, ATLAS12_DIR, str(BRIEF_FONT_H), BRIEF_FONT_TTF,
                        str(BRIEF_FONT_INDEX)], check=True)
        a12 = json.load(open(os.path.join(ATLAS12_DIR, "atlas_index.json")))
        assert a12["count"] == ai["count"], \
            f"briefing atlas count {a12['count']} != main atlas count {ai['count']} (dense map would diverge)"
        print(f"[atlas12] {a12['count']} glyphs @H={BRIEF_FONT_H} "
              f"({os.path.basename(BRIEF_FONT_TTF)}#{BRIEF_FONT_INDEX}) for briefing prose")

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
    statusclear = os.path.join(BUILD, "statusclear.exe")
    subprocess.run([sys.executable, os.path.join(TOOLS, "patch_status_clear.py"),
                    gwclamped, statusclear, str(FONT_H)], check=True)

    # 7. briefing-only countLines (@0x43fdd5) clone that reads the ORIGINAL _pctype table
    #    (0x4ba542), undoing the step-3 repoint blast-radius on the on-map campaign/advisor
    #    briefing panel ONLY. The shared routine 0x43fdd5 and its 17 other callers stay
    #    byte-identical (only the 2 box-drawer callers 0x456e01/0x457000 are redirected).
    #    Only ordering requirement: after the repoint (step 3).
    hooked_final = os.path.join(BUILD, "PANZER2.EXE")
    clone_out = os.path.join(BUILD, "clone.exe") if BRIEF_FONT12 else hooked_final
    subprocess.run([sys.executable, os.path.join(TOOLS, "patch_briefing_wrapcount_clone.py"),
                    statusclear, clone_out], check=True)

    # 8. briefing-only smaller font (default 12px). Appends a .b12 section holding a 2nd
    #    (BRIEF_FONT_H) atlas + a flag-dispatched WWSTUB, repoints the word-wrap hook to a
    #    dispatch, and wraps ONLY the two on-map briefing box-drawer render calls (0x456e8d/
    #    0x45706b) with a flag trampoline -> only the briefing prose is smaller; the other 9
    #    drawWrappedText callers and all drawStringCore UI keep FONT_H. Also rescales the
    #    briefing box HEIGHT (native x10 -> x(BRIEF_FONT_H+2)) so the whole paragraph is shown.
    #    Must run last (after the clone), on the fully-hooked EXE. Zero blast radius: one new
    #    appended section + repointed ww-hook rel32 + 2 render-call rel32 + 2 box-height sites.
    if BRIEF_FONT12:
        subprocess.run([sys.executable, os.path.join(TOOLS, "patch_briefing_font12.py"),
                        clone_out, os.path.join(ATLAS12_DIR, "atlas_font.dat"),
                        hooked_final, BUILD, str(BRIEF_FONT_H), str(BRIEF_BOX_PITCH)], check=True)

    # 8. game dir: fresh hardlink copy of the pristine extract, swap in hooked EXE
    if os.path.exists(GAME):
        shutil.rmtree(GAME)
    subprocess.run(["cp", "-al", SRC_GAME, GAME], check=True)
    ge = os.path.join(GAME, "PANZER2.EXE")
    os.remove(ge)
    shutil.copy(hooked_final, ge)

    # 9. encode ALL English-slot loose data files
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

    # 10. sanity
    d = open(ge, "rb").read()
    hf = 0x43e699 - 0x401000 + 0x400
    gf = 0x41b013 - 0x401000 + 0x400
    wf = 0x43e955 - 0x401000 + 0x400
    print("=== EXE sanity ===")
    print(f"  lang byte @0xa32a0 = 0x{d[0xa32a0]:02x} (want 09 English)")
    print(f"  main hook @0x43e699 = 0x{d[hf]:02x} (want e9)")
    print(f"  gwclamp   @0x41b013 = 0x{d[gf]:02x} (want e9)")
    print(f"  ww-hook   @0x43e955 = 0x{d[wf]:02x} (want e9)")
    # briefing clone: the 2 box-drawer callers must now target the .brm countLines clone
    for cva in (0x456e01, 0x457000):
        cf = cva - 0x401000 + 0x400
        ctgt = cva + 5 + struct.unpack_from('<i', d, cf+1)[0]
        print(f"  briefing drawer @0x{cva:x} -> 0x{ctgt:x} (want a .brm clone VA, NOT 0x43fdd5)")
        assert ctgt != 0x43fdd5 and ctgt >= 0x5c0000, f"caller 0x{cva:x} not redirected: 0x{ctgt:x}"
    # shared countLines @0x43fdd5 must be byte-identical to stock (still reads [0x4ba538])
    mf = 0x43fdd5 - 0x401000 + 0x400
    assert d[mf+0x12d:mf+0x12d+6] == bytes.fromhex("8b0d38a54b00"), "shared 0x43fdd5 was modified!"
    # briefing font12 (step 8): box-height sites rescaled + render calls -> .b12 trampoline
    if BRIEF_FONT12:
        for bva in (0x456e1d, 0x45701c):          # imul eax,eax,BRIEF_BOX_PITCH ; nop ; nop
            bf = bva - 0x401000 + 0x400
            assert d[bf] == 0x6b and d[bf+2] == BRIEF_BOX_PITCH and d[bf+3:bf+5] == b"\x90\x90", \
                f"box-height @0x{bva:x} not rescaled to x{BRIEF_BOX_PITCH}: {d[bf:bf+5].hex()}"
            print(f"  briefing box-h @0x{bva:x} = imul eax,eax,{BRIEF_BOX_PITCH} "
                  f"(was x10; render pitch {BRIEF_FONT_H+2})")
        for rva in (0x456e8d, 0x45706b):          # call briefing render -> .b12 trampoline
            rf = rva - 0x401000 + 0x400
            rtgt = rva + 5 + struct.unpack_from('<i', d, rf+1)[0]
            assert rtgt >= 0x5c0000 and rtgt != 0x460193, f"render call @0x{rva:x} not wrapped: 0x{rtgt:x}"
            print(f"  briefing render @0x{rva:x} -> 0x{rtgt:x} (flag trampoline, not 0x460193)")
        # a .b12 section must be present, and the ww-hook must point into it
        e = struct.unpack_from('<I', d, 0x3c)[0]; coff2 = e+4
        nsec2 = struct.unpack_from('<H', d, coff2+2)[0]; osz2 = struct.unpack_from('<H', d, coff2+16)[0]
        st2 = coff2+20+osz2
        names = [d[st2+i*40:st2+i*40+8].rstrip(b"\0") for i in range(nsec2)]
        assert b".b12" in names, f"no .b12 section: {names}"
        print(f"  sections = {[n.decode(errors='replace') for n in names]}")
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

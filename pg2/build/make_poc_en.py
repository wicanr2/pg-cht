#!/usr/bin/env python3
"""make_poc_en.py — English-mode CJK engine POC (no language flip).
Proves the drawStringCore hook + atlas render CJK, in the game's known-good English
boot (valid font global, no black French logo). Dense-coded Chinese is injected into
the ENGLISH data files (GUI97.TXT / MISC.TXT) that English mode already reads loose.
"""
import os, sys, json, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_poc as M   # reuse translations + encode helpers

BASE = M.BASE
SRC_GAME = M.SRC_GAME
GAME = os.path.join(BASE, "game_en")
BUILD = M.BUILD
ATLAS_DIR = M.ATLAS_DIR
EXE_ORIG = M.EXE_ORIG

def main():
    os.makedirs(BUILD, exist_ok=True)
    all_zh = list(M.GUI97.values()) + list(M.MISC.values())
    strings_path = os.path.join(BUILD, "strings.json")
    json.dump(all_zh, open(strings_path, "w"), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(HERE, "build_atlas_pg2.py"),
                    strings_path, ATLAS_DIR], check=True)
    charmap = json.load(open(os.path.join(ATLAS_DIR, "charmap.json")))
    hooked = os.path.join(BUILD, "PANZER2_en.EXE")
    subprocess.run([sys.executable, os.path.join(HERE, "build_hooked_exe_pg2.py"),
                    EXE_ORIG, os.path.join(ATLAS_DIR, "atlas_font.dat"), hooked, BUILD, "--no-lang"],
                   check=True)
    if os.path.exists(GAME):
        shutil.rmtree(GAME)
    subprocess.run(["cp", "-al", SRC_GAME, GAME], check=True)
    for f in ("PANZER2.EXE", "GUI97.TXT", "MISC.TXT"):
        p = os.path.join(GAME, f)
        if os.path.exists(p):
            os.remove(p)
    shutil.copy(hooked, os.path.join(GAME, "PANZER2.EXE"))
    # patch the ENGLISH data files in place with dense Chinese
    M.encode_file(os.path.join(SRC_GAME, "GUI97.TXT"), os.path.join(GAME, "GUI97.TXT"), M.GUI97, charmap)
    M.encode_file(os.path.join(SRC_GAME, "MISC.TXT"),  os.path.join(GAME, "MISC.TXT"),  M.MISC, charmap)
    d = open(os.path.join(GAME, "PANZER2.EXE"), "rb").read()
    print(f"[verify] lang byte @0xa32a0 = 0x{d[0xa32a0]:02x} (want 09 = English)")
    hf = 0x43e699 - 0x401000 + 0x400
    print(f"[verify] hook @0x43e699 first byte = 0x{d[hf]:02x} (want e9)")
    print(f"[done] English POC game dir: {GAME}")

if __name__ == "__main__":
    main()

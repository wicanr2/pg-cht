#!/usr/bin/env python3
"""make_poc.py — end-to-end PG2 CJK POC build.
1. define test translations (GUI97 + MISC lines)
2. build 16x16 atlas from their chars
3. build hooked EXE (.cjk section + drawString hook + lang byte)
4. lay out a fresh game dir (hardlink copy) + write dense-encoded *.FRA
No repo/original files touched; everything under build_poc/.
"""
import os, sys, json, subprocess, shutil, struct

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                       # build_poc/
SP   = os.path.dirname(os.path.dirname(BASE))      # scratchpad/
SRC_GAME = os.path.join(SP, "pg2", "Panzer2")
GAME = os.path.join(BASE, "game")
BUILD = os.path.join(BASE, "build")
ATLAS_DIR = os.path.join(BUILD, "atlas")
EXE_ORIG = os.path.join(BASE, "PANZER2.EXE.orig")

# --- test translations (exact source line -> Traditional Chinese) ---
GUI97 = {
    "Next Unit": "下一部隊",
    "Supply": "補給",
    "Strategic Map": "戰略地圖",
    "Game Functions": "遊戲功能",
    "Additional Options": "其他選項",
    "How To Play The Game": "遊戲教學",
    "End Turn": "結束回合",
    "Full Screen": "全螢幕",
    "Air Mode": "空戰模式",
    "Exit Game": "離開遊戲",
    "Upgrade Unit": "升級部隊",
    "Undo Last Action": "復原動作",
    "Requisition Unit": "徵召部隊",
    "Field Headquarters": "野戰指揮部",
    "Brilliant Victory": "輝煌勝利",
    "Victory": "勝利",
    "Tactical Victory": "戰術勝利",
    "Loss": "戰敗",
    "Germany": "德國",
    "Russia": "蘇聯",
    "France": "法國",
    "USA": "美國",
    "Italy": "義大利",
    "Poland": "波蘭",
    "United Kingdom": "英國",
    "Axis": "軸心國",
    "Allied": "同盟國",
}
MISC = {
    "CLEAR": "平原",
    "CITY": "城市",
    "AIRFIELD": "機場",
    "FOREST": "森林",
    "HILL": "丘陵",
    "MOUNTAIN": "山地",
    "OCEAN": "海洋",
    "RIVER": "河流",
    "PORT": "港口",
    "SWAMP": "沼澤",
    "FORTIFICATION": "碉堡",
}

def encode_text(s, charmap):
    out = bytearray()
    for ch in s:
        if ch in charmap:
            out += bytes(charmap[ch])
        else:
            out += ch.encode("latin1")
    return bytes(out)

def encode_file(src_txt, dst_fra, tr, charmap):
    raw = open(src_txt, "rb").read()
    segs = raw.split(b"\r\n")
    new = []
    hits = 0
    for seg in segs:
        key = seg.decode("latin1")
        eof = key.endswith("\x1a")
        core = key[:-1] if eof else key
        if core in tr:
            enc = bytearray(encode_text(tr[core], charmap))
            if eof: enc += b"\x1a"
            new.append(bytes(enc)); hits += 1
        else:
            new.append(seg)
    open(dst_fra, "wb").write(b"\r\n".join(new))
    print(f"[fra] {os.path.basename(dst_fra)}: translated {hits}/{len(tr)} lines")

def main():
    os.makedirs(BUILD, exist_ok=True)
    # 1. strings.json for atlas
    all_zh = list(GUI97.values()) + list(MISC.values())
    strings_path = os.path.join(BUILD, "strings.json")
    json.dump(all_zh, open(strings_path, "w"), ensure_ascii=False)
    # 2. atlas
    subprocess.run([sys.executable, os.path.join(HERE, "build_atlas_pg2.py"),
                    strings_path, ATLAS_DIR], check=True)
    charmap = json.load(open(os.path.join(ATLAS_DIR, "charmap.json")))
    # 3. hooked exe
    hooked = os.path.join(BUILD, "PANZER2.EXE")
    subprocess.run([sys.executable, os.path.join(HERE, "build_hooked_exe_pg2.py"),
                    EXE_ORIG, os.path.join(ATLAS_DIR, "atlas_font.dat"), hooked, BUILD], check=True)
    # 4. game dir: fresh hardlink copy (shares PANZER2.DAT etc.), break EXE link
    if os.path.exists(GAME):
        shutil.rmtree(GAME)
    subprocess.run(["cp", "-al", SRC_GAME, GAME], check=True)
    for f in ("PANZER2.EXE",):
        p = os.path.join(GAME, f)
        if os.path.exists(p): os.remove(p)
    shutil.copy(hooked, os.path.join(GAME, "PANZER2.EXE"))
    # write *.FRA (encoded for GUI97/MISC; plain copies for the rest the game opens)
    encode_file(os.path.join(SRC_GAME, "GUI97.TXT"), os.path.join(GAME, "GUI97.FRA"), GUI97, charmap)
    encode_file(os.path.join(SRC_GAME, "MISC.TXT"),  os.path.join(GAME, "MISC.FRA"),  MISC, charmap)
    for f in ("EQUIP97", "NAMES"):
        shutil.copy(os.path.join(SRC_GAME, f+".TXT"), os.path.join(GAME, f+".FRA"))
    # sanity: EXE lang byte + hook
    d = open(os.path.join(GAME, "PANZER2.EXE"), "rb").read()
    print(f"[verify] lang byte @0xa32a0 = 0x{d[0xa32a0]:02x} (want 0c)")
    hf = 0x43e699 - 0x401000 + 0x400
    print(f"[verify] hook @0x43e699 first byte = 0x{d[hf]:02x} (want e9)")
    print(f"[done] game dir: {GAME}")

if __name__ == "__main__":
    main()

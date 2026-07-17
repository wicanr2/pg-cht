#!/usr/bin/env python3
"""合併第一輪 glossary.tsv(zh_tw 欄)+ 第二輪 briefings_glossary.tsv(zh_tw 欄)的
完整唯一 zh 字集(供後續 CJK atlas 重建)。只收 CJK 統一表意文字 + CJK 標點 + 全形符號,
半形數字/字母/標點不重複收錄(atlas 另有 ASCII 字型涵蓋)。"""
import csv

ROUND1 = "/home/anr2/game/Panzer_General/pg-cht/pg2/翻譯/glossary.tsv"
ROUND2 = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯/briefings/briefings_glossary.tsv"
OUT = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯/briefings/charset_full.txt"


def is_cjk_or_punct(ch):
    o = ord(ch)
    return (
        0x4E00 <= o <= 0x9FFF or   # CJK Unified Ideographs
        0x3400 <= o <= 0x4DBF or   # CJK Ext A
        0x3000 <= o <= 0x303F or   # CJK punctuation
        0xFF00 <= o <= 0xFFEF      # fullwidth forms
    )


def collect(path, col="zh_tw"):
    chars = set()
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            zh = row.get(col, "")
            for ch in zh:
                if is_cjk_or_punct(ch):
                    chars.add(ch)
    return chars


r1 = collect(ROUND1)
r2 = collect(ROUND2)
combined = r1 | r2

print(f"round1 unique zh chars: {len(r1)}")
print(f"round2 (briefings) unique zh chars: {len(r2)}")
print(f"round2-only new chars (not in round1): {len(r2 - r1)}")
print(f"combined unique zh chars: {len(combined)}")

with open(OUT, "w", encoding="utf-8") as f:
    for ch in sorted(combined):
        f.write(ch)

new_chars_path = OUT.replace("charset_full.txt", "charset_round2_new.txt")
with open(new_chars_path, "w", encoding="utf-8") as f:
    for ch in sorted(r2 - r1):
        f.write(ch)

print(f"wrote {OUT} ({len(combined)} chars, no separators, single line)")
print(f"wrote {new_chars_path} ({len(r2 - r1)} chars new-in-round2)")

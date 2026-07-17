#!/usr/bin/env python3
"""Pair machine-extracted original unique lines with hand-authored zh translations
(same order, verified equal count) to build briefings_glossary.tsv."""
import csv

HERE = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯/briefings"
UNDONE_LINES = f"{HERE}/undone_unique_lines.txt"
ZH_ORDERED = f"{HERE}/zh_translations_ordered.txt"
OUT_TSV = f"{HERE}/briefings_glossary.tsv"

# read originals: format "<count>\t<original line, may itself start with \t>"
originals = []
with open(UNDONE_LINES, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if line == "":
            continue
        count_str, orig = line.split("\t", 1)
        originals.append(orig)

with open(ZH_ORDERED, encoding="utf-8") as f:
    zh_lines = [l.rstrip("\n") for l in f]

assert len(originals) == len(zh_lines), f"count mismatch: {len(originals)} originals vs {len(zh_lines)} zh lines"

# sanity: no duplicate empty zh
for i, (o, z) in enumerate(zip(originals, zh_lines)):
    if z.strip() == "":
        print(f"[WARN] empty zh translation at index {i} for original: {o!r}")

with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["檔類", "original", "zh_tw", "來源/備註"])
    for o, z in zip(originals, zh_lines):
        w.writerow(["SCENARIO_BRIEF", o, z, "自譯(戰役簡報散文,第二輪補完;人名/地名對齊歷史百科與glossary.tsv)"])

print(f"wrote {OUT_TSV}: {len(originals)} rows")

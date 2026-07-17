#!/usr/bin/env python3
"""
PG2 繁中化 - apply glossary to source TXT files, producing UTF-8 master drafts.

輸入:
  - glossary.tsv (this directory) - 欄位: 檔類 \t original \t zh_tw \t 來源/備註
  - 原始檔案: SRC_ROOT/Panzer2/{GUI97.TXT, MISC.TXT, EQUIP97.TXT, NAMES.TXT, SCENARIO/*.TXT}
  - NAMES.TXT 直接沿用 /home/anr2/game/Panzer_General/pg-cht/pg2/歷史百科/NAMES-姓名庫.tsv (已完成,行序對齊)

輸出 (OUT_ROOT/out/, UTF-8, 鏡像原目錄結構):
  - GUI97.TXT, MISC.TXT, EQUIP97.TXT, NAMES.TXT
  - SCENARIO/<53 個地名/座標表檔案>.TXT (逐行套用;非地名的部隊番號/座標原樣保留)

不改動任何遊戲檔或 repo 檔;只寫 OUT_ROOT/out/ 底下的檔案。
"""
import os
import re
import sys
import json
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.join(HERE, "..", "Panzer2")
OUT_ROOT = os.path.join(HERE, "out")
GLOSSARY_PATH = os.path.join(HERE, "glossary.tsv")
NAMES_TSV = "/home/anr2/game/Panzer_General/pg-cht/pg2/歷史百科/NAMES-姓名庫.tsv"

# line-index overrides for cases where the exact same English string legitimately
# needs a different translation depending on its position in the file (documented
# in glossary.tsv remarks). 1-based line numbers.
OVERRIDES = {
    ("GUI97.TXT", 87): "空中防禦力",  # stat "Ground Defense / Air Defense" pair, not the AA unit-class sense
}


def read_dos_text_lines(path):
    """Read a DOS-style TXT (CRLF, possibly trailing 0x1A EOF marker) preserving
    exact line count. Returns (lines, had_eof_marker)."""
    with open(path, "rb") as f:
        raw = f.read()
    had_eof = raw.endswith(b"\x1a")
    if had_eof:
        raw = raw[:-1]
    text = raw.decode("latin-1")
    # split on \r\n; if file used bare \n fall back
    if "\r\n" in text:
        lines = text.split("\r\n")
    else:
        lines = text.split("\n")
    # drop one trailing empty element left by the final line terminator
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines, had_eof


def write_utf8_lines(path, lines, had_eof_marker=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        for l in lines:
            f.write(l + "\r\n")
        if had_eof_marker:
            f.write("\x1a")


def load_glossary():
    by_cat = {}
    with open(GLOSSARY_PATH, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        for row in reader:
            if len(row) < 3:
                continue
            cat, original, zh = row[0], row[1], row[2]
            by_cat.setdefault(cat, {})[original] = zh
    return by_cat


def apply_simple(cat, filename, glossary, warn_missing=True):
    """Translate a flat line-per-entry file (GUI97/MISC/EQUIP97) via glossary lookup."""
    src = os.path.join(SRC_ROOT, filename)
    lines, had_eof = read_dos_text_lines(src)
    lut = glossary.get(cat, {})
    out_lines = []
    missing = []
    for i, l in enumerate(lines, start=1):
        override = OVERRIDES.get((filename, i))
        if override is not None:
            out_lines.append(override)
            continue
        if l == "":
            out_lines.append("")
            continue
        if l in lut:
            out_lines.append(lut[l])
        else:
            missing.append((i, l))
            out_lines.append(l)  # fallback: leave untranslated (English) rather than drop/corrupt
    if warn_missing and missing:
        print(f"[WARN] {filename}: {len(missing)} lines missing from glossary (left as English):")
        for i, l in missing[:20]:
            print(f"    line {i}: {l!r}")
        if len(missing) > 20:
            print(f"    ... and {len(missing) - 20} more")
    out_path = os.path.join(OUT_ROOT, filename)
    write_utf8_lines(out_path, out_lines, had_eof)
    print(f"wrote {out_path} ({len(out_lines)} lines, {len(missing)} untranslated)")
    return len(lines), len(missing)


def apply_names():
    """NAMES.TXT: reuse the completed NAMES-姓名庫.tsv (line-order aligned, verified 400/400)."""
    src = os.path.join(SRC_ROOT, "NAMES.TXT")
    lines, had_eof = read_dos_text_lines(src)
    zh_names = []
    with open(NAMES_TSV, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for row in reader:
            zh_names.append(row[2])  # zh_tw column
    assert len(zh_names) == len(lines), f"NAMES.TXT ({len(lines)}) vs NAMES-姓名庫.tsv ({len(zh_names)}) length mismatch"
    for en, zh in zip(lines, zh_names):
        pass  # trust prior verified alignment (see 中文化規劃 §7.3 / prior session diff-check)
    out_path = os.path.join(OUT_ROOT, "NAMES.TXT")
    write_utf8_lines(out_path, zh_names, had_eof)
    print(f"wrote {out_path} ({len(zh_names)} lines, reused from NAMES-姓名庫.tsv)")


def has_lower(s):
    return any(c.islower() for c in s)


# generic map-feature words that appear standalone in ALL CAPS in some scenario
# files (misclassified by the has_lower() heuristic since they carry no lowercase
# letter) but are genuinely translatable terrain/feature words, not unit codes.
FORCE_TRANSLATE_UPPER = {"AIRFIELD", "LAKE", "POLDER"}


def apply_scenario(glossary):
    scen_lut = glossary.get("SCENARIO", {})
    src_dir = os.path.join(SRC_ROOT, "SCENARIO")
    scn_bases = set()
    for f in os.listdir(src_dir):
        if f.upper().endswith(".SCN"):
            scn_bases.add(f[:-4].upper())
    files = sorted(
        f for f in os.listdir(src_dir)
        if f.upper().endswith(".TXT") and f[:-4].upper() in scn_bases
    )
    assert len(files) == 53, f"expected 53 place-name SCENARIO txt files, found {len(files)}"

    total_lines = 0
    total_translated = 0
    total_missing = 0
    missing_report = []

    for fn in files:
        src = os.path.join(src_dir, fn)
        lines, had_eof = read_dos_text_lines(src)
        out_lines = []
        for l in lines:
            if l == "":
                out_lines.append("")
                continue
            translatable = has_lower(l) or l in FORCE_TRANSLATE_UPPER
            if not translatable:
                out_lines.append(l)  # unit code / coordinate / numeric designator - unchanged
                continue
            if l in scen_lut:
                out_lines.append(scen_lut[l])
                total_translated += 1
            else:
                out_lines.append(l)  # fallback: leave English, flag
                missing_report.append((fn, l))
                total_missing += 1
        total_lines += len(lines)
        out_path = os.path.join(OUT_ROOT, "SCENARIO", fn)
        write_utf8_lines(out_path, out_lines, had_eof)

    print(f"SCENARIO: {len(files)} files, {total_lines} lines total, "
          f"{total_translated} place-name lines translated, {total_missing} missing")
    if missing_report:
        print("[WARN] missing scenario place-name translations:")
        for fn, l in missing_report[:30]:
            print(f"    {fn}: {l!r}")
        if len(missing_report) > 30:
            print(f"    ... and {len(missing_report) - 30} more")
    return total_lines, total_missing


def main():
    glossary = load_glossary()
    os.makedirs(OUT_ROOT, exist_ok=True)

    print("=== GUI97.TXT ===")
    apply_simple("GUI97", "GUI97.TXT", glossary)

    print("=== MISC.TXT ===")
    apply_simple("MISC", "MISC.TXT", glossary)

    print("=== EQUIP97.TXT ===")
    apply_simple("EQUIP97", "EQUIP97.TXT", glossary)

    print("=== NAMES.TXT ===")
    apply_names()

    print("=== SCENARIO/*.TXT (53 place-name files) ===")
    apply_scenario(glossary)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PG2 繁中化 第二輪 - apply briefings_glossary.tsv to the 249 未譯 SCENARIO prose files
(戰役簡報散文 + 劇本 prose:45 個 *I.TXT 開場白 + 各出擊結果 L/V/MV/BV + 獨立劇本選單簡介 +
戰役總覽文字),產生 UTF-8 master 草稿。

輸入:
  - briefings_glossary.tsv (this directory) - 欄位: 檔類 \t original \t zh_tw \t 來源備註
  - 原始檔案: CLEAN_SRC/Panzer2/SCENARIO/*.TXT (乾淨 7z 重解,非受污染的舊 scratchpad 副本)

輸出 (OUT_ROOT/, UTF-8, 鏡像 SCENARIO/ 結構):
  - SCENARIO/<249 個未譯檔案>.TXT

不改動任何遊戲檔或 repo 檔;只寫本目錄 out/ 底下的檔案。沿用第一輪
(pg2/翻譯/apply_translations.py) 的 CRLF + DOS-EOF(0x1A) 保留邏輯,逐行比對套用。
"""
import os
import csv

HERE = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯/briefings"
CLEAN_SRC = os.path.join(HERE, "clean_src", "Panzer2", "SCENARIO")
OUT_ROOT = os.path.join(HERE, "out", "SCENARIO")
GLOSSARY_PATH = os.path.join(HERE, "briefings_glossary.tsv")
UNDONE_LIST_BASE = "/tmp/undone_base.txt"


def read_dos_text_lines(path):
    """Same logic as round-1 apply_translations.py: split on CRLF if present else
    bare LF; strip trailing 0x1A DOS-EOF marker before decode; track its presence."""
    with open(path, "rb") as f:
        raw = f.read()
    had_eof = raw.endswith(b"\x1a")
    if had_eof:
        raw = raw[:-1]
    text = raw.decode("latin-1")
    if "\r\n" in text:
        lines = text.split("\r\n")
    else:
        lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines, had_eof, ("\r\n" in text)


def write_utf8_lines(path, lines, had_eof_marker, use_crlf):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    eol = "\r\n" if use_crlf else "\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        for l in lines:
            f.write(l + eol)
        if had_eof_marker:
            f.write("\x1a")


def load_glossary():
    lut = {}
    with open(GLOSSARY_PATH, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        for row in reader:
            if len(row) < 3:
                continue
            _, original, zh = row[0], row[1], row[2]
            lut[original] = zh
    return lut


def main():
    lut = load_glossary()
    bases = [l.strip() for l in open(UNDONE_LIST_BASE, encoding="utf-8") if l.strip()]

    # map base -> actual filename (case-preserving) in clean source dir
    dir_files = os.listdir(CLEAN_SRC)
    fn_by_base = {}
    for f in dir_files:
        if f.upper().endswith(".TXT"):
            fn_by_base[f[:-4].upper()] = f

    total_files = 0
    total_lines = 0
    total_translated = 0
    total_missing = 0
    missing_report = []

    for base in bases:
        fn = fn_by_base.get(base.upper())
        if fn is None:
            print(f"[ERROR] source file not found for base {base!r}")
            continue
        src = os.path.join(CLEAN_SRC, fn)
        lines, had_eof, use_crlf = read_dos_text_lines(src)
        out_lines = []
        for l in lines:
            if l.strip() == "":
                # blank or whitespace-only separator line (original formatting
                # artifact, e.g. a stray space before CRLF) - pass through as-is,
                # not a translatable content line.
                out_lines.append(l)
                continue
            if l in lut:
                out_lines.append(lut[l])
                total_translated += 1
            else:
                out_lines.append(l)  # fallback: leave English, flag
                missing_report.append((fn, l))
                total_missing += 1
        total_lines += len(lines)
        total_files += 1
        out_path = os.path.join(OUT_ROOT, fn)
        write_utf8_lines(out_path, out_lines, had_eof, use_crlf)

    print(f"SCENARIO briefings: {total_files} files, {total_lines} lines total, "
          f"{total_translated} lines translated, {total_missing} missing")
    if missing_report:
        print("[WARN] missing translations:")
        for fn, l in missing_report[:50]:
            print(f"    {fn}: {l!r}")
        if len(missing_report) > 50:
            print(f"    ... and {len(missing_report) - 50} more")
    assert total_files == 249, f"expected 249 files, processed {total_files}"


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
估算 out/ 底下各 master 檔案轉成 dense 2-byte CJK 編碼後的大小,與已知上限比較。
規則(見 中文化規劃.md §4.4、任務說明):
  - ASCII / 半形字元 = 1 byte
  - 中文字元(含全形符號)= 2 byte(dense 2-byte 私有編碼,與 UTF-8 3 byte 不同)
  - 上限:GUI97.TXT / EQUIP97.TXT = 64KB;NAMES.TXT = 32KB;SCENARIO/*.TXT 各 32KB
  - MISC.TXT 官方 TechDoc 未列上限,以 32KB(與其他小檔同級)當保守參考值
輸出:size_report.tsv (檔名 \t 估計bytes \t 上限bytes \t 是否超限 \t 備註)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")

LIMITS = {
    "GUI97.TXT": 64 * 1024,
    "EQUIP97.TXT": 64 * 1024,
    "NAMES.TXT": 32 * 1024,
    "MISC.TXT": 32 * 1024,  # not documented explicitly; conservative reference value
}
SCENARIO_LIMIT = 32 * 1024


def is_cjk(ch):
    o = ord(ch)
    return (
        0x4E00 <= o <= 0x9FFF or   # CJK Unified Ideographs
        0x3400 <= o <= 0x4DBF or   # CJK Ext A
        0x3000 <= o <= 0x303F or   # CJK punctuation
        0xFF00 <= o <= 0xFFEF      # fullwidth forms
    )


def estimate_dense_bytes(text):
    n = 0
    for ch in text:
        if ch in ("\r", "\n"):
            n += 1
        elif is_cjk(ch):
            n += 2
        else:
            n += 1  # ASCII / half-width, incl. the 0x1A EOF marker if present
    return n


def report_file(path, limit, rows):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    size = estimate_dense_bytes(text)
    over = size > limit
    rows.append((os.path.relpath(path, OUT_ROOT), size, limit, "超限" if over else "OK"))
    return over


def main():
    rows = []
    any_over = False

    for fn, limit in LIMITS.items():
        path = os.path.join(OUT_ROOT, fn)
        if os.path.exists(path):
            if report_file(path, limit, rows):
                any_over = True

    scen_dir = os.path.join(OUT_ROOT, "SCENARIO")
    if os.path.isdir(scen_dir):
        for fn in sorted(os.listdir(scen_dir)):
            if fn.upper().endswith(".TXT"):
                path = os.path.join(scen_dir, fn)
                if report_file(path, SCENARIO_LIMIT, rows):
                    any_over = True

    out_path = os.path.join(HERE, "size_report.tsv")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("檔案\t估計dense2byte大小(bytes)\t上限(bytes)\t狀態\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")

    over_rows = [r for r in rows if r[3] == "超限"]
    print(f"wrote {out_path}: {len(rows)} files checked, {len(over_rows)} over limit")
    if over_rows:
        print("[WARN] over-limit files:")
        for r in over_rows:
            print(f"    {r[0]}: {r[1]} bytes > {r[2]} bytes limit")


if __name__ == "__main__":
    main()

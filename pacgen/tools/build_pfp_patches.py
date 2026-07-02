#!/usr/bin/env python3
"""從 txt_pfp_en/ 與 txt_pfp_zh/ 對照,產出可套用的 byte-length-preserving patch 表。

策略:
1. 用 pfp_split.py 拆的 en/ 與 glossary-applied 的 zh/ 每行對照
2. 一行對一行:若 zh 已翻譯 (與 en 不同) 且 Big5 編碼 <= en byte 長度 → 加 patch
3. patch 位置 = TXT.PFP 中該節區的絕對 offset + 節內行 offset
4. Big5 不足 en byte 長度時 pad 空格
5. zh 超長就 skip (v0.4 保留原文,v0.5 可能改截斷或縮字)

輸出:pfp_patches.json (offset, orig_len, zh) 列表,給 patch_pfp_inplace.py v2 讀取

用法:
    python3 build_pfp_patches.py <TXT.PFP> <en_dir> <zh_dir> [--out pfp_patches.json]
"""
import sys, json, pathlib, re, csv

def load_section_offsets(pfp_path):
    """回傳 { section_idx: (title, absolute_start_offset) }"""
    data = open(pfp_path, 'rb').read()
    starts = [m.start() for m in re.finditer(rb'#\r\n#\t', data)]
    sections = {}
    for i, s in enumerate(starts):
        parts = data[s:].split(b'\r\n', 2)
        if len(parts) < 3:
            continue
        title = parts[1][2:].decode('latin1', 'replace')
        header_len = len(parts[0]) + 2 + len(parts[1]) + 2
        content_offset = s + header_len
        sections[i] = (title, s, content_offset)
    return sections, data

def parse_section_lines(content_bytes):
    """把節內容切成 [(byte_offset_within_content, line_bytes)] — 排除 # 註解與空行"""
    result = []
    off = 0
    for line in content_bytes.split(b'\r\n'):
        # 不切掉 line,只記錄 offset
        result.append((off, line))
        off += len(line) + 2  # + \r\n
    return result

def build_patches(pfp_path, en_dir, zh_dir):
    sections, pfp_data = load_section_offsets(pfp_path)
    en_dir = pathlib.Path(en_dir)
    zh_dir = pathlib.Path(zh_dir)

    patches = []  # each: dict(section_idx, section_title, section_offset, line_offset, abs_offset, en, zh, orig_len, zh_bytes_len, pad)
    stats = {'total_lines':0, 'en_zh_diff':0, 'fits':0, 'toolong':0, 'unchanged':0}

    for idx in sorted(sections.keys()):
        title, sec_start, content_off = sections[idx]
        # 找對應 en/zh 檔
        en_files = list(en_dir.glob(f'{idx:02d}_*.txt'))
        zh_files = list(zh_dir.glob(f'{idx:02d}_*.txt'))
        if not en_files or not zh_files:
            continue
        en_lines_raw = en_files[0].read_bytes().split(b'\r\n')
        zh_lines_raw = zh_files[0].read_bytes().split(b'\r\n')
        if len(en_lines_raw) != len(zh_lines_raw):
            continue  # 保守: 行數不對就跳過整節
        line_off = 0
        for en_ln, zh_ln in zip(en_lines_raw, zh_lines_raw):
            stats['total_lines'] += 1
            abs_off = content_off + line_off
            en_str = en_ln.decode('latin1', 'replace')
            # 跳過空行 / 註解
            if not en_ln.strip() or en_ln.startswith(b'#'):
                line_off += len(en_ln) + 2
                continue
            # 若 zh 一樣或未翻譯就跳過
            if en_ln == zh_ln:
                stats['unchanged'] += 1
                line_off += len(en_ln) + 2
                continue
            stats['en_zh_diff'] += 1
            zh_bytes = zh_ln  # zh_ln 已經是 big5 bytes (from apply_glossary.py)
            if len(zh_bytes) <= len(en_ln):
                # 適配:pad 空格到原長度
                pad = len(en_ln) - len(zh_bytes)
                patches.append({
                    'idx': idx,
                    'title': title,
                    'abs_offset': abs_off,
                    'orig_len': len(en_ln),
                    'en': en_str.strip(),
                    'zh': zh_bytes.decode('big5', errors='replace').strip(),
                    'zh_bytes_hex': zh_bytes.hex(),
                    'pad_spaces': pad,
                })
                stats['fits'] += 1
            else:
                stats['toolong'] += 1
            line_off += len(en_ln) + 2
    return patches, stats

def main():
    pfp_path = sys.argv[1]
    en_dir = sys.argv[2]
    zh_dir = sys.argv[3]
    out = sys.argv[4] if len(sys.argv) > 4 else 'pfp_patches.json'
    patches, stats = build_patches(pfp_path, en_dir, zh_dir)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'stats': stats, 'patches': patches}, f, ensure_ascii=False, indent=2)
    print(f"[build] total lines: {stats['total_lines']}")
    print(f"[build] en==zh (untranslated): {stats['unchanged']}")
    print(f"[build] en!=zh (translated): {stats['en_zh_diff']}")
    print(f"[build]   fits (patch generated): {stats['fits']}")
    print(f"[build]   too long (skip): {stats['toolong']}")
    print(f"[build] → {out}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""把 glossary 套用到 en 目錄的每個 .txt,產出 zh 版本。

策略:
1. 讀 glossary.tsv → { english_phrase: chinese } (case-sensitive optional)
2. 對每個 en/*.txt,line-by-line:
   - 若整行 == glossary key → 用中譯取代
   - 若整行是 glossary key 的組合(空格分隔且全部命中) → 組成中譯
   - 否則保留原文(v0.1 hybrid,留給後續 session 手工細化)
3. 額外做 substring 替換 (可選,只在某些節區安全) — 目前不做,避免誤傷型號代碼
"""
import sys, re, pathlib

def load_glossary(path):
    gloss = {}
    for line in open(path, encoding='utf-8'):
        if line.startswith('english\t') or not line.strip():
            continue
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 2:
            continue
        en, zh = parts[0], parts[1]
        if en and zh:
            gloss[en] = zh
    return gloss

def translate_line(line_bytes, gloss):
    """line_bytes 是 latin1(以 CRLF 結尾的一行,不含 \r\n)。回傳 bytes(可能是 big5 encoded 中文)。"""
    line = line_bytes.decode('latin1', 'replace')
    # 純空行 / 註解行 / 空白保留
    if not line.strip() or line.startswith('#'):
        return line_bytes
    key = line.strip()
    # 整行命中
    if key in gloss:
        translated = gloss[key]
        # 保留 leading/trailing 空白
        lead = line[:len(line) - len(line.lstrip())]
        trail = line[len(line.rstrip()):]
        return (lead + translated + trail).encode('big5', errors='replace')
    # 幾個字組合命中(全部詞都是 glossary key,如 "Anti-tank Gun")
    words = key.split()
    if all(w in gloss for w in words) and len(words) >= 2:
        translated = ''.join(gloss[w] for w in words)
        lead = line[:len(line) - len(line.lstrip())]
        trail = line[len(line.rstrip()):]
        return (lead + translated + trail).encode('big5', errors='replace')
    return line_bytes

def translate_file(src_path, dst_path, gloss):
    data = src_path.read_bytes()
    # 保持行結構,line-by-line 處理
    out = bytearray()
    lines = data.split(b'\r\n')
    for i, ln in enumerate(lines):
        out += translate_line(ln, gloss)
        if i < len(lines) - 1:
            out += b'\r\n'
    dst_path.write_bytes(bytes(out))
    return len(lines)

def main():
    endir, zhdir, glossp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
    zhdir.mkdir(parents=True, exist_ok=True)
    gloss = load_glossary(glossp)
    print(f"[apply-gloss] {len(gloss)} entries loaded", file=sys.stderr)
    total_lines = 0
    total_files = 0
    for f in sorted(endir.iterdir()):
        if f.suffix != '.txt' and f.name != '_manifest.tsv':
            continue
        if f.name == '_manifest.tsv':
            # 直接 copy
            (zhdir / f.name).write_text(f.read_text(encoding='utf-8'), encoding='utf-8')
            continue
        n = translate_file(f, zhdir / f.name, gloss)
        total_lines += n
        total_files += 1
    print(f"[apply-gloss] processed {total_files} files / {total_lines} lines", file=sys.stderr)

if __name__ == "__main__":
    main()

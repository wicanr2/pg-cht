#!/usr/bin/env python3
"""將 TXT.PFP 拆成 74 個 section .txt 檔,便於翻譯。
用 `#\r\n#\t標題\r\n#\r\n` 當節區起點 marker。"""
import re, sys, os, pathlib

def split_pfp(data):
    """回傳 [(section_title, content_bytes), ...]

    Header 只讀 2 行:  #\r\n#\t<title>\r\n
    Content 保留剩下全部(可能含 #note: 或 #\r\n 等 metadata),不做假設。"""
    starts = [m.start() for m in re.finditer(rb'#\r\n#\t', data)]
    starts.append(len(data))
    sections = []
    for i in range(len(starts) - 1):
        blk = data[starts[i]:starts[i+1]]
        # split 2 lines 得 header,rest 全當 content
        parts = blk.split(b'\r\n', 2)
        if len(parts) < 3:
            continue
        title = parts[1][2:].decode('latin1', 'replace')  # remove #\t prefix
        content = parts[2]
        sections.append((title, content))
    return sections

def sanitize_filename(title, idx):
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', title)[:40].strip('_')
    return f"{idx:02d}_{slug}.txt"

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
    data = open(src, 'rb').read()
    sections = split_pfp(data)
    manifest = []
    for i, (title, content) in enumerate(sections):
        fn = sanitize_filename(title, i)
        (pathlib.Path(outdir) / fn).write_bytes(content)
        lines_ct = content.count(b'\r\n') + (1 if content and not content.endswith(b'\r\n') else 0)
        manifest.append(f"{i:02d}\t{fn}\t{lines_ct}\t{title}")
    (pathlib.Path(outdir) / '_manifest.tsv').write_text(
        "idx\tfilename\tlines\ttitle\n" + '\n'.join(manifest) + '\n', encoding='utf-8')
    print(f"[pfp-split] {len(sections)} sections -> {outdir}", file=sys.stderr)

if __name__ == "__main__":
    main()

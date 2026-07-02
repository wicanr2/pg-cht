#!/usr/bin/env python3
"""將翻譯過的 section .txt 檔重組回 TXT.PFP 格式 (Big5 encoding)。
讀 _manifest.tsv 決定順序,每個 section 前加 `#\r\n#\t<title>\r\n#\r\n`。"""
import sys, pathlib

def main():
    indir, out_path, encoding = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'big5'
    indir = pathlib.Path(indir)
    manifest = (indir / '_manifest.tsv').read_text(encoding='utf-8').strip().split('\n')[1:]
    out = bytearray()
    for line in manifest:
        idx, fn, lines_ct, title = line.split('\t', 3)
        # 只用 2 行 header (#\r\n + #\t<title>\r\n),content 自帶剩下 metadata
        header = f"#\r\n#\t{title}\r\n".encode(encoding, errors='replace')
        content = (indir / fn).read_bytes()
        out += header + content
    open(out_path, 'wb').write(out)
    print(f"[pfp-pack] wrote {len(out)} bytes to {out_path} (enc={encoding})", file=sys.stderr)

if __name__ == "__main__":
    main()

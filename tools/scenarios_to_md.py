#!/usr/bin/env python3
"""三作劇本 TSV → 按 era/region 分節 Markdown。"""
import csv, sys, pathlib, collections

def load_tsv(path, key='scen'):
    return list(csv.DictReader(open(path, encoding='utf-8'), delimiter='\t'))

def render(games, out_dir):
    for game_key, meta, era_order in games:
        rows = meta['rows']
        title = meta['title']
        intro = meta['intro']
        era_key = meta.get('era_key', 'era')
        out = [f'# {title}\n', intro + '\n']
        # TOC
        out.append('## 目錄\n')
        for era in era_order:
            e_rows = [r for r in rows if r.get(era_key, '').strip() == era]
            if not e_rows: continue
            anchor = era.replace(' ', '-')
            out.append(f'- [{era}](#{anchor}) — {len(e_rows)} 個劇本')
        out.append('')
        # 章節
        for era in era_order:
            e_rows = [r for r in rows if r.get(era_key, '').strip() == era]
            if not e_rows: continue
            out.append(f'\n## {era}\n')
            for r in e_rows:
                year = r.get('year', '').strip()
                zh_name = r.get('zh_name', r.get('scen', '')).strip()
                scen = r.get('scen', '').strip()
                brief = r.get('brief_zh', '').strip()
                out.append(f'### {zh_name}  \n')
                meta_line = []
                if year: meta_line.append(f'*{year}*')
                meta_line.append(f'`{scen}`')
                out.append('  '.join(meta_line) + '\n')
                out.append(brief + '\n')
        (pathlib.Path(out_dir) / f'{game_key}.md').write_text('\n'.join(out), encoding='utf-8')
        print(f'wrote {game_key}.md')

if __name__ == '__main__':
    d = pathlib.Path(sys.argv[1])  # docs/scenarios/
    pg = load_tsv(d / 'pg-scenarios.tsv')
    ag = load_tsv(d / 'ag-scenarios.tsv')
    pacgen = load_tsv(d / 'pacgen-scenarios.tsv')

    games = [
        ('pg', {
            'title': '裝甲元帥 (Panzer General) — 38 個劇本',
            'intro': ('SSI 1994 出品的 5D General 系列首作,德軍視角橫跨 1939-46 年歐洲戰場。'
                      '38 個劇本按時序與戰場拆成三大階段,加上兩個架空延伸情境。'
                      '**譯名**:採台灣軍事史學界慣用譯,避免大陸簡譯。**歷史根據**:公共領域二戰史實。'),
            'rows': pg,
        }, ['開戰', '東線', '西線', '架空']),
        ('ag', {
            'title': '盟軍將軍 (Allied General) — 39 個劇本',
            'intro': ('SSI 1995 出品的 5D 系列續作,以盟軍/蘇軍雙視角橫跨 1940-45 年。'
                      '39 個劇本按戰場地理拆成四大戰區,含兩個架空延伸情境。'
                      '**譯名規範**同 PG,強調台灣軍事史學界慣用譯法。'),
            'rows': ag,
        }, ['北非', '南歐', '西歐', '東線']),
        ('pacgen', {
            'title': '太平洋元帥 (Pacific General) — 33 個劇本',
            'intro': ('SSI/Mindscape 1997 出品的 5D 系列末代,聚焦 1936-46 年太平洋戰場。'
                      '33 個劇本涵蓋南方作戰(日軍南進)、反攻(盟軍蛙跳)、教學與架空四大類。'
                      '**譯名**:海戰艦名採中文戰史慣用譯(企業號、翔鶴、飛龍);飛機型號保留原文(F4F、A6M、B-29);'
                      '兵種類別中譯(戰列艦、驅逐艦、航空母艦)。'),
            'rows': pacgen,
        }, ['開戰', '南方作戰', '反攻', '教學', '架空']),
    ]
    render(games, d)

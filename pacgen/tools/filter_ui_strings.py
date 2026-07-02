#!/usr/bin/env python3
"""從 dump 過的 string TSV 過濾出「可能是 UI 字串」的候選。
排除 CRT runtime/檔名/路徑 slug,留可翻譯 UI/menu/msg 用字串。"""
import sys, re

CRT_HINT = re.compile(
    r'\.(c|cpp|h|dll|exe|smk|shp|tdb|scn|bnk|mel|mus|tit|des|txt|bmp|pcx|prf|bin|dat|inf|ini|idx|ico|pfp|res|obj|lib)$'
    r'|^_[a-zA-Z_]+$'
    r'|^[A-Z_]{2,}\s*==\s*'
    r'|^_?[Cc]rt[A-Z]'
    r'|_pFirst|_pLast|_pHead|_BLOCK_'
    r'|IGNORE_LINE|IGNORE_REQ|nBlockUse|lRequest'
    r'|^[a-z_]+\.c\b'
    r'|!=\s*NULL|==\s*NULL'                  # C 判空 assert
    r'|_T\(|\bNULL\b|\bassert(ion)?\b'
    r'|\bruntime error\b|\bAssertion\b|\bMicrosoft Visual C\+\+\b'
    r'|IOB|stream->_|_ptr|_base|nLine|nBlockUse|lRequest|pOldBlock|pNewBlock'
    r'|\b(sizeof|malloc|free|realloc|calloc|fclose|fopen|fread|fwrite)\b'
    r'|szUser|command\.com|_pipe|_purecall|_flushall'
    r'|BLOCK_TYPE|HEAP_|HeapAlloc|HeapFree'
    r'|Expression:|Program:'
    r'|\bDAMAGED\b|\bIgnore\b|\bNormal\b'
)

FILEPATHS = re.compile(r'^([a-zA-Z]:|\.{1,2}[/\\]|[a-z_]+[/\\])')

# 允許的 UI 特徵:含空白+字母 / 標點 / 疑問句 / 短動詞 / % 格式
def score_ui(text):
    s = text.strip()
    if len(s) < 3: return 0
    if CRT_HINT.search(s): return 0
    if FILEPATHS.match(s): return 0
    # 全大寫 + 底線 = enum / assert
    if re.match(r'^[A-Z_]{3,}$', s): return 0
    # 只含 hex / 數字 / punct
    if re.match(r'^[0-9a-fA-F\-\.\s]+$', s): return 0
    # 只是型別/函式名(無空白且駝峰)
    if not re.search(r'\s', s) and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{4,}$', s):
        # 排除 UI 慣用短詞(OK, Cancel, New, Load...) — 但這些通常單詞很短
        return 0
    score = 1
    if re.search(r'[a-z][A-Z]', s): score -= 1  # camelCase 減
    if ' ' in s: score += 2                     # 有空白 → 句子
    if re.search(r'[.!?]$', s): score += 1
    if '%' in s: score += 1                     # printf 格式
    if len(s) > 12: score += 1
    return max(0, score)

# UI 短詞白名單(常見按鈕/選單)
UI_SHORT_WHITELIST = {
    'OK','Cancel','Yes','No','New','Load','Save','Exit','Quit','Back','Next','Done',
    'Play','Start','Pause','Stop','Continue','Options','Help','About','Info',
    'File','Edit','View','Game','Menu','Tools','Window','Print','Open','Close',
    'Purchase','Refit','Upgrade','Retreat','Move','Attack','Defend','Skip',
    'Axis','Allied','Japan','America','USSR','Britain','China',
    'Turn','Prestige','Score','Victory','Defeat','Draw','Loss','Win',
    'Scenario','Campaign','Briefing','Debriefing','Report','Dossier',
    'Fine','Clear','Rain','Snow','Storm','Fog','Winter','Summer',
    'Land','Air','Sea','Naval','Ground','Fighter','Bomber','Infantry',
    'North','South','East','West',
    'Small','Medium','Large','None','All','Any',
}

def main():
    inpath, outpath = sys.argv[1], sys.argv[2]
    total = 0
    kept = 0
    with open(inpath, encoding='utf-8') as f, open(outpath, 'w', encoding='utf-8') as o:
        hdr = f.readline()
        o.write(hdr)
        for line in f:
            total += 1
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 6: continue
            fo, va, sec, xref, ln, text = parts[:6]
            try:
                x = int(xref); L = int(ln)
            except:
                continue
            if sec not in ('.rdata', '.data'): continue
            if x < 1: continue
            # 白名單短詞
            if text.strip() in UI_SHORT_WHITELIST:
                o.write(line); kept += 1; continue
            # 一般過濾
            s = score_ui(text)
            if s >= 1:
                o.write(line); kept += 1
    print(f"[filter] {kept}/{total} kept", file=sys.stderr)

if __name__ == "__main__":
    main()

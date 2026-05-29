# -*- coding: utf-8 -*-
# 共用對話按鈕 OK->確定 / CANCEL->取消 (見 SKILL §6c)
# 密度法去字:保留金邊/內框/漸層;微軟正黑體粗體;來源取自 ART.DAT.bak。
# 用法:python example_dialog_buttons.py [--commit]
import importlib.util, sys, os
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
_here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location("artlib",os.path.join(_here,"artlib.py"))
A=importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
ART=r"D:\03_game_tmp\AlliedGeneralLite_v1.1\AlliedGeneral_v1.1\ART\ART.DAT"
FB=r"C:\Windows\Fonts\msjhbd.ttc"   # 微軟正黑體粗體:小字清晰且本身粗體(勿用 kaiu+stroke,小字會糊成黑團)
COMMIT="--commit" in sys.argv
SIZE=13; INSET=8
cancel=["cNQn","cNbp","agJ1","agJ2","adf1","adf2","aLQn","aLbp","gEQn","gEbp","rUQn","rUbp"]
ok=["dUfn","daip","gLcn","gLtp","g`Sn","g`dp","g]Xn","g]ip","okdn","okup","r_Vn","r`Sn","r`dp","r]Xn","r]ip"]
jobs=[(c,"取消") for c in cancel]+[(c,"確定") for c in ok]

def do(d,en,dbak,ebak,code,zh):
    e=A.find(en,code.encode("latin1"),b"RLEi")
    eb=A.find(ebak,code.encode("latin1"),b"RLEi"); W,H,pn,rows=A.decode_rle_v2(dbak,eb)  # 原圖取自 .bak
    pal=A.parse_pal(dbak,A.find(ebak,pn,b"CPal")); lum=[(0.3*r+0.59*g+0.11*b) for (r,g,b) in pal]
    bg=Counter(rows[y][x] for y in range(4,H-4) for x in range(INSET,W-INSET)).most_common(1)[0][0]; bgl=lum[bg]
    iw=(W-INSET)-INSET
    def far(v): return abs(lum[v]-bgl)>thr
    def dens(y): return sum(1 for x in range(INSET,W-INSET) if far(rows[y][x]))/iw
    def trows(): return [y for y in range(3,H-3) if 0.10<dens(y)<0.55]  # 文字列;>55%=邊框/內框橫線(保留),<10%=空白
    thr=50; tr=trows()
    if len(tr)<2: thr=24; tr=trows()           # 低對比灰底鈕降門檻重試
    if not tr: print("  no text",code); return None
    ty0,ty1=min(tr),max(tr)+1
    rowbg={}
    for y in tr:
        base=Counter(rows[y][x] for x in range(INSET,W-INSET) if not far(rows[y][x]))
        rowbg[y]=base.most_common(1)[0][0] if base else bg
    txc=Counter(rows[y][x] for y in tr for x in range(INSET,W-INSET) if far(rows[y][x])).most_common(1)[0][0]  # 原文字色
    for y in tr:                                # 去字:只清文字列、x∈[INSET,W-INSET] 的文字筆畫,回填該列底色
        for x in range(INSET,W-INSET):
            if far(rows[y][x]): rows[y][x]=rowbg[y]
    im=Image.new("L",(W,H),0); dr=ImageDraw.Draw(im); f=ImageFont.truetype(FB,SIZE)
    bb=dr.textbbox((0,0),zh,font=f); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
    dr.text((W//2-tw//2-bb[0],(ty0+ty1)//2-th//2-bb[1]),zh,fill=255,font=f); pm=im.load()
    for y in range(H):
        for x in range(W):
            if pm[x,y]>128: rows[y][x]=txc
    if COMMIT:
        ok2,nl,sp=A.patch_inplace_v2(d,e,rows,W); assert ok2,(code,nl,sp)
    img=Image.new("RGB",(W,H)); img.putdata([pal[v&0xFF] for r in rows for v in r]); return img

d,en=A.load(ART); dbak,ebak=A.load(ART+".bak")
previews=[]
for code,zh in jobs:
    img=do(d,en,dbak,ebak,code,zh)
    if img: previews.append((code,zh,img))
if COMMIT: open(ART,"wb").write(d); print("COMMITTED")
else: print("PREVIEW only — 預覽圖 dialog_buttons_preview.png")
cellh=4*25+18
sheet=Image.new("RGB",(2*(4*95+10)+10,cellh*((len(previews)+1)//2)),(20,20,20)); dr=ImageDraw.Draw(sheet)
for i,(code,zh,im) in enumerate(previews):
    im2=im.resize((im.width*4,im.height*4),Image.NEAREST); cx=(i%2)*(4*95+10); cy=(i//2)*cellh
    sheet.paste(im2,(cx+4,cy+16)); dr.text((cx+4,cy+2),code+" "+zh,fill=(255,255,0))
sheet.save(os.path.join(_here,"dialog_buttons_preview.png"))

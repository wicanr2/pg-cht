# -*- coding: utf-8 -*-
import importlib.util, shutil, sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
spec=importlib.util.spec_from_file_location("artlib",r"C:\Users\原來是個胖仔\_artlib.py")
A=importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
ART=r"D:\03_game_tmp\AlliedGeneralLite_v1.1\AlliedGeneral_v1.1\ART\ART.DAT"
COMMIT="--commit" in sys.argv
shutil.copy2(ART+".bak",ART)
d,entries=A.load(ART)
e=A.find(entries,b"pYon",b"RLEi"); W,H,pn,rows=A.decode_rle_v2(d,e)
pal=A.parse_pal(d,A.find(entries,pn,b"CPal"))
lum=[(0.3*r+0.59*g+0.11*b) for (r,g,b) in pal]
FB=r"C:\Windows\Fonts\msjhbd.ttc"

def header(text,sx0,sx1,sy0,sy1,tx=180,fsz=12,yoff=0,cxover=None):
    # 1) plate x-extent: cols with bright gold (lum>150)
    cols=[x for x in range(sx0,sx1) if any(lum[rows[y][x]]>150 for y in range(sy0,sy1))]
    bx0,bx1=min(cols),max(cols)+1
    # 2) body rows: dominant color is mid (lum 120-200) i.e. 土黃 OR has dark text(lum<90); exclude highlight(>200)/shadow/green
    body=[]
    for y in range(sy0,sy1):
        cnt=Counter(rows[y][x] for x in range(bx0,bx1))
        dom,_=cnt.most_common(1)[0]; dl=lum[dom]
        hastext=any(lum[rows[y][x]]<90 for x in range(bx0,bx1))
        if 120<=dl<=200 and (hastext or dl<200): body.append(y)
    if not body: print("no body",text); return
    by0,by1=min(body),max(body)+1
    # 3) de-text: each body row -> fill dark pixels with that row's bg (mode of non-dark)
    for y in range(by0,by1):
        nd=[rows[y][x] for x in range(bx0,bx1) if lum[rows[y][x]]>=90]
        bg=Counter(nd).most_common(1)[0][0] if nd else 138
        for x in range(bx0,bx1):
            if lum[rows[y][x]]<90: rows[y][x]=bg
    # 4) stamp chinese centered in plate body, no vertical whitespace
    f=ImageFont.truetype(FB,fsz);im=Image.new("L",(W,H),0);dr=ImageDraw.Draw(im)
    tb=dr.textbbox((0,0),text,font=f);tw=tb[2]-tb[0];th=tb[3]-tb[1]
    cx=cxover if cxover is not None else (bx0+bx1)//2
    cy=(by0+by1)//2+yoff
    dr.text((cx-tw//2-tb[0],cy-th//2-tb[1]),text,fill=255,font=f);px=im.load()
    for y in range(H):
        for x in range(W):
            if px[x,y]>82: rows[y][x]=tx
    print("%s plate x%d-%d body y%d-%d fsz%d"%(text,bx0,bx1,by0,by1,fsz))

# title + 4 headers
header("偏好設定",110,260,4,28,tx=180,fsz=13,cxover=167)   # center in dialog
header("經驗",45,170,95,120,fsz=12,yoff=2); header("經驗",195,320,95,120,fsz=12,yoff=2)
header("聲望",45,170,200,232,fsz=12,yoff=2); header("聲望",195,320,200,232,fsz=12,yoff=2)

# green labels (flat green bg ok to flat-fill) + buttons — from fix6
def paint(text,box,bg,tx,size):
    x0,y0,x1,y1=box
    for y in range(y0,y1):
        for x in range(x0,x1):
            if 0<=y<H and 0<=x<W: rows[y][x]=bg
    f=ImageFont.truetype(FB,size);im=Image.new("L",(W,H),0);dr=ImageDraw.Draw(im)
    tb=dr.textbbox((0,0),text,font=f);tw=tb[2]-tb[0];th=tb[3]-tb[1]
    cx=(x0+x1)//2;cy=(y0+y1)//2
    dr.text((cx-tw//2-tb[0],cy-th//2-tb[1]),text,fill=255,font=f);px=im.load()
    for y in range(H):
        for x in range(W):
            if px[x,y]>82: rows[y][x]=tx
paint("補給",(80,349,120,365),38,138,11); paint("天氣",(80,367,128,383),38,138,11)
paint("顯示部隊強度",(162,349,272,365),38,138,11); paint("顯示隱藏單位",(162,367,266,383),38,138,11)
paint("顯示對手移動",(108,385,232,401),38,138,11)
paint("取消",(75,413,193,430),73,104,11); paint("確定",(227,413,296,430),73,104,11)

img=Image.new("RGB",(W,H));img.putdata([pal[v&0xFF] for r in rows for v in r])
img.resize((W*2,H*2),Image.NEAREST).save(r"C:\Users\原來是個胖仔\_art_png\pyon_fix8.png")
if COMMIT:
    ok,nl,sp=A.patch_inplace_v2(d,e,rows,W);assert ok;open(ART,"wb").write(d);print("COMMITTED")
else: print("PREVIEW")

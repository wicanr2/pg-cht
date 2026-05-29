# -*- coding: utf-8 -*-
import importlib.util, sys, binascii
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
spec=importlib.util.spec_from_file_location("artlib",r"C:\Users\原來是個胖仔\_artlib.py")
A=importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
ART=r"D:\03_game_tmp\AlliedGeneralLite_v1.1\AlliedGeneral_v1.1\ART\ART.DAT"
COMMIT="--commit" in sys.argv
FB=r"C:\Windows\Fonts\msjhbd.ttc"
d,entries=A.load(ART)

def process(codehex, preview_name):
    code=binascii.unhexlify(codehex)
    e=A.find(entries,code,b"RLEi"); W,H,pn,rows=A.decode_rle_v2(d,e)
    pal=A.parse_pal(d,A.find(entries,pn,b"CPal"))
    lum=[(0.3*r+0.59*g+0.11*b) for (r,g,b) in pal]
    def stamp(text,bx0,by0,bx1,by1,tx,fsz,left=False):
        f=ImageFont.truetype(FB,fsz);im=Image.new("L",(W,H),0);dr=ImageDraw.Draw(im)
        tb=dr.textbbox((0,0),text,font=f);tw=tb[2]-tb[0];th=tb[3]-tb[1]
        cx = bx0 - tb[0] if left else (bx0+bx1)//2-tw//2-tb[0]
        cy=(by0+by1)//2-th//2-tb[1]
        dr.text((cx,cy),text,fill=255,font=f);px=im.load()
        for y in range(H):
            for x in range(W):
                if px[x,y]>82: rows[y][x]=tx
    def detext_band(text,sx0,sx1,sy0,sy1,fsz,left=False):
        # gold/gray bars: text rows = rows w/ enough contrast pixels; fill whole text row w/ row-bg; stamp
        body=[];rowbg={}
        for y in range(sy0,sy1):
            bg=Counter(rows[y][x] for x in range(sx0,sx1)).most_common(1)[0][0]; rowbg[y]=bg
            if sum(1 for x in range(sx0,sx1) if abs(lum[rows[y][x]]-lum[bg])>25)>=4: body.append(y)
        if not body: print("  no body",text); return
        by0,by1=min(body),max(body)+1
        txp=Counter(rows[y][x] for y in body for x in range(sx0,sx1) if abs(lum[rows[y][x]]-lum[rowbg[y]])>25)
        txc=txp.most_common(1)[0][0] if txp else 104
        for y in body:
            bg=rowbg[y]
            for x in range(sx0,sx1): rows[y][x]=bg
        stamp(text,sx0,by0,sx1,by1,txc,fsz,left=left)
    def label(text,sx0,sy0,sx1,sy1,fsz,left=True):
        # auto-polarity: bg=mode; pick light-on-dark or dark-on-light by pixel count
        bg=Counter(rows[y][x] for y in range(sy0,sy1) for x in range(sx0,sx1)).most_common(1)[0][0]
        bgl=lum[bg]
        light=[];dark=[]
        for y in range(sy0,sy1):
            for x in range(sx0,sx1):
                dl=lum[rows[y][x]]-bgl
                if dl>45: light.append((x,y,rows[y][x]))
                elif dl<-45: dark.append((x,y,rows[y][x]))
        pts=light if len(light)>=len(dark) else dark
        if not pts: print("  miss",text); return
        xs=[p[0] for p in pts];ys=[p[1] for p in pts];txc=Counter(p[2] for p in pts).most_common(1)[0][0]
        b0,b1,b2,b3=min(xs),min(ys),max(xs)+1,max(ys)+1
        for y in range(b1-1,b3+1):
            for x in range(b0-1,b2+1):
                if 0<=y<H and 0<=x<W: rows[y][x]=bg
        stamp(text,b0,b1,b2,b3,txc,fsz,left=left)
    gold_bar=detext_band; green_label=lambda t,a,b,c,e2,f,left=True: label(t,a,b,c,e2,f,left=left)
    # --- labels (positions from grid, 231x298) ---
    gold_bar("設定",42,192,1,18,12)
    gold_bar("音量",55,180,25,46,12)
    green_label("靜音",85,132,150,153,11,left=False)
    green_label("記錄遊戲歷程",40,168,205,188,11)
    green_label("顯示六角格邊界",40,187,205,207,11)
    green_label("戰鬥動畫",40,206,205,226,11)
    green_label("隱藏桌面",40,224,205,244,11)
    img=Image.new("RGB",(W,H));img.putdata([pal[v&0xFF] for r in rows for v in r])
    img.resize((W*2,H*2),Image.NEAREST).save(preview_name)
    if COMMIT:
        ok,nl,sp=A.patch_inplace_v2(d,e,rows,W); assert ok,(nl,sp); print("  committed",code,nl,sp)
    else: print("  preview",code)

process("61626a64", r"C:\Users\原來是個胖仔\_art_png\settings_al.png")   # abjd Allied
process("675b6a64", r"C:\Users\原來是個胖仔\_art_png\settings_ge.png")  # g[jd German
process("726b6a64", r"C:\Users\原來是個胖仔\_art_png\settings_ru.png")  # rkjd Russian
if COMMIT:
    open(ART,"wb").write(d); print("written")
print("PREVIEW" if not COMMIT else "DONE")

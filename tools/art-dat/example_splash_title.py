# -*- coding: utf-8 -*-
# 在 SPLASH.DAT 的 ALLIED GENERAL 標誌下加鋼鐵漸層中文標題「盟軍元帥」(見 SKILL §12)
# 用法:python example_splash_title.py [--commit]
import importlib.util, struct, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
_here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location("artlib",os.path.join(_here,"artlib.py"))
A=importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
P=r"D:\03_game_tmp\AlliedGeneralLite_v1.1\AlliedGeneral_v1.1\ART\SPLASH.DAT"
FB=r"C:\Windows\Fonts\msjhbd.ttc"   # 微軟正黑體粗體
ZH="盟軍元帥"
d=bytearray(open(P,"rb").read())
e_rlei=[b"sjbh",b"RLEi",0x1a38,struct.unpack_from(">I",d,0x1a38+4)[0],0]
e_cpal=[bytes(d[0x1a38+12:0x1a38+16]),b"CPal",0x0e,struct.unpack_from(">I",d,0x0e+4)[0],0]
W,H,pn,rows=A.decode_rle_v2(d,e_rlei)
pal=A.parse_pal(d,e_cpal); lum=[(0.3*r+0.59*g+0.11*b) for (r,g,b) in pal]
S=set(i for i in range(256) if max(pal[i])>110 and (max(pal[i])-min(pal[i]))<55 and lum[i]>120)
pts=[(x,y) for y in range(158,258) for x in range(380,W) if rows[y][x] in S]
gx0=min(p[0] for p in pts); gx1=max(p[0] for p in pts); gy1=max(p[1] for p in pts)
def nearest(rgb):
    bi,bd=0,1e9
    for i in range(256):
        pr,pg,pb=pal[i]; dd=(pr-rgb[0])**2+(pg-rgb[1])**2+(pb-rgb[2])**2
        if dd<bd: bd,bi=dd,i
    return bi
def grad(t):
    st=[(0.0,(255,255,255)),(0.18,(232,232,236)),(0.42,(176,176,186)),(0.62,(150,150,160)),
        (0.74,(214,214,222)),(0.88,(120,120,130)),(1.0,(96,96,104))]
    for k in range(len(st)-1):
        t0,c0=st[k]; t1,c1=st[k+1]
        if t0<=t<=t1:
            f=(t-t0)/(t1-t0); return tuple(int(c0[j]+(c1[j]-c0[j])*f) for j in range(3))
    return st[-1][1]
tw_target=gx1-gx0; size=64
for s in range(96,30,-1):
    bb=ImageDraw.Draw(Image.new("L",(1,1))).textbbox((0,0),ZH,font=ImageFont.truetype(FB,s))
    if bb[2]-bb[0]<=tw_target: size=s; break
f=ImageFont.truetype(FB,size); mask=Image.new("L",(W,H),0); dr=ImageDraw.Draw(mask)
bb=dr.textbbox((0,0),ZH,font=f); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
dr.text(((gx0+gx1)//2-tw//2-bb[0], gy1+14-bb[1]),ZH,fill=255,font=f); mp=mask.load()
ys=[y for y in range(H) for x in range(W) if mp[x,y]>128]; ty0,ty1=min(ys),max(ys)
op=mask.filter(ImageFilter.MaxFilter(5)).load(); dark=nearest((20,20,24))
for y in range(H):
    for x in range(W):
        if op[x,y]>128 and mp[x,y]<=128: rows[y][x]=dark
for y in range(ty0,ty1+1):
    col=nearest(grad((y-ty0)/max(1,ty1-ty0)))
    for x in range(W):
        if mp[x,y]>128: rows[y][x]=col
Image.new("RGB",(W,H),0).putdata  # noop
img=Image.new("RGB",(W,H)); img.putdata([pal[v&0xFF] for r in rows for v in r])
img.save(os.path.join(_here,"splash_title_preview.png"))
ok,nl,sp=A.patch_inplace_v2(d,e_rlei,rows,W); print("fit ok=%s stream=%d/%d"%(ok,nl,sp))
if "--commit" in sys.argv and ok:
    import shutil; shutil.copy2(P,P+".premZh"); open(P,"wb").write(d); print("COMMITTED")

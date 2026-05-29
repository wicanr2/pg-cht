# -*- coding: utf-8 -*-
"""Reusable ART.DAT bitmap label repainter for AG. Auto-detects English label bbox,
sizes the Chinese to match the original text height (so layout is preserved), repaints in palette space."""
import importlib.util
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
A_spec=importlib.util.spec_from_file_location("artlib",r"C:\Users\原來是個胖仔\_artlib.py")
A=importlib.util.module_from_spec(A_spec); A_spec.loader.exec_module(A)
FONT=r"C:\Windows\Fonts\mingliu.ttc"

class Screen:
    def __init__(self, artpath, name):
        self.art=artpath
        self.d,self.entries=A.load(artpath)
        self.e=A.find(self.entries,name,b"RLEi")
        self.W,self.H,self.pn,self.rows=A.decode_rle_v2(self.d,self.e)
        self.pal=A.parse_pal(self.d,A.find(self.entries,self.pn,b"CPal"))
        self.lum=[(0.3*r+0.59*g+0.11*b) for (r,g,b) in self.pal]
    def autobox(self,reg,lighter,thr=45):
        x0,y0,x1,y1=reg
        bg=Counter(self.rows[y][x] for y in range(y0,y1) for x in range(x0,x1)).most_common(1)[0][0]
        bgl=self.lum[bg]; pts=[]; tx=[]
        for y in range(y0,y1):
            for x in range(x0,x1):
                v=self.rows[y][x]; dl=self.lum[v]-bgl
                if (lighter and dl>thr) or ((not lighter) and dl<-thr): pts.append((x,y)); tx.append(v)
        if not pts: return None
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        return (min(xs),min(ys),max(xs)+1,max(ys)+1),bg,Counter(tx).most_common(1)[0][0]
    def paint(self,text,reg,lighter,dh=1,maxw_pad=2,thr=45,force_size=None,force_tx=None,force_bg=None,font=FONT,mask=110):
        r=self.autobox(reg,lighter,thr)
        if not r:
            print("  MISS:",text,reg); return False
        (b0,b1,b2,b3),bg,tx=r
        if force_tx is not None: tx=force_tx
        if force_bg is not None: bg=force_bg
        bw=b2-b0; bh=b3-b1
        # erase
        for y in range(b1-1,b3+1):
            for x in range(b0-1,b2+1):
                if 0<=y<self.H and 0<=x<self.W: self.rows[y][x]=bg
        # size font to match original text height (bh) -> preserves layout
        size=force_size if force_size else max(7,bh+dh)
        # shrink if too wide
        for s in range(size,5,-1):
            f=ImageFont.truetype(font,s); im=Image.new("L",(1,1)); dr=ImageDraw.Draw(im)
            bb=dr.textbbox((0,0),text,font=f); tw=bb[2]-bb[0]
            if tw<=bw+maxw_pad or s==6: size=s; break
        f=ImageFont.truetype(font,size)
        im=Image.new("L",(self.W,self.H),0); dr=ImageDraw.Draw(im)
        bb=dr.textbbox((0,0),text,font=f); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
        cx=(b0+b2)//2; cy=(b1+b3)//2
        dr.text((cx-tw//2-bb[0],cy-th//2-bb[1]),text,fill=255,font=f); px=im.load()
        for y in range(self.H):
            for x in range(self.W):
                if px[x,y]>mask: self.rows[y][x]=tx
        print("  '%s' bbox=(%d,%d,%d,%d) size=%d bg=%d tx=%d"%(text,b0,b1,b2,b3,size,bg,tx))
        return True
    def commit(self):
        ok,newlen,space=A.patch_inplace_v2(self.d,self.e,self.rows,self.W)
        if not ok:
            print("  *** DOES NOT FIT: %d > %d"%(newlen,space)); return False
        open(self.art,"wb").write(self.d)
        # verify
        d2,en2=A.load(self.art); e2=A.find(en2,self.e[0],b"RLEi")
        _,_,_,r2=A.decode_rle_v2(d2,e2)
        print("  committed %s, stream=%d/%d, verify=%s"%(self.e[0],newlen,space,r2==self.rows))
        return True
    def preview(self,path,scale=2):
        img=Image.new("RGB",(self.W,self.H)); img.putdata([self.pal[v&0xFF] for r in self.rows for v in r])
        img.resize((self.W*scale,self.H*scale),Image.NEAREST).save(path)

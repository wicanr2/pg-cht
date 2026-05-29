# -*- coding: utf-8 -*-
import importlib.util, struct
from PIL import Image
spec=importlib.util.spec_from_file_location("paintlib",r"C:\Users\原來是個胖仔\_paintlib.py")
P=importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
ART=r"D:\03_game_tmp\AlliedGeneralLite_v1.1\AlliedGeneral_v1.1\ART\ART.DAT"
FB=r"C:\Windows\Fonts\kaiu.ttf"   # 標楷體 DFKai-SB — 毛筆楷書，雍容華貴
COMMIT = ("--commit" in __import__("sys").argv)
MASK=128
# (code, chinese, region, size)  buttons 148x37 dark-on-cream ; header 139x18
JOBS=[
 (b"anSn","北非",(12,7,136,30),20),  (b"andp","北非",(12,7,136,30),20),
 (b"awWn","西歐",(12,7,136,30),20),  (b"awhp","西歐",(12,7,136,30),20),
 (b"argn","俄羅斯",(12,7,136,30),20),(b"arxp","俄羅斯",(12,7,136,30),20),
 (b"sR`c".replace(b"`",bytes([0x60])),"戰術選擇",(4,2,134,16),14),
]
previews=[]
for code,zh,reg,sz in JOBS:
    s=P.Screen(ART,code)
    is_btn = (code!=b"sRc"[:0]+bytes([0x73,0x52,0x60,0x63]))
    ftx = 69 if is_btn else None   # region buttons: force dark text (idx 69)
    fbg = 73 if is_btn else None   # region buttons: cream face
    s.paint(zh,reg,False,force_size=sz,font=FB,mask=MASK,thr=40,force_tx=ftx,force_bg=fbg)
    img=Image.new("RGB",(s.W,s.H)); img.putdata([s.pal[v&0xFF] for r in s.rows for v in r])
    previews.append((code,img))
    if COMMIT: s.commit()
# preview sheet
maxw=max(im.width for _,im in previews); tot=sum(im.height+18 for _,im in previews)
sheet=Image.new("RGB",(maxw*2+10,(tot)*2),(20,20,20))
from PIL import ImageDraw; dr=ImageDraw.Draw(sheet); y=0
for code,im in previews:
    im2=im.resize((im.width*2,im.height*2),Image.NEAREST); sheet.paste(im2,(5,y+18))
    dr.text((5,y),code.decode('latin1','replace'),fill=(255,255,0)); y+=im2.height+36
sheet.save(r"C:\Users\原來是個胖仔\_art_png\campaign_preview.png")
print("COMMITTED" if COMMIT else "PREVIEW ONLY")

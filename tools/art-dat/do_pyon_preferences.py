# -*- coding: utf-8 -*-
import importlib.util, shutil
spec=importlib.util.spec_from_file_location("paintlib",r"C:\Users\原來是個胖仔\_paintlib.py")
P=importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
ART=r"D:\03_game_tmp\AlliedGeneralLite_v1.1\AlliedGeneral_v1.1\ART\ART.DAT"
shutil.copy2(ART+".bak",ART)
FB=r"C:\Windows\Fonts\msjhbd.ttc"   # JhengHei Bold - crisp at small sizes
s=P.Screen(ART,b"pYon")
opt=dict(font=FB,mask=80)
s.paint("偏好設定",(95,2,245,24),False,force_size=12,**opt)
s.paint("經驗",(38,92,130,114),False,force_size=11,**opt); s.paint("經驗",(205,92,298,114),False,force_size=11,**opt)
s.paint("聲望",(38,200,130,232),False,force_size=11,**opt); s.paint("聲望",(205,200,298,232),False,force_size=11,**opt)
s.paint("補給",(40,352,150,380),True,force_size=11,**opt); s.paint("天氣",(40,380,150,406),True,force_size=11,**opt)
s.paint("顯示部隊強度",(150,352,302,380),True,force_size=11,**opt); s.paint("顯示隱藏單位",(150,380,302,406),True,force_size=11,**opt)
s.paint("顯示對手移動",(95,404,250,430),True,force_size=11,**opt)
s.paint("取消",(70,420,145,430),False,thr=35,force_size=9,**opt)
s.paint("確定",(235,420,272,430),False,thr=35,force_size=9,**opt)
s.preview(r"C:\Users\原來是個胖仔\_art_png\pyon_v4.png")
s.commit()

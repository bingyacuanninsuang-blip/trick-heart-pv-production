from pathlib import Path
import sys,shutil
sys.dont_write_bytecode=True
old=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
here=Path('<REVISION_WORKSPACE>/work/audit-mask')
sys.path.insert(0,str(old.parent/'python_lib'))
from PIL import Image
import cv2,numpy as np
path=Path('<USER_HOME>/.codex/generated_images/01a12612-48b8-76f1-a8ed-b1da38d8981f/exec-ad2fcd13-79e4-475b-8789-603060e9ac47.png')
cel=np.asarray(Image.open(path).convert('RGBA').resize((1280,860),Image.Resampling.LANCZOS)).copy()
cel=cv2.warpAffine(cel,np.float32([[1,0,0],[0,1,100]]),(1280,860),borderMode=cv2.BORDER_REPLICATE)
Image.fromarray(cel).save(here.parent/'assets-v7/hand-1084.png')
shutil.copyfile(old/'assets/white-sailor/bare-612-v3.png',here.parent/'assets-v7/hand-600.png')
p=here/'hand_fixes.py';s=p.read_text(encoding='utf-8-sig')
s=s.replace("m=c.rabbit_mask(src,(600,0,1920,880),(900,0,1920,650))","m=v6.f.component(c.rabbit_mask(src,(600,0,1920,880),(900,0,1920,650)),200)")
s=s.replace('asset600_crop_ref=600','asset600_crop_ref=612')
s=s.replace('matrix=c.tracking(c.reference(cropref),src,track,n)','matrix=alternate_register(c.reference(cropref),src,v6) if ref==600 else c.tracking(c.reference(cropref),src,track,n)')
s=s.replace('for n in [603,605,606,612,620,1082,1084,1088]:','for n in [600,601,602,603,605,606,612,620,1082,1084,1088]:')
p.write_text(s,encoding='utf-8')

p=here/'hand_fixes.py';s=p.read_text(encoding='utf-8')
extra='''def alternate_register(ref,src,v6):
    np=v6.np
    def anchors(a):
        r,g,b=a.astype(np.int16).transpose(2,0,1)
        yellow=(r>230)&(g>125)&(g<220)&(b<100)&(v6.c.rect((1120,440,1560,760))>0)
        yy,xx=np.where(yellow);coin=np.array([xx.mean(),yy.mean()])
        wrist=(r>245)&(g>185)&(g<240)&(b>175)&(b<245)&(v6.c.rect((1200,760,1600,900))>0)
        yy,xx=np.where(wrist);joint=np.array([xx.mean(),yy.mean()])
        return coin,joint
    ac,aw=anchors(ref);bc,bw=anchors(src)
    av=aw-ac;bv=bw-bc
    denom=float(av@av)
    co=float(av@bv)/denom
    si=float(av[0]*bv[1]-av[1]*bv[0])/denom
    linear=np.array([[co,-si],[si,co]])
    shift=bc-linear@ac
    return np.column_stack([linear,shift]).astype(np.float32)

'''
s=s if 'def alternate_register(ref,src,v6):' in s else s.replace('def compose_hand(',extra+'def compose_hand(')
p.write_text(s,encoding='utf-8')
print('Hand helper updated with alternate600 and completed1084')



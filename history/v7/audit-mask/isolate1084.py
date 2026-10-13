from pathlib import Path
import os,sys,json
sys.dont_write_bytecode=True
OLD=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
HERE=Path('<REVISION_WORKSPACE>/work/audit-mask')
ASSETS=HERE.parent/'assets-v7'
sys.path.insert(0,str(OLD.parent/'python_lib'));sys.path.insert(0,str(OLD/'tools'))
import revision6_composite as v6
from PIL import Image,ImageDraw
import numpy as np,cv2
cv2.setNumThreads(1)
path=Path('<USER_HOME>/.codex/generated_images/01a12612-48b8-76f1-a8ed-b1da38d8981f/exec-620385ba-ace0-4a0c-bb3d-d52cf5892d90.png')
im=np.asarray(Image.open(path).convert('RGB').resize((1280,860),Image.Resampling.LANCZOS)).copy()
src=np.asarray(Image.open(HERE/'source-1084-crop.png').convert('RGB'))
def foot_bounds(a):
    white=(a.min(2)>245)&(a.max(2).astype(int)-a.min(2).astype(int)<7)
    yy,xx=np.indices(white.shape)
    foot=white&(xx>800)&(xx<1200)&(yy>300)&(yy<520)
    ys,xs=np.where(foot)
    bottom=int(ys.max())
    at=float(np.median(xs[ys>bottom-5]))
    return np.array([at,bottom]),[int(xs.min()),int(ys.min()),int(xs.max()),bottom,int(foot.sum())]
ga,gb=foot_bounds(im);sa,sb=foot_bounds(src)
dx,dy=0,37  # Source paw bottom y455; generated paw bottom y418 after resize
matrix=np.float32([[1,0,dx],[0,1,dy]])
r,g,b=im.astype(np.int16).transpose(2,0,1)
skin=(r>225)&(g>175)&(b>165)&(r-g>5)&(r-g<75)&(g-b<35)
count,labels,stats,_=cv2.connectedComponentsWithStats(skin.astype(np.uint8),8)
j=max(range(1,count),key=lambda k:stats[k,4]);skin=(labels==j).astype(np.uint8)*255
yy,xx=np.indices((860,1280))
cuff=(im.max(2).astype(int)-im.min(2).astype(int)<40)&(im.max(2)<235)&(yy>550)&(xx<720)
nonred=~((r>65)&(r>g*1.55)&(r>b*1.50)&(abs(g-b)<38))
alpha=(nonred&(cv2.dilate(skin|cuff.astype(np.uint8)*255,np.ones((7,7),np.uint8))>0)).astype(np.uint8)*255
alpha=cv2.morphologyEx(alpha,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
from scipy.ndimage import binary_fill_holes
alpha=binary_fill_holes(alpha>0).astype(np.uint8)*255
im=cv2.warpAffine(im,matrix,(1280,860),borderMode=cv2.BORDER_REPLICATE)
alpha=cv2.warpAffine(alpha,matrix,(1280,860),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_REPLICATE)
rgba=np.dstack([im,alpha]);ASSETS.mkdir(exist_ok=True)
Image.fromarray(rgba).save(HERE/'hand-1084-provisional.png')
Image.fromarray(rgba).save(HERE/'hand-1084-isolated.png')
print(json.dumps({'registration_dxdy':[int(dx),int(dy)],'source_foot_stats':sb,'generated_foot_stats':gb,'crop':[260,220,1540,1080],'alpha_pixels':int((alpha>0).sum())}))

v6.ASSETS=ASSETS;v6.sprite.cache_clear();v6.v3.sprite=v6.sprite
for n in [1082,1084,1090]:
    out,rec=v6.render(n)
    Image.fromarray(out).save(HERE/f'new-{n:05d}.png')
    prior=v6.c.read(OLD/f'runs/paired-v6/frames/final/{n:05d}.png')
    pair=Image.new('RGB',(1920,570),'#172029');d=ImageDraw.Draw(pair)
    d.text((5,5),f'v6 frame {n}',fill='white');d.text((965,5),f'v7 joint-cel hand frame {n}',fill='white')
    pair.paste(Image.fromarray(prior).resize((960,540)),(0,30))
    pair.paste(Image.fromarray(out).resize((960,540)),(960,30))
    pair.save(HERE/f'contact-{n:05d}.jpg',quality=98)
    print(json.dumps(rec))





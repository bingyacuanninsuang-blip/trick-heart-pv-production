"""Isolated v7 motion/end patches. Artwork is imagegen; code only masks/tracks/composites."""
from pathlib import Path
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'work/assets-v7'
RANGES = [(2139,2169), (3584,3630), (3630,3666)]

@lru_cache(maxsize=8)
def asset(name):
    return np.asarray(Image.open(ASSETS / (name + '.png')).convert('RGB').resize((1920,1080), Image.Resampling.LANCZOS)).copy()

def collar_anchor(s,c):
    # Source white collar is a stable clothing instance, separate from face/ear.
    neutral=(s.min(2)>228)&((s.max(2).astype(int)-s.min(2))<22)
    raw=neutral&(c.rect((1500,760,1920,1030))>0)
    count,labels,stats,_=cv2.connectedComponentsWithStats(raw.astype(np.uint8),8)
    if count<2:raise ValueError('Source collar missing')
    ix=max(range(1,count),key=lambda j:stats[j,4])
    if stats[ix,4]<3000:raise ValueError('Source collar too small')
    yy,xx=np.where(labels==ix)
    top=yy<np.percentile(yy,28)
    return np.float32([xx[top].mean(),yy[top].mean()])

def patch_blow(n, out, s, v6):
    c,f = v6.c,v6.f
    if n < 2147 or n >= 2157:
        out,rec = v6.blow(s,n)
        return out,dict(rec,blow_state='prepare' if n < 2147 else 'relax',
                        source_pose=2139 if n<2147 else 2166)
    state = 'inhale' if n < 2151 else 'blow'
    gen = asset(state)
    # Generated cels retain the original adopted 2145 image registration.
    mask = c.generated_nonred(gen) & (c.rect((1370,0,1920,1080))>0)
    gm = v6.biggest(mask.astype(np.uint8)*255)
    state_ref=2148 if state=='inhale' else 2151
    ref=v6.src(state_ref)
    matrix=c.tracking(ref,s,(1570,300,1910,960),n)
    delta=collar_anchor(ref,c)-collar_anchor(v6.src(2145),c)
    if np.array_equal(matrix,np.float32([[1,0,0],[0,1,0]])):
        delta+=collar_anchor(s,c)-collar_anchor(ref,c)
    matrix[:,2]+=matrix[:,:2]@delta
    gen = cv2.warpAffine(gen,matrix,(1920,1080),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    gm = cv2.warpAffine(gm,matrix,(1920,1080),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_REPLICATE)
    erase = (c.source_nonbg(s,f.color(s)) & (c.rect((1370,0,1920,1080))>0)).astype(np.uint8)*255
    out = s.copy()
    out[c.dilate(erase|gm,4)>0] = f.color(s)
    out = c.paste(out,gen,gm)
    # Original filled paper shape owns all original lyrics and fragments.
    gold = c.text_foreground(s,[(0,0,1510,1080)])
    contours,_ = cv2.findContours(gold,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    paper = np.zeros((1080,1920),np.uint8)
    cv2.drawContours(paper,contours,-1,255,-1)
    out = c.paste(out,s,paper)
    return out,dict(blow_state=state,source_pose=2148 if state=='inhale' else 2151,
                    registration_ref=2145,matrix=matrix.tolist(),source_lyric_animation=True)

def patch_braid(n,out,s,v6):
    c,f=v6.c,v6.f
    pm,bd=f.panel_mask(s,(579,316,1370,798))
    if bd is None:
        raise ValueError('No source braid panel at frame '+str(n))
    x,y,w,h=bd
    gen=asset('braid')
    temp=out.copy()
    temp[y:y+h,x:x+w]=cv2.resize(gen[325:790,580:1370],(w,h),interpolation=cv2.INTER_LANCZOS4)
    out=c.paste(out,temp,pm)
    return out,dict(braid_simple_cel=True,panel_bounds=list(map(int,bd)))

def patch_back(n,out,s,v6):
    c,f=v6.c,v6.f
    gen=asset('back')
    # Use the proven scene's original typography/particle ownership logic.
    # Inject only the adopted cel layer; restore immediately after the call.
    gm=f.key(gen,(680,0,1280,1080))
    original=f.layer
    def adopted(name,box,border=False):
        if name=='v7-back':return gen.copy(),gm.copy()
        return original(name,box,border)
    scene=next(dict(sh) for sh in f.SHOTS if sh['start']<=n<sh['end'])
    scene.update(asset='v7-back',roi=(680,0,1280,1080))
    f.layer=adopted
    try:
        out,_=f.apply_scene(s,n,scene)
    finally:
        f.layer=original
    return out,dict(back_braid_side='character_left/viewer_left',
                    back_clips_side='character_left/viewer_left',
                    back_simple_cel=True,original_typography_preserved=True)

def render(n,out,s,v6):
    if 2139<=n<2169:return patch_blow(n,out,s,v6)
    if 3584<=n<3630:return patch_braid(n,out,s,v6)
    if 3630<=n<3666:return patch_back(n,out,s,v6)
    return out,{}





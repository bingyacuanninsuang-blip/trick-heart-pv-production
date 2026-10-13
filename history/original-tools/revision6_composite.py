"""V6: hand anatomy and shared pale grade; complete foreground mattes."""
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor
import os,sys,json,shutil,argparse,multiprocessing
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'python_lib'))
import imageio_ffmpeg
os.environ['ROXY_FFMPEG']=imageio_ffmpeg.get_ffmpeg_exe()
import revision5_composite as v5
import revision3_composite as v3
import revision4_composite as v4
import revision_composite as v2
import composite as c
import full_composite as f
from composite import np,cv2,Image,ImageDraw,ImageFont
RUN=PROJECT/'runs/paired-v6'
ASSETS=PROJECT/'assets/paired-v6'
DEST=RUN/'frames/final'
REVIEW=RUN/'review'
PALE=np.float32([255,246,244])
SHADE=np.float32([250,230,227])
NEW_HANDS={1018,1059,1064,1071,1075,1084,600}
RANGES=[(393,444),(600,603),(1018,1091),(1281,1308),(1930,2007),
        (2081,2127),(2139,2169),(2970,3003),(3584,3630),(3666,3768)]
def old(n):return c.read(PROJECT/'runs/paired-v5/frames/final'/f'{n:05d}.png')
def src(n):return v5.read(n,'source')
@lru_cache(maxsize=16)
def art(name):
    return np.asarray(Image.open(ASSETS/f'{name}.png').convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS)).copy()
def biggest(mask,seed=None):
    count,lab,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    if seed is not None:
        ids=np.unique(lab[(seed>0)&(mask>0)])
        ids=[int(i) for i in ids if i and stats[i,4]>100]
    else:ids=[max(range(1,count),key=lambda j:stats[j,4])] if count>1 else []
    return np.isin(lab,ids).astype(np.uint8)*255
def skin(im):
    broad=v5.skin(im)
    core=broad&(im[:,:,0]>215)&(im[:,:,1]>185)&(im[:,:,2]>178)
    count,lab,stats,_=cv2.connectedComponentsWithStats(c.dilate(broad,5),8)
    contact=np.bincount(lab[core],minlength=count)
    ids=[i for i in range(1,count) if contact[i]>12]
    return broad&np.isin(lab,ids)
def grade(im,mask):
    count=int(mask.sum())
    if not count:return im,0
    values=im[mask].astype(np.float32)
    light=np.maximum(values[:,1],values[:,2])
    anchor=np.percentile(light,80)
    darkness=np.clip((anchor-light)/48,0,1)
    # Shared pale cel palette removes orange casts and strong skin gradients.
    corrected=PALE[None,:]*(1-darkness[:,None])+SHADE[None,:]*darkness[:,None]
    out=im.copy();out[mask]=np.clip(corrected,0,255).astype(np.uint8)
    return out,count
ORIGINAL_SPRITE=v3.sprite
@lru_cache(maxsize=20)
def sprite(ref):
    if ref not in NEW_HANDS:return ORIGINAL_SPRITE(ref)
    x0,y0,x1,y1=v3.CROPS[str(ref)]
    im=Image.open(ASSETS/f'hand-{ref}.png').convert('RGBA').resize((x1-x0,y1-y0),Image.Resampling.LANCZOS)
    a=np.asarray(im).copy()
    rgb=np.zeros((1080,1920,3),np.uint8);alpha=np.zeros((1080,1920),np.uint8)
    rgb[y0:y1,x0:x1]=a[:,:,:3];alpha[y0:y1,x0:x1]=a[:,:,3]
    return rgb,alpha
v3.sprite=sprite

def pair(out,s,n):
    gen=art('palm')
    sleeve=c.polygon([(70,0),(665,0),(755,102),(582,355),(393,385),(205,230)])>0
    zone=c.rect((100,0,1145,745))>0
    neutral=(gen.max(2).astype(int)-gen.min(2).astype(int)<22)&sleeve&c.generated_nonred(gen)
    gm=biggest(((skin(gen)|neutral)&zone).astype(np.uint8))
    gm=c.dilate(gm,9)
    matrix=c.tracking(src(393),s,(200,0,1080,700),n)
    gm=c.warp(gm,matrix,True);gen=c.warp(gen,matrix)
    ownership=c.warp(c.rect((100,0,1130,740)),matrix,True)>0
    owned=v5.owned_pair(out,n)&skin(out)&ownership
    gray=c.generated_nonred(out)&(out.max(2)<210)&(c.warp(sleeve.astype(np.uint8)*255,matrix,True)>0)
    erase=c.dilate((owned|gray).astype(np.uint8)*255,13)
    out=out.copy();out[erase>0]=f.color(s)
    pm,pc=v3.paper(s)
    if pc is not None:out[(erase>0)&(pm>0)]=pc
    out=c.paste(out,gen,gm)
    return out,{'palm_no_nails':True,'palm_reference':393}

def shallow_hat(out,s,n):
    r,g,b=s.astype(np.int16).transpose(2,0,1)
    region=c.rect((350,320,1450,1065))&c.frame_inner(s)
    visible=(r>18)&(r<110)&(abs(r-g)<15)&(abs(g-b)<15)&(region>0)
    if visible.sum()<1000:return out,{'shallow_beret':'hidden by source smoke'}
    gen=art('hat');gm=(c.generated_nonred(gen)&(region>0)).astype(np.uint8)*255
    gm=biggest(gm)
    matrix=v5.hat_motion(s,1281,n,(415,700,1400,1040))
    gm=c.warp(gm,matrix,True);gen=c.warp(gen,matrix)
    erase=(c.source_nonbg(out,f.color(s))&(region>0)).astype(np.uint8)*255
    out=out.copy();out[c.dilate(erase|gm,3)>0]=f.color(s)
    out=c.paste(out,gen,gm)
    out=c.paste(out,s,v5.foreground_white(s))
    return c.paste(old(n),out,c.frame_inner(s)),{'shallow_beret':True}

def dog(out,s):
    box=c.rect((230,520,897,1080))>0
    matte=biggest((c.source_nonbg(s,f.color(s))&box).astype(np.uint8))
    matte=c.dilate(matte,3)
    return c.paste(out,s,matte),{'dog_full_source_matte':int((matte>0).sum())}

def hair(s,n):
    shot=dict(asset='full-2090',ref=2090,roi=(485,0,1920,1080),
              letters=[(0,440,850,650)],duck=True)
    out,_=f.apply_scene(s,n,shot)
    return out,{'hair_roi_expanded':True}

def blow(s,n):
    ref=v2.pose(n,(2139,2166),(1550,250,1920,850))
    name='mage-profile-closed-v2' if ref==2166 else 'full-2145'
    im=c.asset(name).copy()
    gm=biggest((c.generated_nonred(im)&(c.rect((1370,0,1920,1080))>0)).astype(np.uint8))
    matrix=c.tracking(src(ref),s,(1570,300,1910,840),n)
    gm=c.warp(gm,matrix,True);im=c.warp(im,matrix)
    erase=((c.source_nonbg(s,f.color(s)))&(c.rect((1370,0,1920,1080))>0)).astype(np.uint8)*255
    out=s.copy();out[c.dilate(erase|gm,4)>0]=f.color(s)
    out=c.paste(out,im,gm)
    # Source paper including black lyrics is one moving, filled foreground shape.
    gold=c.text_foreground(s,[(0,0,1510,1080)])
    contours,_=cv2.findContours(gold,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    paper=np.zeros((1080,1920),np.uint8)
    cv2.drawContours(paper,contours,-1,255,-1)
    out=c.paste(out,s,paper)
    return out,{'source_lyric_animation':True,'static_paper_fragment_removed':True}

def clean_band(s):
    # Use the adopted clean cel without restoring similarly coloured old clothing.
    saved=c.butterflies
    try:
        c.butterflies=lambda _:np.zeros((1080,1920),np.uint8)
        out,mask=c.band(s,'full-2976','left',(125,895))
    finally:c.butterflies=saved
    return out,{'white_shoulder_clean':True}

def braid(out,s,n):
    pm,bd=f.panel_mask(s,(579,316,1370,798))
    if bd:
        im=art('braid');x,y,w,h=bd
        temp=out.copy();temp[y:y+h,x:x+w]=cv2.resize(im[325:790,580:1370],(w,h),interpolation=cv2.INTER_LANCZOS4)
        out=c.paste(out,temp,pm)
    return out,{'braid_end_tie_action':True}

def animal_mask(s):
    r,g,b=s.astype(np.int16).transpose(2,0,1)
    cream=np.max(abs(s.astype(np.int16)-[255,236,209]),axis=2)<18
    cream &= c.rect((930,565,1920,1080))>0
    cream=f.component(cream.astype(np.uint8)*255,200)
    dark=(s.max(2)<65)&(c.rect((1280,575,1920,1080))>0)
    count,lab,stats,_=cv2.connectedComponentsWithStats(dark.astype(np.uint8),8)
    ids=[j for j in range(1,count) if stats[j,4]>10000]
    dog=cream|np.isin(lab,ids).astype(np.uint8)*255
    dog=c.dilate(dog,3)
    rabbit=c.rabbit_mask(s,(0,160,540,705),(50,160,390,390))
    white=(s.min(2)>246)&(c.rect((1400,315,1855,735))>0)
    white=f.component(white.astype(np.uint8)*255,400)
    orange=(r>230)&(g>125)&(g<185)&(b<80)&(c.rect((1450,315,1855,735))>0)
    orange &= c.dilate(white,17)>0
    duck=c.dilate(white|orange.astype(np.uint8)*255,3)
    return dog|rabbit|duck

def animals(s,n):
    im,gm=f.layer('full-3675',f.FULL)
    # Character/animal art provides all clothing and hand outlines.
    out=s.copy();bg=f.color(s)
    erase=c.dilate((c.source_nonbg(s,bg).astype(np.uint8)*255)|gm,5)
    out[erase>0]=bg;out=c.paste(out,im,gm)
    out=c.paste(out,s,animal_mask(s))
    # Restore original typography. Decorative gold never owns the old cuffs.
    out=c.paste(out,s,c.dilate(f.letters_mask(s,[(1670,0,1920,1080)]),2))
    dm=f.decorations(s)
    dm &= ~c.dilate(gm,3)
    dm &= ~c.rect((10,730,270,990))
    dm &= ~c.rect((420,250,1560,1080))
    out=c.paste(out,s,dm)
    return out,{'white_cuff_clean':True,'animal_outline_ownership':True}

def ending(out,s):
    pm,bd,_=v4.panel_geometry(s,(120,270,985,820))
    x,y,w,h=bd
    im=art('ending')
    patch=cv2.resize(im[310:780,160:940],(w,h),interpolation=cv2.INTER_LANCZOS4)
    temp=out.copy();temp[y:y+h,x:x+w]=patch
    out=c.paste(out,temp,pm)
    return out,{'ending_old_gold_removed':True}

EXTRA_HANDS=[
 (240,325,[(1090,950,1185,1030)]),
 (454,464,[(1380,240,1670,410)]),
 (464,472,[(800,380,1020,560)]),
 (912,1018,[(910,650,1100,970),(1570,745,1795,1035)]),
 (1174,1208,[(570,695,840,1020),(1090,695,1350,1035)]),
 (1401,1467,[(1160,480,1385,835)]),
 (1543,1585,[(570,600,900,1010)]),
 (1631,1680,[(105,600,195,690),(470,430,570,550),(1375,425,1515,575),(1595,595,1665,670)]),
 (2401,2437,[(1060,1010,1340,1080)]),
 (2437,2455,[(1060,870,1340,1080)]),
 (2455,2472,[(300,230,1600,950)]),
 (2785,2952,[(630,730,690,815),(930,730,1030,825)]),
 (3003,3083,[(300,230,1600,950)]),
 (3083,3239,[(820,740,940,825)]),
 (3356,3397,[(820,740,940,825)]),
 (3478,3509,[(300,230,1600,950)]),
 (3584,3630,[(615,390,1085,790)]),
 (3630,3666,[(1120,575,1190,665)]),
 (3666,3698,[(20,760,180,955),(1360,330,1505,535)]),
]
def all_hands(out,s,n):
    sk=skin(out)
    mask=v5.hand_mask(out,s,n)&sk
    if 393<=n<444:mask|=sk&(c.rect((450,90,1500,1030))>0)
    for a,b,boxes in EXTRA_HANDS:
        if a<=n<b:
            for box in boxes:mask|=sk&(c.rect(box)>0)
    if 3509<=n<3543:
        own=c.polygon([(846,641),(900,607),(937,660),(928,681),(959,703),(980,760),(974,837),(929,925),(863,894),(839,824),(820,751),(828,686)])
        matrix=c.tracking(src(3516),s,(825,615,982,930),n)
        mask|=sk&(c.warp(own,matrix,True)>0)
    if 1018<=n<1091 or 600<=n<603:mask|=sk&(c.rect((250,150,1600,1080))>0)
    out,count=grade(out,mask)
    return out,count

def affected(n):
    return v5.affected(n) or any(a<=n<b for a,b in RANGES) or any(a<=n<b for a,b,_ in EXTRA_HANDS) or 3509<=n<3543

def render(n):
    out=old(n)
    if not affected(n):return out,{'frame':n,'version':'v6','reused_v5':True,'hand_pixels':0}
    s=src(n);meta={}
    if 393<=n<444:out,meta=pair(out,s,n)
    elif 600<=n<603 or 1018<=n<1036 or 1059<=n<1091:
        refs=next(refs for a,b,refs in v3.HAND_RANGES if a<=n<b)
        rebuilt,hand=v3.bare_hand(n,refs)
        ref=hand['reference'] if hand else refs[0]
        box=tuple(v3.CROPS[str(ref)])
        matrix=c.tracking(src(ref),s,box,n)
        region=c.dilate(c.warp(c.rect(box),matrix,True),18)
        out=c.paste(out,rebuilt,region);meta={'hand_redrawn':True,'hand_reference':ref}
    elif 1281<=n<1308:out,meta=shallow_hat(out,s,n)
    elif 1930<=n<2007:out,meta=dog(out,s)
    elif 2081<=n<2127:out,meta=hair(s,n)
    elif 2139<=n<2169:out,meta=blow(s,n)
    elif 2970<=n<3003:out,meta=clean_band(s)
    elif 3584<=n<3630:out,meta=braid(out,s,n)
    elif 3666<=n<3698:out,meta=animals(s,n)
    elif n>=3698:out,meta=ending(out,s)
    out,count=all_hands(out,s,n)
    return out,{'frame':n,'version':'v6','reused_v5':not meta and not count,'hand_pixels':count,**meta}
def one(n):
    cv2.setNumThreads(1)
    if not affected(n):
        shutil.copyfile(PROJECT/'runs/paired-v5/frames/final'/f'{n:05d}.png',DEST/f'{n:05d}.png')
        return {'frame':n,'version':'v6','reused_v5':True,'hand_pixels':0}
    out,record=render(n)
    dest=DEST/f'{n:05d}.png'
    if record['reused_v5']:shutil.copyfile(PROJECT/'runs/paired-v5/frames/final'/dest.name,dest)
    else:Image.fromarray(out).save(dest,compress_level=3)
    return record
def preview(picks):
    REVIEW.mkdir(parents=True,exist_ok=True)
    for k in range(0,len(picks),8):
        sheet=Image.new('RGB',(1920,600),'#172029');d=ImageDraw.Draw(sheet)
        for i,n in enumerate(picks[k:k+8]):
            out,rec=render(n);Image.fromarray(out).save(REVIEW/f'{n:05d}.png')
            (REVIEW/f'{n:05d}.json').write_text(json.dumps(rec,indent=2))
            x=i%4*480;y=i//4*300
            sheet.paste(Image.fromarray(out).resize((480,270)),(x,y+30))
            d.text((x+6,y+5),f'{n} / {n/24:.3f}s',fill='white')
        sheet.save(REVIEW/f'preview-{k//8}.jpg',quality=97)
    print('Previewed',len(picks),'frames',flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');ap.add_argument('--frames',nargs='+',type=int);args=ap.parse_args()
    if args.all:
        DEST.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
        records=[]
        with ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
            for i,r in enumerate(pool.map(one,range(3768),chunksize=8)):
                records.append(r)
                if i%120==0:print('V6 frames',i,'/ 3768',flush=True)
        (REVIEW/'frame-verification.json').write_text(json.dumps(records,indent=2))
    else:preview(args.frames or [393,432,600,1018,1036,1059,1064,1071,1075,1084,1281,1290,1944,2090,2148,2154,2155,2163,2976,3588,3600,3675,3710])
if __name__=='__main__':main()


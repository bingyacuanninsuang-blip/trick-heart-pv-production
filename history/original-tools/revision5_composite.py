"""Paired PV revision: beret props and black-character hand colour.
Uses v4 lossless frames as immutable inputs and source-owned motion/occlusion.
"""
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor
import argparse,os,sys,json,shutil,multiprocessing
PROJECT=Path(__file__).resolve().parents[1]
WORK=PROJECT.parent
sys.path.insert(0,str(WORK/'python_lib'))
OLD=PROJECT/'runs/white-sailor'
RUN=PROJECT/'runs/paired-v5'
ASSETS=PROJECT/'assets/paired-v5'
os.environ.update(PV_RUN_ROOT=str(OLD),PV_ASSET_ROOT=str(PROJECT/'assets/white-sailor'),PV_CHARACTER_PROFILE='paired-characters')
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
import composite as c
import full_composite as f
import revision4_juggle as j
DEST=RUN/'frames/final'
REVIEW=RUN/'review'
TARGET=np.float32([253,235,230])
IDENTITY=np.float32([[1,0,0],[0,1,0]])
# Declared ownership regions exclude faces, legs, clothing and the white character.
BOXES=[
(0,86,[(550,285,1390,835)]),(163,240,[(550,285,1390,835)]),
(240,325,[(425,360,610,530)]),(449,454,[(370,0,560,185)]),
(464,472,[(270,0,410,85),(805,380,932,520)]),
(534,546,[(210,465,480,780),(1420,465,1690,780)]),
(546,621,[(320,420,1450,1030)]),
(901,912,[(225,270,445,715),(1220,670,1720,920)]),
(1018,1091,[(260,170,1580,1080)]),

(1244,1281,[(70,885,330,1050),(1300,500,1490,870)]),
(1467,1543,[(705,470,1135,905)]),
(1585,1631,[(1120,590,1510,1080),(0,0,420,270)]),
(1850,1930,[(300,400,1650,1080)]),
(1930,2007,[(850,400,1000,535),(1128,655,1220,810)]),
(2197,2224,[(420,420,930,825)]),
(2224,2235,[(675,420,980,840)]),
(2314,2367,[(480,870,810,1080)]),
(2367,2401,[(335,510,820,1080)]),

]
def read(n,kind='full-composite-v4'):
    return np.asarray(Image.open(OLD/f'frames/{kind}/{n:05d}.png').convert('RGB'))

@lru_cache(maxsize=6)
def art(name):
    return np.asarray(Image.open(ASSETS/(name+'.png')).convert('RGB'))

def skin(im):
    r,g,b=im.astype(np.int16).transpose(2,0,1)
    return (r>180)&(g>145)&(b>135)&(r-g>8)&(r-g<65)&(r-b>9)&(g-b<32)&((r-g)>(g-b)*.75)

def owned_pair(im,n):
    m=skin(im)&(c.rect((450,90,1500,1030))>0)
    num,lab,st,centers=cv2.connectedComponentsWithStats(m.astype(np.uint8),8)
    ids=[]
    for i in range(1,num):
        x,y,w,h,area=st[i];cx,cy=centers[i]
        if area<16:continue
        if 393<=n<444 and cx<930 and cy<560:ids.append(i)
        elif 3003<=n<3024 and cx<1025 and cy<540:ids.append(i)
        elif 3024<=n<3038 and cy<472:ids.append(i)
    return np.isin(lab,ids)

def gray_hand_regions(src,n):
    # Source mage gloves are neutral gray. Shirt/hat are rejected geometrically.
    r,g,b=src.astype(np.int16).transpose(2,0,1)
    raw=(r>210)&(r<252)&(abs(r-g)<9)&(abs(g-b)<9)
    try:a=j.face_anchor(src)
    except ValueError:a=j.source_info(min(n,2768))[0] if 2472<=n<2785 else None
    num,lab,st,centers=cv2.connectedComponentsWithStats(raw.astype(np.uint8),8)
    roi=np.zeros((1080,1920),np.uint8)
    cuff=(r>230)&(g>100)&(g<190)&(b<90)
    ids=[]
    for i in range(1,num):
        x,y,w,h,area=map(int,st[i]);cx,cy=centers[i]
        if area<120 or y<200 or w>350 or h>300:continue
        if a:
            fx,fy,fw=a
            neck=(int(fx-fw*.33),int(fy+fw*.55),int(fx+fw*.33),int(fy+fw*1.55))
            hit=((lab[max(0,neck[1]):min(1080,neck[3]),max(0,neck[0]):min(1920,neck[2])])==i).sum()
            if hit>80:continue
        if 624<=n<704 and y>880:continue
        contact=cuff[max(0,y-22):min(1080,y+h+22),max(0,x-22):min(1920,x+w+22)].sum()
        if contact<40:continue
        ids.append(i)
    return np.isin(lab,ids)

def gray_owned_skin(im,src,n):
    anchors=gray_hand_regions(src,n)
    anchors=cv2.dilate(anchors.astype(np.uint8),np.ones((7,7),np.uint8))>0
    num,lab,stats,_=cv2.connectedComponentsWithStats(skin(im).astype(np.uint8),8)
    contact=np.bincount(lab[anchors],minlength=num)
    ids=[i for i in range(1,num) if contact[i]>9 and stats[i,4]>16]
    return np.isin(lab,ids)

def hand_mask(im,src,n):
    roi=np.zeros((1080,1920),np.uint8)
    for a,b,boxes in BOXES:
        if a<=n<b:
            for box in boxes:roi |= c.rect(box)
    mask=skin(im)&(roi>0)
    if 393<=n<444 or 3003<=n<3038:mask |= owned_pair(im,n)
    if 621<=n<704 or 2472<=n<2778:
        mask |= gray_owned_skin(im,src,n)
    if 1154<=n<1174 or 2785<=n<2952:
        num,lab,stats,centers=cv2.connectedComponentsWithStats(skin(im).astype(np.uint8),8)
        ids=[]
        for i in range(1,num):
            cx,cy=centers[i]
            if stats[i,4]<8:continue
            if 1154<=n<1174 and 1080<cx<1400 and 630<cy<900:ids.append(i)
            if 2785<=n<2952 and ((625<cx<687 and 740<cy<815) or (935<cx<1030 and 735<cy<790)):ids.append(i)
        mask |= np.isin(lab,ids)
    if 459<=n<464:
        ownership=c.polygon([(1430,265),(1555,265),(1627,367),(1595,382),(1535,342),(1485,371),(1427,365)])
        mask |= skin(im)&(ownership>0)
    return mask

def colour_hands(im,mask):
    count=int(mask.sum())
    if count<12:return im,{'hand_pixels':0}
    # Uniform palette shift retains local shading and all ink outlines.
    median=np.median(im[mask],axis=0)
    delta=np.maximum(TARGET-median,0);delta[0]=min(delta[0],3)
    out=im.copy()
    out[mask]=np.clip(im[mask].astype(np.float32)+delta,0,255).astype(np.uint8)
    return out,{'hand_pixels':count,'before_median':median.tolist(),'after_median':np.median(out[mask],axis=0).tolist()}

def foreground_white(src,all_white=False):
    m=(src.min(axis=2)>246).astype(np.uint8)
    if all_white:return cv2.dilate(m,np.ones((5,5),np.uint8))*255
    num,lab,st,_=cv2.connectedComponentsWithStats(m,8)
    ids=[i for i in range(1,num) if st[i,4]>9000]
    return cv2.dilate(np.isin(lab,ids).astype(np.uint8),np.ones((5,5),np.uint8))*255

def hat_motion(src,ref,n,box):
    m=c.tracking(read(ref,'source'),src,box,n)
    if ref==855 and np.array_equal(m,IDENTITY):
        def corner(im):
            r,g,b=im.astype(np.int16).transpose(2,0,1)
            dark=(r>17)&(r<85)&(abs(r-g)<9)&(abs(g-b)<9)&(c.rect((220,710,1400,1080))>0)
            yy,xx=np.where(dark)
            return np.float32([np.percentile(xx,1),yy.min()]) if len(xx)>100 else np.float32([0,0])
        d=corner(src)-corner(read(855,'source'))
        m=IDENTITY.copy();m[:,2]=d
    return m

@lru_cache(maxsize=3)
def prop_layer(name):
    im=art(name)
    if name=='rabbit':
        region=c.rect((200,715,1220,1080))
    elif name=='held':
        region=c.polygon([(40,650),(490,650),(490,880),(468,1025),(380,1060),(40,1060)])
        region &= c.frame_inner(im)
    else:
        region=c.rect((360,325,1450,1065))&c.frame_inner(im)
    mask=(c.generated_nonred(im)&(region>0)).astype(np.uint8)*255
    if name=='rabbit':mask[im.min(axis=2)>175]=0
    if name=='held':
        mask[skin(im)]=0
        mask[(im.min(axis=2)>215)]=0
    num,lab,st,_=cv2.connectedComponentsWithStats(mask,8)
    ids=[i for i in range(1,num) if st[i,4]>500]
    mask=np.isin(lab,ids).astype(np.uint8)*255
    return im,mask

def props(im,src,n):
    extra={}
    if 849<=n<862:
        gen,alpha=prop_layer('rabbit');m=hat_motion(src,855,n,(240,760,1260,1080))
        gen=c.warp(gen,m);alpha=c.warp(alpha,m,True)
        # Erase original hat silhouette, restoring foreground rabbit/bubbles last.
        region=c.rect((200,710,1400,1080))
        old=(c.source_nonbg(src,f.color(src))&(region>0)).astype(np.uint8)*255
        area=c.dilate(old|alpha,5)
        out=im.copy();out[area>0]=f.color(src);out=c.paste(out,gen,alpha)
        out=c.paste(out,src,foreground_white(src,True))
        out=c.paste(out,src,f.letters_mask(src,[(0,700,230,1080)]))
        # Top/right rabbit and its red ear must be exact source pixels.
        out=c.paste(out,src,~region)
        return out,{'prop':'inverted-beret-rabbit','matrix':m.tolist()}
    if 1244<=n<1281:
        gen,alpha=prop_layer('held')
        oldregion=c.polygon([(45,650),(500,738),(485,845),(380,1060),(45,1060)])
        area=((c.source_nonbg(im,f.color(src))&(oldregion>0)).astype(np.uint8)*255)|alpha
        out=im.copy();out[c.dilate(area,3)>0]=f.color(src);out=c.paste(out,gen,alpha)
        hands=skin(im)&(c.rect((70,885,335,1050))>0)
        out=c.paste(out,im,c.dilate(hands.astype(np.uint8)*255,3))
        # Preserve sleeve bow and the moving original paper border.
        white=(im.min(axis=2)>215)&(im.max(axis=2)-im.min(axis=2)<25)
        num,lab,stats,_=cv2.connectedComponentsWithStats(white.astype(np.uint8),8)
        seeds=c.rect((460,875,585,1040))>0
        ids=np.unique(lab[seeds & white]);ids=[int(i) for i in ids if i]
        keep=cv2.dilate(np.isin(lab,ids).astype(np.uint8)*255,np.ones((5,5),np.uint8))
        out=c.paste(out,im,keep)
        out=c.paste(im,out,c.frame_inner(src))
        return out,{'prop':'held-beret'}
    if 1281<=n<1308:
        ref=read(1281,'source')
        region=c.rect((350,320,1450,1060))&c.frame_inner(src)
        r,g,b=src.astype(np.int16).transpose(2,0,1)
        visible=(r>18)&(r<110)&(abs(r-g)<15)&(abs(g-b)<15)&(region>0)
        if visible.sum()<1000:return im,{'prop':'hidden-by-smoke'}
        gen,alpha=prop_layer('smoke-open')
        m=hat_motion(src,1281,n,(415,700,1400,1040))
        old=((c.source_nonbg(ref,f.color(ref)))&(region>0)).astype(np.uint8)*255
        old=c.warp(old,m,True);gen=c.warp(gen,m);alpha=c.warp(alpha,m,True)
        out=im.copy();out[c.dilate(old|alpha,5)>0]=f.color(src)
        out=c.paste(out,gen,alpha)
        out=c.paste(out,src,foreground_white(src))
        out=c.paste(im,out,c.frame_inner(src))
        return out,{'prop':'inverted-beret-smoke','matrix':m.tolist(),'original_hat_visible_pixels':int(visible.sum())}
    return im,extra

def affected(n):
    return any(a<=n<b for a,b,_ in BOXES) or any(a<=n<b for a,b in [(393,444),(459,464),(1154,1174),(2785,2952),(621,704),(849,862),(1281,1308),(2472,2778),(3003,3038)])

def render(n):
    im=read(n)
    if not affected(n):return im,{'frame':n,'reused_v4':True}
    src=read(n,'source')
    out,meta=props(im,src,n)
    mask=hand_mask(out,src,n)
    out,col=colour_hands(out,mask)
    return out,dict(frame=n,reused_v4=False,**meta,**col)

def one(n):
    cv2.setNumThreads(1);dest=DEST/f'{n:05d}.png'
    if not affected(n):
        shutil.copyfile(OLD/f'frames/full-composite-v4/{n:05d}.png',dest)
        return {'frame':n,'reused_v4':True}
    out,r=render(n);Image.fromarray(out).save(dest,compress_level=3);return r

def preview(picks):
    REVIEW.mkdir(parents=True,exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for page in range((len(picks)+7)//8):
        sheet=Image.new('RGB',(1280,4*392),'#192028');d=ImageDraw.Draw(sheet)
        for j,n in enumerate(picks[page*8:page*8+8]):
            out,r=render(n);Image.fromarray(out).save(REVIEW/f'{n:05d}.png')
            (REVIEW/f'{n:05d}.json').write_text(json.dumps(r,indent=2))
            x=j%2*640;y=j//2*392;sheet.paste(Image.fromarray(out).resize((640,360)),(x,y+32))
            d.text((x+4,y+4),f'{n} | {n/24:.3f}s',font=font,fill='white')
        sheet.save(REVIEW/f'preview-{page}.jpg',quality=96)
    print('Previewed',len(picks),'frames',flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');ap.add_argument('--frames',type=int,nargs='+');ap.add_argument('--update',nargs='+');args=ap.parse_args()
    cv2.setNumThreads(1)
    if args.all or args.update:
        DEST.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
        indices=list(range(3768)) if args.all else sorted({n for spec in args.update for n in range(*map(int,spec.split(':')))})
        records=[None]*3768 if args.all else json.loads((REVIEW/'frame-verification.json').read_text())
        with ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
            for i,r in enumerate(pool.map(one,indices,chunksize=8)):
                records[r['frame']]=r
                if i%120==0:print(f'Revised frames {i}/3768',flush=True)
        (REVIEW/'frame-verification.json').write_text(json.dumps(records,indent=2))
        print('Revised frames complete',flush=True)
    else:preview(args.frames or [48,205,264,414,459,540,580,624,640,906,1040,1158,1262,1512,1608,1944,2200,2388,2520,2600,2640,2710,2880,3018,3030,849,855,861,1244,1280,1281,1290,1294,1297,1300,1307])
if __name__=='__main__':main()


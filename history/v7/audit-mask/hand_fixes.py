"""Source-owned prop masks and whole-cel hand palette, v7."""
from pathlib import Path
def coin_mask(src,v6):
    c,np,cv2=v6.c,v6.np,v6.cv2
    r,g,b=src.astype(np.int16).transpose(2,0,1)
    zone=c.rect((1120,440,1560,760))>0
    yellow=(r>230)&(g>125)&(g<220)&(b<100)&zone
    count,labels,stats,_=cv2.connectedComponentsWithStats(yellow.astype(np.uint8),8)
    ids=[j for j in range(1,count) if 10<stats[j,4]<6000]
    raw=np.isin(labels,ids).astype(np.uint8)*255
    contours,_=cv2.findContours(raw,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    mask=np.zeros((1080,1920),np.uint8)
    if not contours:return mask
    cv2.fillConvexPoly(mask,cv2.convexHull(np.concatenate(contours)),255)
    ink=(src.max(2)<170)&(c.dilate(mask,7)>0)
    return c.morph(mask|ink.astype(np.uint8)*255,3)

def source_rabbit_mask(src,v6):
    c,np,cv2=v6.c,v6.np,v6.cv2
    r,g,b=src.astype(np.int16).transpose(2,0,1)
    white=v6.f.component((src.min(2)>246).astype(np.uint8)*255,200)
    red=(r>160)&(g<125)&(b>45)&(r>1.6*g)
    count,labels,stats,_=cv2.connectedComponentsWithStats(red.astype(np.uint8),8)
    contacts=np.bincount(labels[c.dilate(white,11)>0],minlength=count)
    ids=[i for i in range(1,count) if stats[i,4]>100 and contacts[i]>20]
    body=white|np.isin(labels,ids).astype(np.uint8)*255
    ink=(src.max(2)<110)&(c.dilate(body,9)>0)
    body|=ink.astype(np.uint8)*255
    from scipy.ndimage import binary_fill_holes
    return binary_fill_holes(body>0).astype(np.uint8)*255

def alternate_register(ref,src,v6):
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

def compose_hand(out,src,n,v6,assets,asset600_crop_ref=612):
    c,np,cv2=v6.c,v6.np,v6.cv2
    ref=600 if n<603 else 603 if n<606 else 612 if n<621 else 1084
    cropref=asset600_crop_ref if ref==600 else ref
    original=Path(assets)/f'hand-{ref}.png'
    if not original.is_file():
        original=v6.PROJECT/'assets/white-sailor'/f'bare-{ref}-v3.png'
    x0,y0,x1,y1=v6.v3.CROPS[str(cropref)]
    cel=np.asarray(v6.Image.open(original).convert('RGBA').resize((x1-x0,y1-y0),v6.Image.Resampling.LANCZOS)).copy()
    rgb=np.zeros((1080,1920,3),np.uint8)
    alpha=np.zeros((1080,1920),np.uint8)
    rgb[y0:y1,x0:x1]=cel[:,:,:3];alpha[y0:y1,x0:x1]=cel[:,:,3]
    rgb,count=v6.grade(rgb,v6.skin(rgb)&(alpha>0))
    gm=v6.v3.glove(n)
    if np.count_nonzero(gm)<350:return (src.copy() if n>=1082 else out),{'hand_visible':False,'zoom_source_exact':n>=1082}
    refmask=v6.v3.glove(cropref)
    ys,xs=np.where(refmask>0)
    track=(max(0,int(xs.min())-35),max(0,int(ys.min())-35),min(1920,int(xs.max())+35),min(1080,int(ys.max())+35))
    matrix=alternate_register(c.reference(cropref),src,v6) if ref==600 else c.tracking(c.reference(cropref),src,track,n)
    rgb=cv2.warpAffine(rgb,matrix,(1920,1080),borderMode=cv2.BORDER_REPLICATE)
    alpha=cv2.warpAffine(alpha,matrix,(1920,1080),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_REPLICATE)

    region=c.rect((950,150,1870,1080)) if n<621 else c.dilate(c.warp(c.rect(tuple(v6.v3.CROPS[str(1084)])),matrix,True),18)
    erased=src.copy()
    erased[region>0]=v6.f.color(src)
    rebuilt=c.paste(erased,rgb,alpha)
    if n<621:
        keep=coin_mask(src,v6)
        rebuilt=c.paste(rebuilt,src,keep)
    else:
        keep=source_rabbit_mask(src,v6)
        rebuilt=c.paste(rebuilt,src,keep)
        lyrics=c.dilate(v6.f.letters_mask(src,[(0,0,1920,230),(1000,880,1920,1080)]),2)
        rebuilt=c.paste(rebuilt,src,lyrics)
    return c.paste(out,rebuilt,region|alpha|keep),{'hand_reference':ref,'sprite_crop_reference':cropref,'hand_pixels':count,'whole_cel_grade':True,'source_prop_full_ink_mask':True,'tracking':matrix.tolist()}

if __name__=='__main__':
    import sys,json
    sys.dont_write_bytecode=True
    old=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
    here=Path('<REVISION_WORKSPACE>/work/audit-mask')
    sys.path.insert(0,str(old.parent/'python_lib'));sys.path.insert(0,str(old/'tools'))
    import revision6_composite as v6
    v6.cv2.setNumThreads(1)
    records=[]
    for n in [1082,1084,1087,1088,1089,1090]:
        src=v6.src(n)
        prior=v6.c.read(old/f'runs/paired-v6/frames/final/{n:05d}.png')
        after,rec=compose_hand(prior,src,n,v6,here.parent/'assets-v7')
        v6.Image.fromarray(after).save(here/f'handfix-{n:05d}.png')
        rec['frame']=n;records.append(rec)
    (here/'hand-fix-records.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(records,indent=2))


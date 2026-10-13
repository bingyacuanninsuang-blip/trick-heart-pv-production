"""V10: approved gesture replay with correct handedness, localized credit, warm panel skin."""
from pathlib import Path
import sys,json,os,argparse,functools
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'work';V=WORK/'v10'
OLD=Path('<ORIGINAL_WORKSPACE>');P=OLD/'work/trick-heart-project'
sys.path[:0]=[str(OLD/'work/python_lib'),str(P/'tools')]
import revision6_composite as v6
from PIL import Image,ImageDraw,ImageFont
import numpy as np
cv=v6.cv2;c=v6.c;f=v6.f;cv.setNumThreads(1)
BASE=WORK/'v9/frames';DEST=V/'frames';REVIEW=V/'review'
RANGES=[(591,621,'23s_gesture_replay_coin'),(2702,2785,'movie_signature'),(3584,3630,'warm_face_neck_hands')]
CREDIT_TEXT=['MOVIE','GPT-6 × 虹夏天使在我家']
def affected(n):return any(a<=n<b for a,b,_ in RANGES)
def replay_ref(n):
 return 546 if n<594 else 549 if n<597 else 552 if n<600 else 555 if n<603 else 576
@functools.lru_cache(None)
def replay_layer(ref):
 # Adopt the same existing whole cel as the 23-second sequence; mirror the complete hand and sleeve.
 rgba=np.array(Image.open(V/'assets'/f'hand-{ref}.png').convert('RGBA'));rgb,alpha=rgba[:,:,:3],rgba[:,:,3]
 rgb=v6.grade(rgb,v6.skin(rgb)&(alpha>0))[0]
 return np.fliplr(rgb).copy(),np.fliplr(alpha).copy()
def hand(old,src,n):
 ref=replay_ref(n);rgb,alpha=replay_layer(ref)
 mirrored_source=np.fliplr(v6.src(ref)).copy()
 # Wrist/sleeve anchor, avoiding finger-specific fitting between different gestures.
 matrix=c.tracking(mirrored_source,src,(1220,735,1725,1080),n)
 rgb=cv.warpAffine(rgb,matrix,(1920,1080),flags=cv.INTER_LINEAR,borderMode=cv.BORDER_REPLICATE)
 alpha=cv.warpAffine(alpha,matrix,(1920,1080),flags=cv.INTER_NEAREST,borderMode=cv.BORDER_REPLICATE)
 out=old.copy();zone=c.rect((950,150,1870,1080))
 out[zone>0]=f.color(src)
 out=c.paste(out,rgb,alpha&zone)
 # The original coin instance preserves exact appearance timing and motion.
 r,g,b=src.astype(np.int16).transpose(2,0,1)
 raw=((r>225)&(g>105)&(g<225)&(b<105)&(zone>0)).astype(np.uint8)
 cc,lab,stats,_=cv.connectedComponentsWithStats(raw,8)
 ids=[i for i in range(1,cc) if 8<stats[i,4]<6000 and stats[i,1]<850]
 core=np.isin(lab,ids).astype(np.uint8)*255
 near=c.dilate(core,13)>0
 # Keep the entire source coin's dark contour, exclude the old gray glove around it.
 coin=((core>0)|(near&(src.max(2)<145))).astype(np.uint8)*255
 coin&=zone
 # Do not recover the old orange cuff or garment, which are large connected instances.
 out=c.paste(out,src,coin)
 return out,dict(gesture_reference=ref,whole_cel_mirrored=True,handedness='opposite hand retained after source cut',wrist_matrix=matrix.tolist(),coin_source_frame=n,coin_pixels=int((coin>0).sum()))
@functools.lru_cache(None)
def lettering():
 im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im)
 latin=ImageFont.truetype('C:/Windows/Fonts/times.ttf',43)
 cjk=ImageFont.truetype('C:/Windows/Fonts/simsun.ttc',48)
 d.text((198,470),'MOVIE',font=latin,fill=(255,211,151,255))
 # A single mixed-script line keeps both names together.
 x=198
 for char in CREDIT_TEXT[1]:
  font=cjk if ord(char)>255 else latin
  d.text((x,525),char,font=font,fill=(255,211,151,255))
  x+=d.textlength(char,font=font)+2
 return np.array(im)
def credit(old,src,n):
 out=old.copy()
 glyph=c.text_foreground(old,[(130,435,1225,625)])
 bg=np.median(old[410:435,750:900].reshape(-1,3),axis=0).astype(np.uint8)
 out[c.rect((150,480,840,600))>0]=bg
 rgba=lettering();m=c.tracking(v6.src(2702),src,(150,400,1100,650),n)
 out=c.paste(out,c.warp(rgba[:,:,:3],m),c.warp(rgba[:,:,3],m,True))
 # Original closing curtain owns the foreground in the final part of this shot.
 if n>=2769:
  r,g,b=src.astype(np.int16).transpose(2,0,1);raw=((r<110)&(g<70)&(b<70)).astype(np.uint8)
  cc,lab,st,_=cv.connectedComponentsWithStats(raw,8);ids=[i for i in range(1,cc) if st[i,3]>900 and st[i,1]<100]
  out=c.paste(out,old,np.isin(lab,ids).astype(np.uint8)*255)
 return out,dict(movie_signature=CREDIT_TEXT,source_curtain_occlusion=True,matrix=m.tolist())
@functools.lru_cache(None)
def warm_panel():
 im=np.array(Image.open(V/'assets/chin-neck-source.png').convert('RGB'))
 mask=v6.skin(im);values=im[mask].astype(float);light=np.maximum(values[:,1],values[:,2])
 anchor=np.percentile(light,80);depth=np.clip((anchor-light)/45,0,1)
 palette=np.array([255,232,219])[None,:]*(1-depth[:,None])+np.array([245,204,190])[None,:]*depth[:,None]
 out=im.copy();out[mask]=palette.astype(np.uint8)
 return out
def render(n):
 old=c.read(BASE/f'{n:05d}.png')
 if not affected(n):return old,dict(frame=n,reused_v9=True,changed_pixels=0)
 src=v6.src(n);rec=dict(frame=n,reused_v9=False)
 if n<621:out,meta=hand(old,src,n)
 elif n<2785:out,meta=credit(old,src,n)
 else:
  pm,bd=f.panel_mask(src,(579,316,1370,798))
  if bd is None:raise ValueError('Panel missing '+str(n))
  x,y,w,h=bd;temp=old.copy();temp[y:y+h,x:x+w]=cv.resize(warm_panel(),(w,h),interpolation=cv.INTER_LANCZOS4)
  out=c.paste(old,temp,cv.erode(pm,np.ones((3,3),np.uint8)))
  meta=dict(warm_skin_palette=[255,232,219],shared_face_neck_hands=True,panel_bounds=list(map(int,bd)))
 rec.update(meta);rec['changed_pixels']=int(np.any(old!=out,axis=2).sum())
 return out,rec
PICKS=[552,576,590,591,593,594,596,597,599,600,602,603,606,612,620,621,2701,2702,2712,2768,2770,2784,2785,3583,3584,3588,3610,3629,3630]
def preview():
 REVIEW.mkdir(parents=True,exist_ok=True);records=[]
 for n in PICKS:
  out,rec=render(n);Image.fromarray(out).save(REVIEW/f'{n:05d}.png');records.append(rec)
 for page in range((len(PICKS)+7)//8):
  sheet=Image.new('RGB',(1920,1200),'#182028');d=ImageDraw.Draw(sheet)
  for j,n in enumerate(PICKS[page*8:page*8+8]):
   x=j%2*960;y=j//2*300
   for k,folder in enumerate([BASE,REVIEW]):
    sheet.paste(Image.open(folder/f'{n:05d}.png').resize((480,270)),(x+k*480,y+30));d.text((x+k*480+4,y+5),f'v{9+k} {n} {n/24:.3f}s',fill='white')
  sheet.save(REVIEW/f'compare-{page+1}.jpg',quality=97)
 (REVIEW/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
 print('V10 previews saved',flush=True)
def assemble():
 DEST.mkdir(parents=True,exist_ok=True);records=[]
 for n in range(3768):
  dst=DEST/f'{n:05d}.png'
  if affected(n):
   if dst.exists():dst.unlink()
   out,rec=render(n);Image.fromarray(out).save(dst,compress_level=3)
  else:
   if not dst.exists():os.link(BASE/dst.name,dst)
   rec=dict(frame=n,reused_v9=True,changed_pixels=0)
  records.append(rec)
  if n%120==0:print('V10 frame',n,flush=True)
 (V/'frame-records.json').write_text(json.dumps(dict(frame_count=3768,ranges=RANGES,records=records),ensure_ascii=False,indent=2),encoding='utf-8')
 print('V10 complete sequence saved',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');args=ap.parse_args()
 assemble() if args.all else preview()

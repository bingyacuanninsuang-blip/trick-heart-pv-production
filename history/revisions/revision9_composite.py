"""V9 local repairs on immutable v8 frame sequence."""
from pathlib import Path
import sys,json,os,argparse,functools
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'work';V=WORK/'v9'
OLD=Path('<ORIGINAL_WORKSPACE>');P=OLD/'work/trick-heart-project'
sys.path[:0]=[str(OLD/'work/python_lib'),str(P/'tools')]
import revision6_composite as v6
from PIL import Image,ImageDraw
import numpy as np
cv=v6.cv2;c=v6.c;f=v6.f;cv.setNumThreads(1)
BASE=WORK/'v8/frames';DEST=V/'frames';REVIEW=V/'review';A=V/'assets'
RANGES=[(1631,1708,'cup_grip_and_black_cuff'),(1850,1930,'whole_hand_skin'),(3584,3630,'chin_neck_redraw')]
def affected(n):return any(a<=n<b for a,b,_ in RANGES)
@functools.lru_cache(None)
def cup_art():
 box=(1300,385,1560,640);x0,y0,x1,y1=box
 im=np.array(Image.open(A/'white-cup.png').convert('RGB').resize((x1-x0,y1-y0),Image.Resampling.LANCZOS))
 full=np.zeros((1080,1920,3),np.uint8);full[y0:y1,x0:x1]=im
 return full
@functools.lru_cache(None)
def panel_art():return np.array(Image.open(A/'chin-neck.png').convert('RGB'))
def flat_skin(im,mask):
 # Same pale cel palette for every finger, palm and wrist. Remove baked rectangular grades.
 out=im.copy();out[mask]=np.array([255,246,244],np.uint8)
 return out
def cups(old,src,n):
 out=old.copy()
 m=c.tracking(v6.src(1680),src,(210,210,440,620),n)
 gen=c.asset('pair-1680-v2').copy();gen[~c.generated_nonred(gen)]=f.color(src);gen=c.warp(gen,m)
 region=c.warp(c.rect((445,445,498,564)),m,True)>0
 r,g,b=out.astype(np.int16).transpose(2,0,1)
 warm=(r>90)&(g>45)&(r>g*1.25)&(g>b*1.5)
 # Only adopt black/gray cuff pixels, never the yellow cup instance.
 cloth=(gen.max(2)<190)&(gen.max(2).astype(int)-gen.min(2)<65)
 cup_instance=(gen[:,:,0]>200)&(gen[:,:,1]>150)&(gen[:,:,2]<120)
 cuff=warm&region&~cup_instance
 out[cuff]=gen[cuff]
 gen=cup_art().copy()
 own=c.rect((1360,425,1512,565))
 # Original/redraw silhouettes are owned together, preventing remnants of square fingertips.
 original=c.read(BASE/'01680.png')
 oldmask=(c.generated_nonred(original)&(own>0)).astype(np.uint8)*255
 newmask=(c.generated_nonred(gen)&(own>0)).astype(np.uint8)*255
 m2=c.tracking(v6.src(1680),src,(1450,245,1780,630),n)
 erase=c.warp(c.dilate(oldmask|newmask,3)&own,m2,True)
 rgb=c.warp(gen,m2);alpha=c.warp(newmask,m2,True)
 out[erase>0]=f.color(src);out=c.paste(out,rgb,alpha)
 # Grade the new hand as a single skin instance, leaving cup/cuff ownership intact.
 out=v6.grade(out,v6.skin(out)&(c.warp(own,m2,True)>0))[0]
 return out,{'black_cuff_yellow_pixels_removed':int(cuff.sum()),'joint_white_cup_grip':True,'matrix_black':m.tolist(),'matrix_white':m2.tolist()}
def render(n):
 old=c.read(BASE/f'{n:05d}.png')
 if not affected(n):return old,{'frame':n,'reused_v8':True,'changed_pixels':0}
 src=v6.src(n);meta={'frame':n,'reused_v8':False}
 if 1631<=n<1708:out,info=cups(old,src,n);meta.update(info)
 elif 1850<=n<1930:
  mask=v6.skin(old)&(c.rect((200,0,1470,1080))>0)
  out=flat_skin(old,mask);meta['whole_hand_skin_pixels']=int(mask.sum());meta['all_fingertips_included']=True
 else:
  pm,bd=f.panel_mask(src,(579,316,1370,798))
  if bd is None:raise ValueError('Missing original panel '+str(n))
  x,y,w,h=bd;im=cv.resize(panel_art(),(w,h),interpolation=cv.INTER_LANCZOS4)
  im=v6.grade(im,v6.skin(im))[0]
  temp=old.copy();temp[y:y+h,x:x+w]=im
  out=c.paste(old,temp,cv.erode(pm,np.ones((3,3),np.uint8)))
  meta.update(chin_neck_redrawn=True,panel_bounds=list(map(int,bd)))
 meta['changed_pixels']=int(np.any(old!=out,axis=2).sum())
 return out,meta
PICKS=[1630,1631,1656,1680,1707,1708,1849,1850,1856,1858,1863,1872,1875,1888,1929,1930,3583,3584,3588,3610,3629,3630]
def preview():
 REVIEW.mkdir(parents=True,exist_ok=True);records=[]
 for n in PICKS:
  out,rec=render(n);records.append(rec);Image.fromarray(out).save(REVIEW/f'{n:05d}.png')
 for page in range((len(PICKS)+7)//8):
  sheet=Image.new('RGB',(1920,1200),'#182028');d=ImageDraw.Draw(sheet)
  for j,n in enumerate(PICKS[page*8:page*8+8]):
   x=j%2*960;y=j//2*300
   for k,folder in enumerate([BASE,REVIEW]):
    sheet.paste(Image.open(folder/f'{n:05d}.png').resize((480,270)),(x+k*480,y+30));d.text((x+k*480+4,y+5),f'v{8+k} {n} {n/24:.3f}s',fill='white')
  sheet.save(REVIEW/f'compare-{page+1}.jpg',quality=97)
 (REVIEW/'preview-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 print('V9 keyframe previews saved at '+str(REVIEW),flush=True)
def assemble():
 DEST.mkdir(parents=True,exist_ok=True);records=[]
 for n in range(3768):
  dst=DEST/f'{n:05d}.png'
  if affected(n):
   if dst.exists():dst.unlink()
   out,rec=render(n);Image.fromarray(out).save(dst,compress_level=3)
  else:
   if not dst.exists():os.link(BASE/dst.name,dst)
   rec={'frame':n,'reused_v8':True,'changed_pixels':0}
  records.append(rec)
  if n%120==0:print('V9 frame',n,flush=True)
 (V/'frame-records.json').write_text(json.dumps({'frame_count':3768,'ranges':RANGES,'records':records},indent=2),encoding='utf-8')
 print('V9 complete frame sequence saved',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');args=ap.parse_args()
 assemble() if args.all else preview()

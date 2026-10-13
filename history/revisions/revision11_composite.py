"""V11 video layer repairs: three shared warm skin grades and complete sofa instance."""
from pathlib import Path
import sys,os,json,argparse,functools,shutil
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'work';V=WORK/'v11'
OLD=Path('<ORIGINAL_WORKSPACE>');P=OLD/'work/trick-heart-project'
sys.path[:0]=[str(OLD/'work/python_lib'),str(P/'tools')]
import revision6_composite as v6
import revision8_composite as v8
from PIL import Image,ImageDraw
import numpy as np
cv=v6.cv2;c=v6.c;f=v6.f;v4=v6.v4;cv.setNumThreads(1)
BASE=WORK/'v10/frames';DEST=V/'frames';REVIEW=V/'review';A=V/'assets'
RANGES=[(1174,1208,'warm_white_portrait'),(2314,2367,'warm_black_bouquet'),(2367,2401,'warm_black_flower_close'),(3083,3239,'complete_sleeping_sofa'),(3356,3397,'complete_awake_sofa')]
PICKS=[1174,1188,1207,2314,2328,2366,2367,2388,2400,3083,3091,3120,3168,3238,3356,3365,3376,3396]
A.mkdir(parents=True,exist_ok=True)
@functools.lru_cache(None)
def art(name):
 path=A/(name+'.png')
 if not path.exists():Image.fromarray(c.asset(name)).save(path)
 return np.array(Image.open(path).convert('RGB'))
def affected(n):return any(a<=n<b for a,b,_ in RANGES)
def warm(im,raw):
 # Use the ungraded adopted cel as skin ownership to include the complete
 # original shade. This avoids pale-mask holes around the ears and neck.
 values=raw.astype(np.float32);r,g,b=values.transpose(2,0,1)
 mask=(r>160)&(g>120)&(b>105)&(r-g>8)&(r-g<100)&(r-b>9)&(g>=b)&(g-b<40)&((r-g)>(g-b)*.75)
 mask=f.component(mask.astype(np.uint8)*255,100)>0
 light=np.maximum(g,b)
 anchor=float(np.percentile(light[mask],80))
 depth=np.clip((anchor-light)/48,0,1)
 rgb=np.float32([255,232,219])*(1-depth[:,:,None])+np.float32([244,203,188])*depth[:,:,None]
 out=im.copy();out[mask]=np.clip(rgb[mask],0,255).astype(np.uint8)
 # Only antialiased edges of the skin instances, excluding red flowers/ink.
 edge=(c.dilate(mask.astype(np.uint8)*255,3)>0)&~mask
 edge&=(r>150)&(r>g+4)&(r>b+5)&(g>b)&(r-g<100)&(g-b<40)
 delta=rgb-values
 out[edge]=np.clip(values[edge]+delta[edge]*.7,0,255).astype(np.uint8)
 return out,int(mask.sum())
def sofa(old,src,n):
 awake=n>=3356
 name='full-3120';ref=None
 if awake:
  ref=v6.v2.pose(n,(3356,3365,3376),(900,330,1190,610))
  name={3356:'sofa-front-v4',3365:'sofa-right-v4',3376:'sofa-awake-v4'}[ref]
 gen=art(name).copy();bg=f.color(v6.src(3120));gen[v4.boundary_connected(~c.generated_nonred(gen))]=bg
 # Complete sofa including both outer arms, pillows, seat and right leg.
 # Cabinet and source dog lie outside this object ownership.
 own=c.polygon([(460,550),(575,525),(585,515),(780,315),(1180,315),(1200,520),(1370,515),(1420,645),(1420,1010),(1340,1020),(1280,1070),(970,1070),(785,920),(460,870)])
 out=c.paste(old,gen,own)
 # Keep the cabinet exact. Its leftmost outline is beyond the couch right arm.
 out=c.paste(out,old,c.rect((1420,500,1920,1080)))
 # Preserve foreground dog and its outline from the unmodified source.
 r,g,b=src.astype(np.int16).transpose(2,0,1)
 animal=((r>200)&(g>190)&(b>160)&(r-g>5)&(g-b>9))|(src.max(2)<90)
 animal&=c.rect((0,795,780,1080))>0
 animal=f.component(animal.astype(np.uint8)*255,250)
 animal=c.dilate(animal,3)
 out=c.paste(out,old,animal)
 # Original captions and moving butterflies retain source timing and depth.
 background=v4.boundary_connected(~c.generated_nonred(gen)).astype(np.uint8)*255
 out=c.paste(out,src,c.butterflies(src)&c.rect((0,190,1920,830))&background)
 out=c.paste(out,src,f.decorations(src,4000)&~c.rect((780,345,1335,1080)))
 out=c.paste(out,src,f.letters_mask(src,[(0,0,1920,190),(1250,400,1920,1080)]))
 if awake:out=v4.restore_sofa_lyric(out,src)
 if n<3092:
  curtain=v4.boundary_connected((r<110)&(r>g*1.5)&(r>b*1.5)).astype(np.uint8)*255
  out=c.paste(out,src,curtain)
 # The previously approved hand palette is preserved for consistency.
 out=v6.all_hands(out,src,n)[0]
 return out,{'complete_sofa_layer':name,'pose_reference':ref,'both_sofa_sides_owned':True}
def render(n):
 old=c.read(BASE/f'{n:05d}.png');rec={'frame':n,'reused_v10':not affected(n)}
 if not affected(n):return old,{**rec,'changed_pixels':0}
 if n<2401:
  shot=v8.original_shot(n)
  if n>=2314:shot['flowers']=False
  raw=v8.scene(v6.src(n),n,shot)
  out,count=warm(old,raw);rec.update(shared_warm_skin_pixels=count,face_neck_hands_same_palette=True)
 else:
  out,info=sofa(old,v6.src(n),n);rec.update(info)
 rec['changed_pixels']=int(np.any(out!=old,axis=2).sum())
 return out,rec
def preview():
 REVIEW.mkdir(parents=True,exist_ok=True);records=[]
 for n in PICKS:
  out,rec=render(n);Image.fromarray(out).save(REVIEW/f'{n:05d}.png');records.append(rec)
 for page in range((len(PICKS)+3)//4):
  sheet=Image.new('RGB',(1920,2328),'#182028');d=ImageDraw.Draw(sheet)
  for j,n in enumerate(PICKS[page*4:page*4+4]):
   for k,folder in enumerate([BASE,REVIEW]):
    # Four rows at half size allow all representative poses on each page.
    sheet.paste(Image.open(folder/f'{n:05d}.png').resize((960,540)),(960*k,582*j+42))
    d.text((960*k+8,582*j+6),f'v{10+k} {n} {n/24:.3f}s',fill='white')
  sheet.save(REVIEW/f'compare-{page+1}.jpg',quality=97)
 (REVIEW/'records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 print('V11 preview complete',flush=True)
def assemble():
 DEST.mkdir(parents=True,exist_ok=True);records=[]
 for n in range(3768):
  dest=DEST/f'{n:05d}.png'
  if affected(n):
   if dest.exists():dest.unlink()
   out,rec=render(n);Image.fromarray(out).save(dest,compress_level=3)
  else:
   if not dest.exists():os.link(BASE/dest.name,dest)
   rec={'frame':n,'reused_v10':True,'changed_pixels':0}
  records.append(rec)
  if n%120==0:print('V11 frames',n,flush=True)
 (V/'frame-records.json').write_text(json.dumps({'version':'v11','frame_count':3768,'ranges':RANGES,'records':records},indent=2),encoding='utf-8')
 print('V11 frames complete',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');args=ap.parse_args()
 assemble() if args.all else preview()

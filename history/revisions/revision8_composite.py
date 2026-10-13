"""Isolated v8 local repairs. Original project and v7 deliverables are immutable."""
from pathlib import Path
import sys,json,shutil,argparse,functools,os
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'work';V=WORK/'v8'
OLD=Path('<ORIGINAL_WORKSPACE>')
P=OLD/'work/trick-heart-project'
sys.path[:0]=[str(OLD/'work/python_lib'),str(P/'tools')]
import revision6_composite as v6
from PIL import Image,ImageDraw
import numpy as np
cv=v6.cv2;c=v6.c;f=v6.f;v2=v6.v2
cv.setNumThreads(1)
BASE=WORK/'frames-v7/final';DEST=V/'frames';A=V/'assets';REVIEW=V/'review'
RANGES=[(393,444,'sailor_cuff'),(546,600,'hand_anatomy_and_skin'),(787,849,'rear_braid'),(1036,1059,'card_fingers'),(1091,1095,'turn_braid'),(1174,1208,'face_skin'),(1401,1543,'cup_string_close'),(1631,1708,'cup_string_pair'),(2081,2127,'rabbit_outline'),(2314,2401,'flower_hand_occlusion'),(3630,3666,'rear_bag_braid')]
G=Path('<USER_HOME>/.codex/generated_images/01a12612-48b8-76f1-a8ed-b1da38d8981f')
for name,id in [('cuff','3af9a113-9d45-453a-bf89-b13b522f48e3'),('gesture','1ac110e6-2309-4011-b485-940c1d683350')]:
 if not (A/(name+'.png')).exists():shutil.copyfile(G/('exec-'+id+'.png'),A/(name+'.png'))
@functools.lru_cache(None)
def art(name):return np.array(Image.open(A/(name+'.png')).convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS))
def affected(n):return any(a<=n<b for a,b,_ in RANGES)
def grade(out,own=None):
 mask=v6.skin(out)
 if own is not None:mask&=own>0
 return v6.grade(out,mask)[0]
def matrix(ref,n,box):return c.tracking(v6.src(ref),v6.src(n),box,n)
def scene(src,n,shot,name=None):
 shot=dict(shot)
 if shot.get('start') in v2.TRACKS:shot['track']=v2.TRACKS[shot['start']]
 original=f.layer
 if name:
  im=art(name);box=tuple(shot.get('roi',f.FULL));gm=f.key(im,box,shot.get('border',False))
  f.layer=lambda *args,**kwargs:(im.copy(),gm.copy())
 try:return f.apply_scene(src,n,shot)[0]
 finally:f.layer=original
def original_shot(n):return dict(next(s for s in f.SHOTS if s['start']<=n<s['end']))
def source_string(out,src,n):
 # Rope-only corridors. Restore original pixels including black edge and white core.
 if n<1467:polys=[[(0,565),(1210,565),(1210,660),(0,660)]]
 elif n<1543:polys=[[(950,580),(1920,580),(1920,655),(950,655)]]
 elif n<1585:polys=[[(0,1080),(540,765),(635,815),(120,1080)]]
 elif n<1631:polys=[[(1370,820),(1710,1080),(1530,1080),(1250,860)]]
 else:polys=[[(500,520),(548,520),(752,905),(693,933)],[(1395,530),(1442,530),(1250,866),(1195,885)]]
 zone=np.zeros((1080,1920),np.uint8)
 for poly in polys:zone|=c.polygon(poly)
 if n>=1631:return c.paste(out,src,zone),int(zone.sum()//255)
 r,g,b=src.astype(np.int16).transpose(2,0,1)
 neutral=(np.maximum(np.maximum(r,g),b)-np.minimum(np.minimum(r,g),b)<15)&(r>135)&(zone>0)
 core=neutral.astype(np.uint8)*255
 # Exclude broad neutral instances such as sleeves/skin; strings are slender.
 thick=cv.morphologyEx(core,cv.MORPH_OPEN,np.ones((9,9),np.uint8))
 core&=~c.dilate(thick,5)
 mask=c.dilate(core,5)&zone
 return c.paste(out,src,mask),int(mask.sum()//255)
def render(n):
 old=c.read(BASE/f'{n:05d}.png')
 if not affected(n):return old,{'frame':n,'reused_v7':True,'changed_pixels':0}
 src=v6.src(n);out=old.copy();meta={'frame':n,'reused_v7':False}
 if 393<=n<444:
  gen=art('cuff');m=matrix(393,n,(1040,550,1710,1080))
  region=c.polygon([(1205,996),(1470,799),(1598,856),(1780,1080),(1175,1080)])
  region=c.polygon([(1160,997),(1470,784),(1650,854),(1810,1080),(1160,1080)])
  # Include the full cuff contour; normalize untouched red background.
  gen=gen.copy();gen[~c.generated_nonred(gen)]=f.color(src)
  # Keep only sleeve pixels from generated artwork; preserve background and hand.
  rgb=gen.astype(np.int16);blue=(rgb[:,:,2]>rgb[:,:,0]+8)&(rgb[:,:,2]>rgb[:,:,1])
  sleeve=(rgb.min(2)>195)&(rgb.max(2)-rgb.min(2)<22)
  gm=region
  out=c.paste(out,c.warp(gen,m),c.warp(gm,m,True));meta['cuff_reconstructed']=True
 elif 546<=n<591:
  out=v6.v3.bare_hand(n,[546,549,552,555,576])[0]
  out=grade(out,c.rect((200,260,1150,1080)));meta['whole_hand_grade']=True
 elif 591<=n<600:
  gen=art('gesture');gm=f.key(gen,(950,180,1870,1080))
  m=matrix(595,n,(1230,710,1630,1080))
  out[c.rect((950,150,1870,1080))>0]=f.color(src)
  out=c.paste(out,c.warp(gen,m),c.warp(gm,m,True));out=grade(out,c.warp(gm,m,True))
  if n>=594:
   r,g,b=src.astype(np.int16).transpose(2,0,1);gold=((r>230)&(g>125)&(g<220)&(b<100)).astype(np.uint8)
   cc,lab,st,_=cv.connectedComponentsWithStats(gold,8);ids=[i for i in range(1,cc) if 10<st[i,4]<6000 and st[i,1]<850]
   out=c.paste(out,src,c.dilate(np.isin(lab,ids).astype(np.uint8)*255,2))
  meta['simplified_five_digit_pointing']=True
 elif 787<=n<849:
  ref=v2.pose(n,(787,798,804,810),(650,300,1150,850))
  name={787:'back-0787',798:'back-calm-v2',804:'back-0787',810:'back-gust-v2'}[ref]
  out=scene(src,n,dict(asset=name,ref=ref,roi=(300,170,1230,1080),track=(740,650,1100,1050)),name)
  meta['pose']=ref;meta['front_braid_hidden']=True
 elif 1036<=n<1059:
  out=scene(src,n,dict(asset='hand-1036',ref=1036,roi=(300,170,1490,1080),track=(810,230,1420,755)),'hand-1036')
  out=grade(out,c.rect((300,540,1260,1080)));meta['card_grip_redrawn']=True
 elif 1091<=n<1095:
  original=c.asset;c.asset=lambda name:art('back-1092') if name=='back-1092' else original(name)
  try:out=c.render(n)[0]
  finally:c.asset=original
  meta['front_braid_hidden']=True
 elif 1174<=n<1208:
  out=grade(scene(src,n,original_shot(n)));meta['whole_character_grade']=True
 elif 1401<=n<1708:
  out,pixels=source_string(out,src,n);meta['source_string_pixels']=pixels
 elif 2081<=n<2127:
  out=scene(src,n,dict(asset='full-2090',ref=2090,roi=(485,0,1920,1080),letters=[(0,440,850,650)],duck=False))
  r,g,b=src.astype(np.int16).transpose(2,0,1)
  white=(src.min(2)>242)&(c.rect((1100,0,1660,190))>0)
  # Recover the entire original animal's thick contour, including the ear-root joint.
  near=c.dilate(white.astype(np.uint8)*255,19)>0
  dark=src.max(2)<150
  mask=((white|(near&dark))&(c.rect((1100,0,1660,190))>0)).astype(np.uint8)*255
  mask=cv.morphologyEx(mask,cv.MORPH_CLOSE,np.ones((3,3),np.uint8))
  mask[(r>g+30)&(r>b+30)]=0
  out=c.paste(out,src,mask);meta['rabbit_contour_whole']=True
 elif 2314<=n<2401:
  shot=original_shot(n);shot['flowers']=False
  out=scene(src,n,shot);out=grade(out)
  meta['joint_flower_hand_cel']=True;meta['whole_character_grade']=True
 elif 3630<=n<3666:
  shot=original_shot(n);shot.update(asset='v8-back',roi=(680,0,1280,1080))
  out=scene(src,n,shot,'back-ending');meta['front_braid_hidden']=True
 meta['changed_pixels']=int(np.any(old!=out,axis=2).sum())
 return out,meta
PICKS=[393,420,443,546,576,591,595,599,787,798,810,848,1036,1058,1091,1092,1174,1188,1207,1401,1440,1467,1512,1543,1549,1585,1608,1631,1680,1707,2081,2090,2112,2126,2314,2328,2367,2388,2400,3630,3640,3665]
def preview():
 REVIEW.mkdir(parents=True,exist_ok=True);records=[]
 for n in PICKS:
  out,rec=render(n);Image.fromarray(out).save(REVIEW/f'{n:05d}.png');records.append(rec)
 for page in range((len(PICKS)+7)//8):
  sheet=Image.new('RGB',(1920,1200),'#182028');d=ImageDraw.Draw(sheet)
  for j,n in enumerate(PICKS[page*8:page*8+8]):
   x=j%2*960;y=j//2*300
   for k,fn in enumerate([BASE/f'{n:05d}.png',REVIEW/f'{n:05d}.png']):
    sheet.paste(Image.open(fn).resize((480,270)),(x+k*480,y+30));d.text((x+k*480+5,y+5),f'v{7+k} {n} {n/24:.2f}s',fill='white')
  sheet.save(REVIEW/f'compare-{page+1}.jpg',quality=96)
 (REVIEW/'records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 print('V8 preview complete',flush=True)
def assemble():
 DEST.mkdir(parents=True,exist_ok=True);records=[]
 for n in range(3768):
  dst=DEST/f'{n:05d}.png'
  if affected(n):
   if dst.exists():dst.unlink()
   out,rec=render(n);Image.fromarray(out).save(dst,compress_level=3)
  else:
   if not dst.exists():os.link(BASE/dst.name,dst)
   rec={'frame':n,'reused_v7':True,'changed_pixels':0}
  records.append(rec)
  if n%120==0:print('V8 frame',n,flush=True)
 (V/'frame-records.json').write_text(json.dumps({'frame_count':3768,'ranges':RANGES,'records':records},indent=2),encoding='utf-8')
 print('V8 frames complete',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');args=ap.parse_args()
 assemble() if args.all else preview()

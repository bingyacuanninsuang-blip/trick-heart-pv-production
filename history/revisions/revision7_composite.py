"""V7 localized PV revision. Saved v6 frames are immutable read-only inputs."""
from pathlib import Path
import sys,os,json,shutil,hashlib,argparse,importlib.util
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work'
OLD=Path('<ORIGINAL_WORKSPACE>')
PROJECT=OLD/'work/trick-heart-project'
sys.path.insert(0,str(OLD/'work/python_lib'))
sys.path.insert(0,str(PROJECT/'tools'))
import revision6_composite as v6
from PIL import Image,ImageDraw,ImageFont
import numpy as np
v6.cv2.setNumThreads(1)
DEST=WORK/'frames-v7/final'
REVIEW=WORK/'v7-review'
ASSETS=WORK/'assets-v7'
BASE=PROJECT/'runs/paired-v6/frames/final'
RANGES=[(600,621,'coin_hand'),(1082,1091,'rabbit_hand'),(1401,1467,'complete_ahoge'),(2139,2169,'blow_action'),(2367,2401,'face_hand_skin'),(3584,3630,'simple_braid'),(3630,3666,'back_hair_placement')]
def load_module(name,file):
 spec=importlib.util.spec_from_file_location(name,file)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod
hands=load_module('hand_fixes',WORK/'audit-mask/hand_fixes.py')
masks=load_module('mask_fixes',WORK/'audit-mask/mask_fixes.py')
motion=load_module('motion_patch',WORK/'audit-motion/motion_patch.py')
def affected(n):return any(a<=n<b for a,b,_ in RANGES)
def render(n):
 prior=v6.c.read(BASE/f'{n:05d}.png')
 rec={'frame':n,'version':'v7','reused_v6':not affected(n)}
 if not affected(n):return prior,rec
 src=v6.src(n)
 if 600<=n<621 or 1082<=n<1091:
  out,meta=hands.compose_hand(prior,src,n,v6,ASSETS)
 elif 1401<=n<1467:
  out,meta=masks.restore_ahoge(prior,src,n,v6)
 elif 2367<=n<2401:
  out,meta=masks.unify_face_hand_skin(prior,src,n,v6)
 else:out,meta=motion.render(n,prior,src,v6)
 rec.update(meta)
 rec['changed_pixels']=int(np.any(prior!=out,axis=2).sum())
 return out,rec
def preview():
 REVIEW.mkdir(parents=True,exist_ok=True)
 picks=[599,600,602,603,605,606,612,620,621,1081,1082,1084,1088,1090,1091,1401,1440,1466,2146,2147,2148,2150,2151,2154,2156,2157,2166,2367,2388,2400,3584,3588,3629,3630,3640,3665]
 records=[]
 for i,n in enumerate(picks):
  out,rec=render(n);records.append(rec)
  Image.fromarray(out).save(REVIEW/f'{n:05d}.png',compress_level=3)
  if i%6==0:print('Preview',i,'/',len(picks),flush=True)
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
 for page in range((len(picks)+7)//8):
  sheet=Image.new('RGB',(1920,1200),'#172029');d=ImageDraw.Draw(sheet)
  for j,n in enumerate(picks[page*8:page*8+8]):
   x=(j%2)*960;y=(j//2)*300
   old=Image.open(BASE/f'{n:05d}.png').convert('RGB')
   new=Image.open(REVIEW/f'{n:05d}.png').convert('RGB')
   sheet.paste(old.resize((480,270)),(x,y+30))
   sheet.paste(new.resize((480,270)),(x+480,y+30))
   d.text((x+6,y+3),f'v6 {n} {n/24:.3f}s',font=font,fill='white')
   d.text((x+486,y+3),f'v7 {n} {n/24:.3f}s',font=font,fill='white')
  sheet.save(REVIEW/f'compare-{page+1}.jpg',quality=97)
 (REVIEW/'preview-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
def all_frames():
 DEST.mkdir(parents=True,exist_ok=True)
 records=[]
 for n in range(3768):
  dest=DEST/f'{n:05d}.png'
  if affected(n):
   out,rec=render(n)
   Image.fromarray(out).save(dest,compress_level=3)
  else:
   shutil.copyfile(BASE/dest.name,dest)
   rec={'frame':n,'version':'v7','reused_v6':True,'changed_pixels':0}
  records.append(rec)
  if n%120==0:print('V7 frame',n,'/3768',flush=True)
 manifest={'version':'v7','frame_count':3768,'records':records,'changed_intervals':[{'start':a,'end':b,'label':label} for a,b,label in RANGES]}
 (WORK/'v7-frame-records.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print('V7 full frame assembly complete',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');ap.add_argument('--preview',action='store_true')
 args=ap.parse_args()
 all_frames() if args.all else preview()

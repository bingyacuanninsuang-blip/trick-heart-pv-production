import os,sys,json
from pathlib import Path
p=Path(r'<ORIGINAL_WORKSPACE>/work/trick-heart-project')
sys.path.insert(0,str(p.parent/'python_lib'))
sys.path.insert(0,str(p/'tools'))
os.environ['PV_RUN_ROOT']=str(p/'runs/white-sailor')
os.environ['PV_ASSET_ROOT']=str(p/'assets/white-sailor')
os.environ['PV_SOURCE_VIDEO']=str(p/'research/source-1080.mp4')
os.environ['PV_CHARACTER_PROFILE']='paired-characters'
os.environ['ROXY_FFMPEG']='ffmpeg'
import revision4_juggle as v4
from PIL import Image,ImageDraw
import numpy as np,cv2
cv2.setNumThreads(1)
dest=p/'review/juggle-composite';dest.mkdir(parents=True,exist_ok=True)
sheet=Image.new('RGB',(1920,4*300),(25,26,31));d=ImageDraw.Draw(sheet)
rows=[]
for i,n in enumerate(v4.POSE_REFS):
 src=v4.c.reference(n)
 out,meta=v4.render(src,n)
 Image.fromarray(out).save(dest/f'{n:05d}.png')
 x=(i%4)*480;y=(i//4)*300
 sheet.paste(Image.fromarray(out).resize((480,270)),(x,y+30))
 d.text((x+5,y+7),f'{n} / {n/24:.3f}s',fill='white')
 rows.append(dict(frame=n,**meta))
sheet.save(p/'review/juggle-composite-contact.jpg',quality=95)
(p/'review/juggle-composite-check.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Rendered juggling references:',len(rows))

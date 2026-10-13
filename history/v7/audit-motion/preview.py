from pathlib import Path
import sys,os,json
sys.dont_write_bytecode=True
ROOT=Path(r'<REVISION_WORKSPACE>')
OLD=Path(r'<ORIGINAL_WORKSPACE>/work/trick-heart-project')
sys.path[:0]=[str(OLD/'tools'),str(OLD.parent/'python_lib'),str(ROOT/'work/audit-motion')]
import revision6_composite as v6
import motion_patch as p
from PIL import Image,ImageDraw
v6.cv2.setNumThreads(1)
dst=ROOT/'work/audit-motion/preview';dst.mkdir(parents=True,exist_ok=True)
picks=[2139,2146,2147,2150,2151,2154,2156,2157,2168,3584,3588,3600,3629,3630,3640,3665]
records=[]
for k,n in enumerate(picks):
    before=v6.c.read(OLD/'runs/paired-v6/frames/final'/f'{n:05d}.png')
    after,rec=p.render(n,before,v6.src(n),v6)
    Image.fromarray(after).save(dst/f'{n:05d}.png')
    records.append(dict(frame=n,**rec))
    sheet=Image.new('RGB',(1280,394),'#172029');d=ImageDraw.Draw(sheet)
    sheet.paste(Image.fromarray(before).resize((640,360)),(0,34))
    sheet.paste(Image.fromarray(after).resize((640,360)),(640,34))
    d.text((5,8),f'v6 {n}',fill='white');d.text((645,8),f'v7 {n}',fill='white')
    sheet.save(dst/f'compare-{n:05d}.jpg',quality=96)
    print(n,rec,flush=True)
(dst/'records.json').write_text(json.dumps(records,indent=2))

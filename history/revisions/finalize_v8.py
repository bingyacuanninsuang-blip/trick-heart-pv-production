from pathlib import Path
import sys,json,hashlib,subprocess,zipfile,time
sys.dont_write_bytecode=True
import encode_v8 as e
from PIL import Image,ImageDraw,ImageFont
ROOT=e.ROOT;V=ROOT/'work/v8';OUT=ROOT/'outputs'
SEGMENTS=[(393,417,'Sailor cuff'),(591,605,'Hand shape and skin'),(787,819,'Rear hair wind poses'),(1036,1059,'Card grip'),(1091,1095,'Rear turn'),(1174,1208,'Face skin'),(1428,1452,'Cup string close'),(1467,1491,'Cup string close'),(1631,1708,'Cup strings wide'),(2081,2127,'Rabbit outline'),(2314,2340,'Bouquet grip'),(2367,2391,'Flower hand overlap'),(3630,3666,'Rear ending')]
def review():
 dest=OUT/'v8-revision-review.mp4'
 args=[e.FFMPEG,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x392','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-crf','17','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',dest]
 p=subprocess.Popen([str(a) for a in args],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);count=0
 for a,b,label in SEGMENTS:
  for speed,repeats in [('1x',1),('0.5x',2)]:
   for n in range(a,b):
    panel=Image.new('RGB',(1280,392),'#182028');d=ImageDraw.Draw(panel)
    for k,folder in enumerate([e.V7_FRAMES,e.FRAMES]):
     with Image.open(folder/f'{n:05d}.png') as im:panel.paste(im.convert('RGB').resize((640,360)),(640*k,32))
     d.text((8+640*k,7),f'v{7+k} | {label} | {n/24:.2f}s | {speed}',fill='white',font=font)
    blob=panel.tobytes()
    for _ in range(repeats):p.stdin.write(blob);count+=1
  print('Reviewed segment',label,flush=True)
 p.stdin.close();err=p.stderr.read();code=p.wait()
 if code:raise RuntimeError(err.decode(errors='replace'))
 return {'path':str(dest),'sha256':e.digest(dest),'frames':count,'duration':count/24,'audio':'silent','layout':'v7 left / v8 right','playback':['normal','half-speed'],'segments':SEGMENTS}
def package(review):
 verification=e.read(OUT/'v8-verification.json')
 assets=[]
 for p in sorted((V/'assets').glob('*.png')):assets.append({'path':str(p),'sha256':e.digest(p),'dimensions':Image.open(p).size})
 prompts=e.read(V/'imagegen-prompts.json');prompts['jobs']+=e.read(V/'extra-prompts.json')
 (OUT/'v8-imagegen-prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
 record={'version':'v8','output':verification['output'],'sha256':verification['sha256'],'technical':verification['technical'],'audio_unchanged':verification['audio_unchanged'],'v7_preserved':verification['read_only_inputs_unchanged'],'assets':assets,'art_method':'built-in image_gen image editing; selected originals retained','compositing':'source tracking; instance-aware masks; original timeline and typography preserved','review':review,'verification':str(OUT/'v8-verification.json'),'prompts':str(OUT/'v8-imagegen-prompts.json'),'manual_visual_review':'42 representative lossless keyframes, enlarged problem crops and final decoded comparison sheets. Automated full decode; no claim of full manual playback.','created_epoch':time.time()}
 e.write(OUT/'v8-production-record.json',record)
 text="""# V8 revision package
The full delivery is outputs/trick-heart-two-character-pv-v8.mp4. The v7 delivery remains intact.
Corrections: sailor cuff; early pointing hand and whole-hand skin; rear braid hidden in wind/turn/ending shots; rounded card grip; whole-character face/hand palette; original continuous cup strings; complete rabbit ear-root contour; bouquet hand/stem ownership.
Artwork used built-in image_gen image editing. Exact prompts and selected image hashes are recorded.
This package preserves the v8 patch scripts, generated assets, review evidence and verification. Rebuilding the complete film also requires the existing v7 PNG frame sequence and the read-only pv-pv-4 source project at the paths recorded in the scripts. It is an incremental recoverable revision package, not a standalone copy of the source project.
Run work/revision8_composite.py --all, then work/encode_v8.py --encode in the workspace using the configured Python dependencies. Review work/v8/review before export.
"""
 (V/'README.md').write_text(text,encoding='utf-8')
 files=[ROOT/'work/revision8_composite.py',ROOT/'work/encode_v8.py',Path(__file__),V/'README.md',V/'frame-records.json',V/'imagegen-prompts.json',V/'extra-prompts.json',OUT/'v8-imagegen-prompts.json',OUT/'v8-production-record.json',OUT/'v8-verification.json',ROOT/'work/v8-encoding-baseline.json',ROOT/'work/v8-frame-audit.json',ROOT/'work/v8-audio-remux-record.json']
 files+=list((V/'assets').glob('*'))+list((V/'review').glob('compare-*.jpg'))+list(OUT.glob('v8-comparison-*.jpg'))
 zip_path=OUT/'v8-revision-project.zip'
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:
   if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
 e.write(OUT/'v8-package-record.json',{'path':str(zip_path),'sha256':e.digest(zip_path),'bytes':zip_path.stat().st_size,'file_count':len(files),'incremental_package':True})
 print(json.dumps({'video':verification['output'],'review':review['path'],'package':str(zip_path)},ensure_ascii=False),flush=True)
if __name__=='__main__':package(review())

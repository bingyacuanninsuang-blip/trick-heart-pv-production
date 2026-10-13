from pathlib import Path
import sys,json,subprocess,zipfile,time
sys.dont_write_bytecode=True
import encode_v11 as e
from PIL import Image,ImageDraw,ImageFont
ROOT=e.ROOT;V=ROOT/'work/v11';OUT=ROOT/'outputs'
SEGMENTS=[(1173,1209,'White portrait skin'),(2313,2402,'Black bouquet and close-up skin'),(3082,3094,'Sofa opening curtain'),(3144,3204,'Complete sofa sides'),(3355,3398,'Sofa awake poses')]
def review():
 dest=OUT/'v11-revision-review.mp4'
 args=[e.FFMPEG,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x392','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-crf','17','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',dest]
 p=subprocess.Popen([str(a) for a in args],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);count=0
 for a,b,label in SEGMENTS:
  for speed,repeats in [('1x',1),('0.5x',2)]:
   for n in range(a,b):
    panel=Image.new('RGB',(1280,392),'#182028');d=ImageDraw.Draw(panel)
    for k,folder in enumerate([e.V10_FRAMES,e.FRAMES]):
     with Image.open(folder/f'{n:05d}.png') as im:panel.paste(im.convert('RGB').resize((640,360)),(640*k,32))
     d.text((8+640*k,7),f'v{10+k} | {label} | {n/24:.2f}s | {speed}',fill='white',font=font)
    for _ in range(repeats):p.stdin.write(panel.tobytes());count+=1
  print('Reviewed',label,flush=True)
 p.stdin.close();err=p.stderr.read();code=p.wait()
 if code:raise RuntimeError(err.decode(errors='replace'))
 e.command([e.FFMPEG,'-v','error','-xerror','-i',dest,'-f','null','-'])
 return {'path':str(dest),'sha256':e.digest(dest),'frames':count,'duration':count/24,'audio':'silent','layout':'v10 left / v11 right','playback':['normal','half-speed'],'segments':SEGMENTS,'strict_complete_decode_passed':True}
def package(review):
 ver=e.read(OUT/'v11-verification.json')
 assets=[{'path':str(p),'sha256':e.digest(p),'dimensions':Image.open(p).size} for p in sorted((V/'assets').glob('*.png'))]
 rec={'version':'v11','video':ver['output'],'sha256':ver['sha256'],'audio_unchanged':True,'v10_preserved':True,'assets':assets,'art_method':'Existing adopted image_gen cels reused; video compositor palette correction and complete sofa ownership masks. No new art generation.','palette':{'base':[255,232,219],'shade':[244,203,188]},'changes':['Three specified face shots, neck and hands graded to the same warm palette. Original blush and shadow retained.','Complete sleeping and awake sofa cels cover both arms, pillows, seat and right leg. Source cabinet, dog, captions, butterfly movement and curtain depth preserved.'],'review':review,'validation':str(OUT/'v11-verification.json'),'manual_visual_review':'Representative lossless frames, enlarged neck/couch details and final decoded keyframes checked. Full automatic decode; no claim of complete manual playback.','created_epoch':time.time()}
 e.write(OUT/'v11-production-record.json',rec)
 readme="""# V11 incremental revision
Delivery: outputs/trick-heart-two-character-pv-v11.mp4.
The three requested close-up scenes use a natural shared warm palette for face, neck and hands, with original blush and shadows. Both sides of the sleeping and awake sofa use complete adopted cels, removing rectangular furniture cutoffs.
No new image generation; existing approved image_gen artwork reused. The source soundtrack and frame timeline are preserved. Earlier deliveries remain untouched.
To rebuild, run work/revision11_composite.py --all and work/encode_v11.py --encode with existing runtime dependencies.
This is an incremental recoverable package. Rebuilding also needs work/v10/frames and the read-only pv-pv-4 source project at the paths recorded in scripts.
"""
 (V/'README.md').write_text(readme,encoding='utf-8')
 files=[ROOT/'work/check_v11_final.py',OUT/'v11-curtain-check.jpg',ROOT/'work/revision8_composite.py',ROOT/'work/revision11_composite.py',ROOT/'work/encode_v11.py',Path(__file__),V/'README.md',V/'frame-records.json',OUT/'v11-production-record.json',OUT/'v11-verification.json',ROOT/'work/v11-encoding-baseline.json',ROOT/'work/v11-frame-audit.json',ROOT/'work/v11-audio-remux-record.json']
 files+=list((V/'assets').glob('*.png'))+list(OUT.glob('v11-comparison-*.jpg'))
 dest=OUT/'v11-revision-project.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:
   if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
 with zipfile.ZipFile(dest) as z:
  if z.testzip():raise ValueError('Package CRC failed')
 e.write(OUT/'v11-package-record.json',{'path':str(dest),'sha256':e.digest(dest),'bytes':dest.stat().st_size,'incremental_package':True,'crc_check_passed':True})
 print(json.dumps({'video':ver['output'],'review':review['path'],'package':str(dest)},ensure_ascii=False),flush=True)
if __name__=='__main__':package(review())

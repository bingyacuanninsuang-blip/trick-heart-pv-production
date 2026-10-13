"""Portable PNG-sequence exporter with complete original-audio remux and strict checks."""
from pathlib import Path
import argparse,hashlib,json,subprocess,re,shutil,tempfile
from PIL import Image
def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf-8',errors='replace')
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
 return p
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()
def audio_hash(ffmpeg,path):
 return run([ffmpeg,'-v','error','-i',path,'-map','0:a:0','-vn','-c:a','copy','-f','hash','-hash','sha256','pipe:1']).stdout.strip()
def export(frames,audio,output,fps,count,ffmpeg):
 frames,audio,output=map(lambda p:Path(p).resolve(),[frames,audio,output])
 if output.exists():raise FileExistsError('Refusing to overwrite '+str(output))
 if not audio.is_file():raise FileNotFoundError(audio)
 sizes=set()
 for n in range(count):
  path=frames/f'{n:05d}.png'
  if not path.is_file():raise FileNotFoundError(path)
  with Image.open(path) as image:sizes.add(image.size)
 if len(sizes)!=1:raise ValueError('Frame geometry is inconsistent')
 size=sizes.pop()
 if size[0]%2 or size[1]%2:raise ValueError('YUV420P requires even frame dimensions')
 output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='pv-export-',dir=output.parent) as td:
  td=Path(td);video=td/'video.mp4';full=td/'complete.mp4'
  run([ffmpeg,'-v','error','-y','-framerate',fps,'-start_number','0','-i',frames/'%05d.png','-frames:v',count,'-an','-c:v','libx264','-crf','15','-preset','medium','-pix_fmt','yuv420p',video])
  run([ffmpeg,'-v','error','-y','-i',video,'-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-movflags','+faststart',full])
  check=run([ffmpeg,'-v','error','-xerror','-nostats','-progress','pipe:1','-i',full,'-map','0:v:0','-map','0:a:0','-f','null','-'])
  decoded=re.findall(r'^frame=(\d+)',check.stdout,re.M)
  if not decoded or int(decoded[-1])!=count:raise ValueError('Final decoded frame count differs')
  before,after=audio_hash(ffmpeg,audio),audio_hash(ffmpeg,full)
  if before!=after:raise ValueError('Original compressed audio was not preserved')
  record={'output':output.name,'sha256':digest(full),'frames':count,'fps':fps,'video_duration':count/fps,'width':size[0],'height':size[1],'strict_decode_passed':True,'audio_copy_hash':after,'audio_unchanged':True}
  full.replace(output)
  output.with_suffix('.verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
 return record
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--frames',required=True);ap.add_argument('--audio',required=True);ap.add_argument('--output',required=True);ap.add_argument('--fps',type=float,required=True);ap.add_argument('--count',type=int,required=True);ap.add_argument('--ffmpeg',default=shutil.which('ffmpeg'))
 a=ap.parse_args()
 if not a.ffmpeg:ap.error('Provide --ffmpeg or put FFmpeg on PATH')
 if a.fps<=0 or a.count<=0:ap.error('fps and count must be positive')
 print(json.dumps(export(a.frames,a.audio,a.output,a.fps,a.count,a.ffmpeg),indent=2))

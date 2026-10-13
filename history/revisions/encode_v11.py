"""Isolated v11 encoding, full timeline/audio checks and decoded-file comparison evidence."""
from pathlib import Path
import argparse,hashlib,json,math,os,re,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work'
OUT=ROOT/'outputs'
OLD=Path('<ORIGINAL_WORKSPACE>')
PROJECT=OLD/'work/trick-heart-project'
sys.path.insert(0,str(OLD/'work/python_lib'))
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
import cv2
import numpy as np
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
FRAMES=WORK/'v11/frames'
V10_FRAMES=WORK/'v10/frames'
SOURCE=PROJECT/'research/source-1080.mp4'
AUDIO=PROJECT/'runs/white-sailor/research/source-audio.m4s'
V10=OUT/'trick-heart-two-character-pv-v10.mp4'
DEST=OUT/'trick-heart-two-character-pv-v11.mp4'
BASELINE=WORK/'v11-encoding-baseline.json'
MANIFEST=WORK/'v11/frame-records.json'
PICKS=[1174,1188,1207,2314,2328,2366,2367,2388,2400,3120,3168,3396]
EXPECTED={'width':1920,'height':1080,'fps':24.0,'frames':3768,'duration':157.0}
from revision11_composite import RANGES
REQUIRED=RANGES

def log(s):print(s,flush=True)
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def command(args):
 p=subprocess.run([str(a) for a in args],capture_output=True,text=True,encoding='utf-8',errors='replace')
 if p.returncode:raise RuntimeError('Command failed: '+p.stderr[-4000:])
 return p
def audio_hash(p,codec):
 return command([FFMPEG,'-v','error','-i',p,'-map','0:a:0','-vn','-c:a',codec,'-f','hash','-hash','sha256','pipe:1']).stdout.strip()
def prepare():
 prior=read(OUT/'v10-verification.json')
 paths={'source':SOURCE,'audio':AUDIO,'v10':V10}
 data={'inputs':{k:{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for k,p in paths.items()},
       'expected':EXPECTED,'ffmpeg':FFMPEG,'old_project_read_only':True,'baseline_created_epoch':time.time()}
 if data['inputs']['v10']['sha256']!=prior['sha256']:raise ValueError('V10 differs from its delivery record')
 if BASELINE.exists():
  previous=read(BASELINE)
  if previous['inputs']!=data['inputs']:raise ValueError('Original inputs changed after baseline capture')
 else:write(BASELINE,data)
 log('Isolated v11 input baseline ready; no encoding started.')
 return data
def assert_inputs():
 b=read(BASELINE)
 for name,record in b['inputs'].items():
  if digest(Path(record['path']))!=record['sha256']:raise ValueError('Read-only input changed: '+name)
 return b
def intervals(numbers):
 result=[]
 for n in sorted(numbers):
  if result and result[-1]['end']==n:result[-1]['end']=n+1
  else:result.append({'start':n,'end':n+1})
 return result
def declared_intervals(data,records):
 items=data.get('ranges') or data.get('changed_intervals') or data.get('affected_intervals') or data.get('intervals') if isinstance(data,dict) else None
 if items:
  result=[]
  for item in items:
   if isinstance(item,(list,tuple)):s,e=item[:2]
   else:
    s=item.get('start',item.get('start_frame'))
    e=item.get('end',item.get('end_frame_exclusive'))
   if s is None or e is None:raise ValueError('Manifest interval requires start and end')
   s,e=int(s),int(e)
   if not 0<=s<e<=3768:raise ValueError('Invalid declared interval')
   result.append((s,e))
  return result
 allowed=[]
 for r in records:
  if r.get('changed') or r.get('revised') or r.get('reused_v10') is False:allowed.append(int(r['frame']))
 return [(x['start'],x['end']) for x in intervals(allowed)] if allowed else None
def frame_check():
 data=read(MANIFEST)
 records=data if isinstance(data,list) else data.get('records',data.get('frames'))
 if not isinstance(records,list) or [int(r['frame']) for r in records]!=list(range(3768)):
  raise ValueError('Manifest must record all 3768 frames in ascending order')
 actual_names={p.name for p in FRAMES.glob('*.png')}
 expected_names={f'{i:05d}.png' for i in range(3768)}
 if actual_names!=expected_names:raise ValueError('Final PNG sequence has missing or extra names')
 allowed_intervals=declared_intervals(data,records)
 if allowed_intervals is None:raise ValueError('Manifest must declare changed_intervals or per-frame changed/reused_v10 state')
 allowed={n for s,e in allowed_intervals for n in range(s,e)}
 changed=[];hash_changes=[];same=0;checks=[]
 for n in range(3768):
  p=FRAMES/f'{n:05d}.png';previous=V10_FRAMES/p.name
  a,b=digest(p),digest(previous)
  if a==b:
   same+=1
  else:
   hash_changes.append(n)
   with Image.open(p) as new,Image.open(previous) as old:
    if new.size!=(1920,1080) or old.size!=(1920,1080):raise ValueError('Wrong frame geometry '+str(n))
    if not np.array_equal(np.asarray(new.convert('RGB')),np.asarray(old.convert('RGB'))):changed.append(n)
  record=records[n]
  expected_sha=record.get('sha256') or record.get('output_sha256')
  if expected_sha and expected_sha!=a:raise ValueError('PNG differs from final manifest at '+str(n))
  if n%240==0:log(f'Frame audit {n}/3768')
  checks.append({'frame':n,'sha256':a,'reused_v10_bytes':a==b})
 outside=sorted(set(changed)-allowed)
 if outside:raise ValueError('Pixels changed outside declared intervals: '+str(outside[:30]))
 if not changed:raise ValueError('No visual corrections present')
 coverage=[]
 for s,e,label in REQUIRED:
  affected=sorted(set(changed)&set(range(s,e)))
  if not affected:raise ValueError('Required correction has no changed frames: '+label)
  coverage.append({'label':label,'start':s,'end':e,'changed_frames':len(affected)})
 protected=[(849,862),(1244,1281),(1281,1308)]
 protected_changes={f'{s}:{e}':sorted(set(changed)&set(range(s,e))) for s,e in protected}
 if any(protected_changes.values()):raise ValueError('Previously approved hat segment changed')
 result={'frame_count':3768,'reused_v10_byte_identical':same,'pixel_changed_count':len(changed),
         'pixel_changed_intervals':intervals(changed),'file_hash_changed_count':len(hash_changes),
         'declared_intervals':[{'start':s,'end':e} for s,e in allowed_intervals],
         'required_corrections':coverage,'outside_declared_changes':outside,
         'protected_hat_segments_unchanged':True,'manifest_sha256':digest(MANIFEST)}
 write(WORK/'v11-frame-audit.json',{'summary':result,'records':checks})
 log(f'Frame audit passed: {len(changed)} pixel-changed, {same} byte-identical reused v10 frames.')
 return result
def encode():
 tmp=WORK/'trick-heart-two-character-pv-v11.rendering.mp4'
 if tmp.exists():tmp=tmp.with_name(tmp.stem+'-'+str(time.time_ns())+tmp.suffix)
 args=[FFMPEG,'-v','error','-y','-nostats','-progress','pipe:1','-framerate','24','-start_number','0',
       '-i',FRAMES/'%05d.png','-i',AUDIO,'-map','0:v:0','-map','1:a:0','-frames:v','3768',
       '-c:v','libx264','-crf','15','-preset','medium','-pix_fmt','yuv420p','-c:a','copy',
       '-movflags','+faststart',tmp]
 stderr=WORK/'v11-encode-stderr.txt'
 with stderr.open('w',encoding='utf-8') as err:
  p=subprocess.Popen([str(x) for x in args],stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',errors='replace')
  last=-240
  for line in p.stdout:
   if line.startswith('frame='):
    n=int(line.split('=')[1])
    if n-last>=240:log(f'Encoded frames {n}/3768');last=n
  code=p.wait()
 if code:raise RuntimeError(stderr.read_text(encoding='utf-8')[-4000:])
 return tmp
def audio_packet_summary(path):
 result=command([FFMPEG,'-v','error','-i',path,'-map','0:a:0','-vn','-c:a','copy',
                 '-f','framehash','-hash','sha256','pipe:1'])
 rows=[line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith('#')]
 return {'packet_count':len(rows),'first_packet':rows[0] if rows else None,
         'last_packet':rows[-1] if rows else None,
         'packet_hash_list_sha256':hashlib.sha256(result.stdout.encode('utf-8')).hexdigest()}
def remux_full_audio(encoded_video):
 if not encoded_video.is_file():raise FileNotFoundError('Encoded video to resume is missing: '+str(encoded_video))
 target=WORK/'trick-heart-two-character-pv-v11.remuxed.mp4'
 if target.exists():target=target.with_name(target.stem+'-'+str(time.time_ns())+target.suffix)
 log('Copying existing encoded video with the complete original audio; no video re-encoding.')
 before=audio_packet_summary(encoded_video);original=audio_packet_summary(AUDIO)
 before_hash=audio_hash(encoded_video,'copy');original_hash=audio_hash(AUDIO,'copy')
 args=[FFMPEG,'-v','error','-n','-i',encoded_video,'-i',AUDIO,'-map','0:v:0','-map','1:a:0',
       '-c:v','copy','-c:a','copy','-movflags','+faststart',target]
 command(args)
 after=audio_packet_summary(target);after_hash=audio_hash(target,'copy')
 if after_hash!=original_hash:raise ValueError('Complete-audio remux hash still differs')
 truncated=before['packet_count']<original['packet_count']
 record={'encoded_video_input':str(encoded_video),'encoded_video_input_preserved':True,
         'remuxed_path_before_delivery':str(target),'video_reencoded':False,
         'audio_source':str(AUDIO),'frames_v_or_shortest_used_in_remux':False,
         'before_audio_packets':before,'source_audio_packets':original,'after_audio_packets':after,
         'before_audio_copy_hash':before_hash,'source_audio_copy_hash':original_hash,
         'after_audio_copy_hash':after_hash,'original_audio_copy_hash_restored':True,
         'root_cause_assessment':('Initial encode -frames:v reached the video limit before the last audio packets were muxed; fewer packets are observed and complete original hash is restored by unlimited remux.'
                                 if truncated else 'Initial encoded audio hash differed. Unlimited stream-copy remux restored original audio; packet count alone did not establish truncation.'),
         'audio_packet_truncation_observed':truncated,
         'remux_command':[str(x) for x in args]}
 write(WORK/'v11-audio-remux-record.json',record)
 return target,record
def probe_and_decode(p):
 cap=cv2.VideoCapture(str(p))
 if not cap.isOpened():raise ValueError('Cannot open encoded video')
 info={'width':int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),'height':int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
       'fps':cap.get(cv2.CAP_PROP_FPS)}
 cap.release()
 check=command([FFMPEG,'-hide_banner','-v','info','-xerror','-nostats','-progress','pipe:1',
                '-i',p,'-map','0:v:0','-map','0:a:0','-f','null','-'])
 counts=re.findall(r'^frame=(\d+)',check.stdout,re.M)
 if not counts:raise ValueError('Complete decode returned no frames')
 info['frames']=int(counts[-1]);info['duration']=info['frames']/info['fps']
 info['audio']={'description':next((s.strip() for s in check.stderr.splitlines() if 'Audio:' in s),None)}
 if not info['audio']['description']:raise ValueError('Output has no audio')
 for key,val in EXPECTED.items():
  if abs(info[key]-val)>0.0001:raise ValueError(f'Output {key} differs: {info[key]} != {val}')
 info['method']='opencv-geometry-plus-strict-complete-ffmpeg-decode'
 return info
def decoded_frames(p,label):
 folder=WORK/'v11-decoded-qa'/label;folder.mkdir(parents=True,exist_ok=True)
 expression='+'.join(f'eq(n,{n})' for n in PICKS)
 command([FFMPEG,'-v','error','-y','-i',p,'-map','0:v:0','-an','-vf',"select='"+expression+"'",
          '-fps_mode','passthrough','-frames:v',str(len(PICKS)),'-start_number','0',folder/'%03d.png'])
 files=[folder/f'{i:03d}.png' for i in range(len(PICKS))]
 if not all(x.exists() for x in files):raise ValueError('Final decoded key-frame extraction incomplete')
 return files
def contact_sheets(p):
 old=decoded_frames(V10,'v10');new=decoded_frames(p,'v11')
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
 panels=[];qa=[]
 for i,n in enumerate(PICKS):
  panel=Image.new('RGB',(1920,582),'#182028');d=ImageDraw.Draw(panel)
  for x,src,label in [(0,old[i],'v10'),(960,new[i],'v11 final decoded MP4')]:
   with Image.open(src) as im:panel.paste(im.convert('RGB').resize((960,540)),(x,42))
   d.text((x+12,9),f'{n/24:.3f}s | frame {n} | {label}',font=font,fill='white')
  panels.append(panel)
  with Image.open(new[i]) as a,Image.open(FRAMES/f'{n:05d}.png') as b:
   aa=np.asarray(a.convert('RGB'),dtype=np.float32);bb=np.asarray(b.convert('RGB'),dtype=np.float32)
   mse=float(np.mean((aa-bb)**2));mae=float(np.mean(np.abs(aa-bb)))
  qa.append({'frame':n,'decoded_png_sha256':digest(new[i]),'encode_vs_lossless_mean_absolute_error':mae,
             'encode_vs_lossless_psnr_db':10*math.log10(255**2/mse) if mse else None})
 files=[]
 for page in range(3):
  items=panels[page*4:page*4+4];sheet=Image.new('RGB',(1920,582*len(items)),'#182028')
  for row,item in enumerate(items):sheet.paste(item,(0,row*582))
  dest=OUT/f'v11-comparison-{page+1}.jpg';sheet.save(dest,quality=96);files.append(str(dest))
 return {'files':files,'picks':PICKS,'panels_are_decoded_mp4_frames':True,'frame_checks':qa}

def verify(p,audit):
 log('Validating final full decode, exact timeline and original audio.')
 technical=probe_and_decode(p);hashes={}
 for codec in ('copy','pcm_s16le'):
  values={label:audio_hash(path,codec) for label,path in [('source',SOURCE),('audio_input',AUDIO),('v10',V10),('v11',p)]}
  if len(set(values.values()))!=1:raise ValueError('Audio differs for '+codec+': '+str(values))
  hashes[codec]=values
 b=assert_inputs()
 comparisons=contact_sheets(p)
 report={'version':'v11','output':str(DEST),'sha256':digest(p),'bytes':p.stat().st_size,
         'technical':technical,'audio_hashes':hashes,'audio_unchanged':True,'strict_decode':True,
         'read_only_inputs_unchanged':True,'input_baseline':b,'frame_audit':audit,
         'comparison_evidence':comparisons,'encoder_script_sha256':digest(Path(__file__)),
         'verified_epoch':time.time()}
 return report
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true')
 ap.add_argument('--check',action='store_true');ap.add_argument('--encode',action='store_true')
 ap.add_argument('--verify',action='store_true');ap.add_argument('--resume-render',action='store_true');args=ap.parse_args()
 WORK.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
 if args.prepare or not BASELINE.exists():prepare()
 if not(args.check or args.encode or args.verify or args.resume_render):return
 assert_inputs();audit=frame_check()
 if args.encode or args.resume_render:
  encoded=encode() if args.encode else WORK/'trick-heart-two-character-pv-v11.rendering.mp4'
  temp,remux=remux_full_audio(encoded);report=verify(temp,audit);report['audio_remux']=remux
  temp.replace(DEST)
  if digest(DEST)!=report['sha256']:raise ValueError('Final output hash mismatch')
 elif args.verify:
  report=verify(DEST,audit)
  if (WORK/'v11-audio-remux-record.json').exists():report['audio_remux']=read(WORK/'v11-audio-remux-record.json')
 else:return
 write(OUT/'v11-verification.json',report)
 log(json.dumps({'video':str(DEST),'sha256':report['sha256'],'bytes':report['bytes'],
                 'technical':report['technical'],'audio_unchanged':True},ensure_ascii=False))
if __name__=='__main__':main()

"""Finalize recoverable v7 records/archive only after final media verification exists."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys,time,zipfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work';OUT=ROOT/'outputs'
OLD=Path('<ORIGINAL_WORKSPACE>')
PROJECT=OLD/'work/trick-heart-project'
VIDEO=OUT/'trick-heart-two-character-pv-v7.mp4'
RECORD=OUT/'v7-production-record.json'
ARCHIVE=OUT/'v7-revision-project.zip'
ASSETS=WORK/'assets-v7'
MASK_MANIFEST=WORK/'audit-mask/production-assets.json'
MOTION_MANIFEST=WORK/'audit-motion/production-assets.json'
EXPECTED_ASSETS={'hand-600.png','hand-1084.png','inhale.png','blow.png','braid.png','back.png'}
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def keep_previous(p):
 if p.exists():
  history=WORK/'finalize-history'/str(time.time_ns());history.mkdir(parents=True,exist_ok=True)
  shutil.copy2(p,history/p.name)
def write(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);keep_previous(p)
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def file_record(p):
 return {'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size}
def relative(p):return p.relative_to(ROOT).as_posix()
def require(p):
 if not p.is_file():raise FileNotFoundError('Required finalization input missing: '+str(p))
 return p
def contains_text(value,needle):
 if isinstance(value,dict):return any(contains_text(v,needle) for v in value.values())
 if isinstance(value,list):return any(contains_text(v,needle) for v in value)
 return isinstance(value,str) and needle in value
def collect_files():
 files={}
 for p in WORK.rglob('*.py'):
  if 'finalize-history' not in p.parts:files[relative(p)]=p
 for p in WORK.rglob('*.json'):
  if 'finalize-history' not in p.parts:files[relative(p)]=p
 for p in ASSETS.glob('*.png'):files[relative(p)]=p
 for folder in [WORK/'v7-review',WORK/'v7-decoded-qa/v6',WORK/'v7-decoded-qa/v7',WORK/'v7-decoded-extra']:
  if folder.is_dir():
   for p in folder.glob('*'):
    if p.suffix.lower() in ('.png','.jpg','.jpeg'):files[relative(p)]=p
 for p in OUT.glob('v7-*.json'):
  if p.name not in ('v7-production-record.json','v7-project-archive-verification.json'):files[relative(p)]=p
 for p in OUT.glob('v7-*.jpg'):files[relative(p)]=p
 for p in OUT.glob('v7-*.png'):files[relative(p)]=p
 return files
def README_text(verification,review):
 return f"""# トリックハート／魔术之心 双角色PV v7 局部修订工程

本包保存相对已交付v6的七段局部修改、采用资产、脚本和审核证据。
正片：1920×1080，24fps，3768帧，157秒；原音轨完整复制。
v6及原媒体保持只读。归档不含全片PNG缓存、完整MP4、旧工程大媒体或python_lib。

## 内容与证据

- work/assets-v7：六个本地采用资产；hand-600是复用的旧bare-612原画，不是新绘制人物。
- work/revision7_composite.py及audit-mask、audit-motion：局部合成、跟踪、遮罩与姿态选择。
- work/encode_v7.py：编码、完整音轨独立重封装、全解码与音轨hash验证。
- work/review_v7.py：六段原速/半速左右对比，v6在左、v7在右；审阅片静音。
- outputs/v7-production-record.json、v7-verification.json、v7-review-notes.json及work审核log：实际采用记录与审核范围。
- readonly_original_dependencies/tools：旧工具只读快照，供检查依赖；不要执行这些旧入口。
- archive-manifest.json：包内逐文件hash。ZIP外的v7-project-archive-verification.json记录ZIP自身hash。

七段使用左闭右开整数帧区间：
[600,621)、[1082,1091)、[1401,1467)、[2139,2169)、[2367,2401)、[3584,3630)、[3630,3666)。

## 600帧动作替代

用户允许在合理情况下换动作。600–602改用已生成的张掌姿态，以原硬币和手腕锚点进行整体相似变换。
600的资产来自旧bare-612-v3.png，按612的注册框放置；代码不重画人物。
603–605继续使用旧bare-603-v3.png；606–620继续使用旧bare-612-v3.png。
硬币由原片持有独立前景遮罩与黑色边缘；1084手部采用图与原兔子前景分层。

## 恢复依赖

保留原工程 {PROJECT}：
- runs/paired-v6/frames/final：完整3768帧v6无损输入。
- runs/white-sailor/frames/source：原PV逐帧缓存。
- research/source-1080.mp4、runs/white-sailor/research/source-audio.m4s。
- assets及tools：旧姿态原画、场景配置与导入依赖；部分新修改复用旧原画。
- outputs位于旧工程上两级：原v6 MP4与v6-verification.json用于只读基线。

Python运行库：{OLD/'work/python_lib'}；需要Pillow、NumPy、OpenCV、SciPy、imageio_ffmpeg。
已使用bundled Python：{sys.executable}；具体FFmpeg路径见v7-encoding-baseline.json。
原参考：research/character-white.png与character-black.jpg；记录含原路径和SHA256。
审阅标头字体依赖C:/Windows/Fonts/arial.ttf。

解压到独立工作区后先核对archive-manifest.json。
若移动目录，统一更新新脚本的OLD及少数工具中的绝对工作区路径；只读依赖快照不等于已迁移的可执行旧工程。
不要运行旧工具入口，因为它们可能有旧工程写入路径。

按顺序运行（用上述Python替代python）：

python work/revision7_composite.py --preview
python work/revision7_composite.py --all
python work/encode_v7.py --encode
python work/review_v7.py --encode
python work/finalize_v7.py --finalize

如当前工作区已有work/trick-heart-two-character-pv-v7.rendering.mp4，可用：
python work/encode_v7.py --resume-render

初次编码曾因视频帧数限制提前停止音频包写入。当前编码入口把编码视频轨与完整原AUDIO再次无限制stream-copy重封装，
保留原rendering临时文件；audio-remux记录保存前后包数、首末包和hash。恢复模式不重编码视频。

## 原画与审核范围

图像工具负责采用的人物原画；程序只负责遮罩、调色、注册、跟踪、切换与合成。
production-assets.json中的生成说明明确区分原始记录与重建brief；重建brief不是完整原始提示词。
拒绝候选保存在审核记录中，不列为采用素材。包内不会宣称所有帧均经过人工播放。
实际关键帧检查、最终解码抽帧与自动覆盖分别记载。自动全解码不替代解剖、动作和画风视觉检查。

当前正片hash：{verification['sha256']}
当前审阅片hash：{review['review_sha256']}
"""
def finalize():
 required=[OUT/'v7-verification.json',OUT/'v7-review-notes.json',MASK_MANIFEST,MOTION_MANIFEST,
           WORK/'v7-frame-records.json',WORK/'v7-frame-audit.json',WORK/'v7-encoding-baseline.json',
           WORK/'audit-mask/rabbit-fullcanvas-verification.json',WORK/'v7-visual-review-log.json',VIDEO,
           WORK/'qa_rabbit_encoded.py',WORK/'v7-decoded-extra/01088.png',OUT/'v7-hand-preview.png']
 for p in required:require(p)
 ver=read(required[0]);review=read(required[1]);mask=read(MASK_MANIFEST);motion=read(MOTION_MANIFEST)
 if ver['sha256']!=digest(VIDEO):raise ValueError('Final PV differs from verification')
 meta=ver['technical']
 if (meta['width'],meta['height'],meta['fps'],meta['frames'],meta['duration'])!=(1920,1080,24,3768,157):
  raise ValueError('Final PV specification differs')
 for key in ('strict_decode','audio_unchanged','read_only_inputs_unchanged'):
  if ver.get(key) is not True:raise ValueError('Missing final verification: '+key)
 reviewvideo=require(Path(review['review_video']))
 if digest(reviewvideo)!=review['review_sha256']:raise ValueError('Review differs from verification')
 baseline=read(WORK/'v7-encoding-baseline.json')
 for label,entry in baseline['inputs'].items():
  if digest(require(Path(entry['path'])))!=entry['sha256']:raise ValueError('Read-only input changed: '+label)
 localassets=sorted(ASSETS.glob('*.png'))
 if {p.name for p in localassets}!=EXPECTED_ASSETS:raise ValueError('Expected exactly six adopted local assets')
 assets={p.name:file_record(p) for p in localassets}
 refs={name:file_record(require(PROJECT/'research'/filename)) for name,filename in
       [('white','character-white.png'),('black','character-black.jpg')]}
 frames=read(WORK/'v7-frame-records.json');audit=read(WORK/'v7-frame-audit.json')
 if len(frames['records'])!=3768:raise ValueError('Final frame records incomplete')
 if audit['summary']['manifest_sha256']!=digest(WORK/'v7-frame-records.json'):raise ValueError('Frame audit manifest changed')
 intervals=frames['changed_intervals']
 if len(intervals)!=7:raise ValueError('Expected seven revision intervals')
 rabbit=read(WORK/'audit-mask/rabbit-fullcanvas-verification.json')
 for r in rabbit:
  for key in ('rabbit_matte_source_exact','rabbit_red_source_exact','rabbit_white_instances_source_exact'):
   if r.get(key) is not True:raise ValueError('Rabbit source ownership not verified '+str(r.get('frame'))+' '+key)
 actual=read(WORK/'v7-visual-review-log.json')
 agentlogs={}
 for p in [WORK/'audit-render-visual-log.json',WORK/'audit-mask/non-art-fix-review.json',
           WORK/'audit-mask/hand-fix-records.json',WORK/'audit-motion/preview/records.json']:
  if p.is_file():agentlogs[relative(p)]={'file':file_record(p),'data':read(p)}
 scripts={relative(p):file_record(p) for p in sorted(WORK.rglob('*.py')) if 'finalize-history' not in p.parts}
 dependencies={p.name:file_record(p) for p in sorted((PROJECT/'tools').glob('*.py'))}
 altered=[]
 actual_ranges=audit['summary']['pixel_changed_intervals']
 for item in intervals:
  s,e=item['start'],item['end']
  count=sum(max(0,min(e,r['end'])-max(s,r['start'])) for r in actual_ranges)
  altered.append(dict(item,actual_pixel_changed_frames=count))
 record={'version':'v7','delivery':file_record(VIDEO),'technical':meta,
         'audio_unchanged':True,'audio_hashes':ver['audio_hashes'],'audio_remux':ver.get('audio_remux'),
         'immutable_original_inputs':baseline['inputs'],'original_v6_preserved':True,
         'character_reference_images':refs,'character_mapping':{'source_drill_twintails':'black hair with glasses','other_source_character':'long white hair sailor outfit'},
         'revision_intervals_left_closed_right_open':altered,'frame_audit_summary':audit['summary'],
         'adopted_local_asset_count':6,'adopted_local_assets':assets,
         'asset_manifests':{relative(MASK_MANIFEST):mask,relative(MOTION_MANIFEST):motion},
         'all_local_new_script_hashes':scripts,
         'readonly_original_dependencies':{'tools_snapshots':dependencies,
               'execution_policy':'Snapshots for recovery/inspection only; do not execute old entrypoints',
               'external_inputs_required':['saved v6 lossless frames','source frame cache','original source/audio','old adopted assets','old work/python_lib']},
         'hand600_action_substitution':{'authorized':True,'authorization_summary':'User allowed a reasonable alternative hand action; recorded in hand asset manifest and actual visual review log.',
               'authorization_original_wording_if_manifest_contains_it':'问题仍在，允许你在合理的情况下换个动作' if contains_text(mask,'问题仍在，允许你在合理的情况下换个动作') else None,
               'range':[600,603],'adopted_pose':'open palm, existing bare-612-v3 artwork',
               'asset_source':str(PROJECT/'assets/white-sailor/bare-612-v3.png'),
               'registration_reference_frame':612,'tracking':'whole-hand similarity transform from original coin and wrist anchors',
               'continuation_mapping':[{'range':[603,606],'original_asset':'bare-603-v3.png'},{'range':[606,621],'original_asset':'bare-612-v3.png'}],
               'coin_ownership':'original source foreground and ink edge'},
         'generation_prompt_recording':{'tool':'built-in image_gen.imagegen','detail_records':'asset_manifests',
               'brief_policy':'Reconstructed briefs are descriptions of adopted generation stages, not complete original prompt transcripts.',
               'raw_original_prompt_completeness':'See each agent manifest; no complete prompt transcript is inferred.'},
         'failed_candidates_and_reasons':{'source':'agent asset manifests and visual audit logs','include_in_adopted_assets':False,
               'render_audit':agentlogs.get('work/audit-render-visual-log.json')},
         'actual_visual_review_log':actual,'agent_audit_logs':agentlogs,
         'visual_review_scope':'Recorded key frames and source/generated/decoded samples; no claim of full-video manual playback.',
         'rabbit_fullcanvas_validation':{'data':rabbit,'file':file_record(WORK/'audit-mask/rabbit-fullcanvas-verification.json'),
               'all_rabbit_instance_mattes_and_red_parts_source_exact':True,
               'tiny_unowned_white_pixels_changed_total':sum(r.get('tiny_unowned_white_pixels_changed',0) for r in rabbit)},
         'final_encoded_evidence':ver['comparison_evidence'],
         'review_clip':{'file':file_record(reviewvideo),'notes':review},
         'verification_record':file_record(OUT/'v7-verification.json'),
         'archive':{'path':str(ARCHIVE),'includes':'local revision scripts/assets/manifests/evidence and readonly dependency snapshots',
               'excludes':'full 3768 PNG sequence, MP4 media, old project large inputs and runtime libraries',
               'archive_hash_record':str(OUT/'v7-project-archive-verification.json')},
         'created_epoch':time.time()}
 extra=WORK/'v7-decoded-extra/01088.png'
 if extra.is_file():record['rabbit_encoded_frame1088_evidence']=file_record(extra)
 qa=WORK/'qa_rabbit_encoded.py'
 if qa.is_file():record['rabbit_encoded_qa_script']=file_record(qa)
 record['user_visible_hand_preview']=file_record(OUT/'v7-hand-preview.png')
 write(RECORD,record)
 readme=OUT/'v7-revision-project-README.md';keep_previous(readme)
 readme.write_text(README_text(ver,review),encoding='utf-8')
 files=collect_files();files[relative(RECORD)]=RECORD;files['README-v7.md']=readme
 for p in sorted((PROJECT/'tools').glob('*.py')):files['readonly_original_dependencies/tools/'+p.name]=p
 license=PROJECT/'LICENSE'
 if license.is_file():files['readonly_original_dependencies/LICENSE']=license
 archive_manifest={'version':'v7','files':{name:{'sha256':digest(p),'bytes':p.stat().st_size} for name,p in sorted(files.items())},
                   'archive_excludes_full_frame_sequence_and_mp4':True}
 temp=WORK/('v7-revision-project-'+str(time.time_ns())+'.zip')
 with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name,p in sorted(files.items()):z.write(p,name)
  z.writestr('archive-manifest.json',json.dumps(archive_manifest,ensure_ascii=False,indent=2))
 with zipfile.ZipFile(temp) as z:
  bad=z.testzip()
  if bad:raise ValueError('ZIP CRC failure: '+bad)
  for name,entry in archive_manifest['files'].items():
   if hashlib.sha256(z.read(name)).hexdigest()!=entry['sha256']:raise ValueError('ZIP hash failure: '+name)
 for name,p in files.items():
  if digest(p)!=archive_manifest['files'][name]['sha256']:raise ValueError('Input changed while archiving: '+name)
 keep_previous(ARCHIVE);temp.replace(ARCHIVE)
 write(OUT/'v7-project-archive-verification.json',{'archive':file_record(ARCHIVE),
       'file_count':len(archive_manifest['files'])+1,'crc_and_every_entry_sha256_checked':True,
       'production_record':file_record(RECORD),'full_png_sequence_excluded':True,'mp4_excluded':True})
 print(json.dumps({'production_record':str(RECORD),'archive':str(ARCHIVE),'archive_sha256':digest(ARCHIVE),
                   'bytes':ARCHIVE.stat().st_size,'files':len(archive_manifest['files'])+1},ensure_ascii=False),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--finalize',action='store_true');args=ap.parse_args()
 if args.finalize:finalize()
 else:print('Finalizer ready; no artifacts written. Run --finalize after final decoded QA and both agent manifests exist.')

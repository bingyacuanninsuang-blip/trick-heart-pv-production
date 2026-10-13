"""Build the requested character version with independent source/asset records and caches.
Never validate a new source or new art against the historical Roxy release hashes.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from fractions import Fraction
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
LOCAL_LIB=PROJECT.parent/'python_lib'
if LOCAL_LIB.is_dir():
    sys.path.insert(0,str(LOCAL_LIB))
    os.environ['PYTHONPATH']=str(LOCAL_LIB)+os.pathsep+os.environ.get('PYTHONPATH','')
def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    return h.hexdigest()
def read_json(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def resolve(path):
    value=Path(path)
    return (value if value.is_absolute() else PROJECT/value).resolve()
def command(args):
    result=subprocess.run([str(v) for v in args],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if result.returncode:raise RuntimeError('Command failed: '+str(args[0])+'\n'+result.stderr[-3000:])
    return result
def ffmpeg_path():
    configured=os.environ.get('ROXY_FFMPEG')
    if configured:return configured
    found=shutil.which('ffmpeg')
    if found:return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:raise FileNotFoundError('Set ROXY_FFMPEG to a local FFmpeg executable')
def probe(source,ffmpeg):
    ffprobe=os.environ.get('ROXY_FFPROBE') or shutil.which('ffprobe')
    if ffprobe:
        data=json.loads(command([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',source]).stdout)
        video=next(s for s in data['streams'] if s['codec_type']=='video')
        audios=[s for s in data['streams'] if s['codec_type']=='audio']
        if not audios:raise ValueError('Input source has no audio track')
        return {'width':int(video['width']),'height':int(video['height']),
                'fps':float(Fraction(video['avg_frame_rate'])),
                'frames':int(video.get('nb_read_frames') or video['nb_frames']),
                'duration':float(video.get('duration') or data['format']['duration']),
                'audio':audios[0],'method':'ffprobe-count-frames'}
    # OpenCV obtains geometry; FFmpeg decodes every video frame before accepting the input.
    import cv2
    cap=cv2.VideoCapture(str(source))
    if not cap.isOpened():raise ValueError('Cannot read new source video')
    width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps=cap.get(cv2.CAP_PROP_FPS);cap.release()
    decoded=command([ffmpeg,'-hide_banner','-v','info','-nostats','-progress','pipe:1','-i',source,
                     '-map','0:v:0','-an','-f','null','-'])
    counts=re.findall(r'^frame=(\d+)',decoded.stdout,re.M)
    audio_line=next((line.strip() for line in decoded.stderr.splitlines() if 'Audio:' in line),None)
    if not counts or not audio_line:raise ValueError('Cannot verify video frame count and source audio')
    frames=int(counts[-1])
    return {'width':width,'height':height,'fps':fps,'frames':frames,'duration':frames/fps,
            'audio':{'description':audio_line},'method':'opencv-geometry-plus-complete-ffmpeg-decode'}
def validate_media(meta,expected):
    for key in ['width','height','frames']:
        if meta[key]!=expected[key]:raise ValueError(f'New source {key}: {meta[key]} != {expected[key]}')
    if abs(meta['fps']-expected['fps'])>0.001:raise ValueError('New source does not have the required frame rate')
    if abs(meta['duration']-expected['duration'])>1/expected['fps']:
        raise ValueError('New source duration does not match the reference timeline')
def legacy_hashes():
    baseline=read_json(PROJECT/'assets/resources.json')['files']
    return {entry['sha256'] for name,entry in baseline.items() if name.startswith('assets/') and name.endswith('.png')}
def record_assets(config,assets,runroot):
    if not assets.is_dir():raise FileNotFoundError('Generate new requested-character artwork in '+str(assets))
    prohibited=legacy_hashes();records={}
    from PIL import Image
    for file in sorted(assets.rglob('*.png')):
        key=file.relative_to(assets).as_posix();sha=digest(file)
        if sha in prohibited:raise ValueError('Historical Roxy artwork is prohibited in the new asset set: '+key)
        with Image.open(file) as im:
            im.verify()
        with Image.open(file) as im:
            if im.width<16 or im.height<16:raise ValueError('Empty new artwork: '+key)
            records[key]={'sha256':sha,'size':[im.width,im.height],'mode':im.mode}
    if not records:raise ValueError('No generated new-character PNG assets are available')
    result={'asset_root':str(assets),'character_profile':config['character_profile'],'files':records}
    write_json(runroot/'research/new-asset-hashes.json',result)
    return result
def verify_assets(config,assets,runroot,complete=True):
    manifest=read_json(runroot/'research/new-asset-hashes.json')
    if Path(manifest['asset_root']).resolve()!=assets:raise ValueError('New asset root changed; record the new hashes explicitly')
    prohibited=legacy_hashes()
    required=config['required_assets'] if complete else manifest['files']
    missing=[name for name in required if name not in manifest['files'] or not (assets/name).is_file()]
    if missing:
        write_json(runroot/'review/missing-new-cels.json',{'missing':missing})
        raise FileNotFoundError(f'{len(missing)} missing requested-character cels. See {runroot}/review/missing-new-cels.json\n'+', '.join(missing[:15]))
    for name,entry in manifest['files'].items():
        path=(assets/name).resolve()
        if assets not in path.parents:raise ValueError('Asset path leaves the requested asset root')
        sha=digest(path)
        if sha!=entry['sha256'] or sha in prohibited:raise ValueError('New asset hash mismatch or original-character artwork: '+name)
    return manifest
def prepare_frames(source,runroot,ffmpeg,count):
    folder=runroot/'frames/source';folder.mkdir(parents=True,exist_ok=True)
    if len(list(folder.glob('*.png')))!=count:
        command([ffmpeg,'-v','error','-y','-i',source,'-map','0:v:0','-an','-fps_mode','passthrough',
                 '-start_number','0',folder/'%05d.png'])
    if len(list(folder.glob('*.png')))!=count:raise ValueError('Decoded source frame count mismatch')
def configure(config,source,assets,runroot,ffmpeg):
    os.environ.update(PV_RUN_ROOT=str(runroot),PV_ASSET_ROOT=str(assets),
        PV_SOURCE_VIDEO=str(source),PV_CHARACTER_PROFILE=config['character_profile'],ROXY_FFMPEG=str(ffmpeg))
    for folder in ['review','research','frames/source','frames/full-composite-v4','deliverables']:
        (runroot/folder).mkdir(parents=True,exist_ok=True)
def render_one(n):
    import cv2
    from PIL import Image
    import revision4_composite as v4
    cv2.setNumThreads(1)
    out,record=v4.render(n)
    Image.fromarray(out).save(v4.DEST/f'{n:05d}.png',compress_level=3)
    return record
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',default='config/white-sailor.json')
    ap.add_argument('--record-source',action='store_true')
    ap.add_argument('--record-assets',action='store_true')
    ap.add_argument('--prepare-source',action='store_true')
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--frames',type=int,nargs='+')
    ap.add_argument('--all',action='store_true')
    ap.add_argument('--encode',action='store_true')
    ap.add_argument('--verify',action='store_true')
    ap.add_argument('--workers',type=int,default=4)
    args=ap.parse_args()
    config=read_json(resolve(args.config));source=resolve(config['source_video'])
    assets=resolve(config['asset_root']);runroot=resolve(config['run_root']);ffmpeg=ffmpeg_path()
    if runroot==PROJECT:raise ValueError('A new character version requires an independent run directory')
    if assets==PROJECT/'assets':raise ValueError('A new character version requires a separate asset directory')
    if PROJECT not in runroot.parents:raise ValueError('Run caches must stay inside this project')
    if not source.is_file():raise FileNotFoundError('New source input is missing: '+str(source))
    configure(config,source,assets,runroot,ffmpeg)
    baseline=runroot/'research/new-source-baseline.json'
    if args.record_source:
        meta=probe(source,ffmpeg);validate_media(meta,config['expected_video'])
        sha=digest(source)
        if baseline.exists() and read_json(baseline)['sha256']!=sha and any((runroot/'frames').rglob('*.png')):
            raise ValueError('Source changed while cached frames exist; choose a fresh run_root')
        audio=runroot/'research/source-audio.m4s'
        command([ffmpeg,'-v','error','-y','-i',source,'-map','0:a:0','-vn','-c:a','copy','-f','mp4',audio])
        write_json(baseline,{'path':str(source),'source_url':config.get('source_url'),'sha256':sha,
            'bytes':source.stat().st_size,'technical':meta,'audio_sha256':digest(audio),
            'audio_extraction':'stream copy','matches_original_release_hash':False})
        print('New source verified and recorded separately:',meta,flush=True)
    if not baseline.is_file():raise FileNotFoundError('Use --record-source to verify and register this source')
    source_record=read_json(baseline)
    if source_record['sha256']!=digest(source):raise ValueError('New source changed after technical registration')
    if digest(runroot/'research/source-audio.m4s')!=source_record['audio_sha256']:raise ValueError('Copied source audio changed')
    if args.prepare_source:
        prepare_frames(source,runroot,ffmpeg,config['expected_video']['frames'])
        print('Prepared all source frames',flush=True)
    if args.record_assets:
        result=record_assets(config,assets,runroot)
        print('Recorded new PNG hashes:',len(result['files']),flush=True)
    if not (args.check or args.frames or args.all or args.encode or args.verify):return
    manifest=verify_assets(config,assets,runroot,complete=not bool(args.frames))
    fingerprint=hashlib.sha256(json.dumps([source_record['sha256'],manifest,config],sort_keys=True).encode()).hexdigest()
    marker=runroot/'review/render-input-id.json'
    if marker.is_file() and read_json(marker)['fingerprint']!=fingerprint:
        if any((runroot/'frames/full-composite-v4').glob('*.png')):
            raise ValueError('Artwork changed after final frames were rendered; choose a fresh run_root or explicitly archive those frames')
    write_json(marker,{'fingerprint':fingerprint,'source_sha256':source_record['sha256']})
    if args.check:
        print('New source and complete requested-character asset hashes verified',flush=True)
        if not (args.frames or args.all or args.encode or args.verify):return
    if args.frames or args.all:
        prepare_frames(source,runroot,ffmpeg,config['expected_video']['frames'])
        import revision_composite as v2
        # Derivative is deterministic, run-local, and uses only the supplied new art.
        if args.all or any(1224<=n<1244 for n in (args.frames or [])):v2.setup()
        if args.frames:
            import revision4_composite as v4
            invalid=[n for n in args.frames if not 0<=n<config['expected_video']['frames']]
            if invalid:raise ValueError('Preview frames outside the source timeline: '+str(invalid))
            v4.preview(args.frames)
            print('Requested new-character preview frames rendered',flush=True)
        if args.all:
            import multiprocessing
            from concurrent.futures import ProcessPoolExecutor
            total=config['expected_video']['frames'];records=[]
            with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
                for i,record in enumerate(pool.map(render_one,range(total),chunksize=8)):
                    records.append(record)
                    if i%120==0:print(f'New-character final frames {i}/{total}',flush=True)
            write_json(runroot/'review/v4-frame-verification.json',records)
            write_json(runroot/'review/final-render-input-id.json',{'fingerprint':fingerprint})
    output=runroot/'deliverables'/(config['output_stem']+'.mp4')
    if args.encode:
        frames=runroot/'frames/full-composite-v4'
        records=read_json(runroot/'review/v4-frame-verification.json')
        if [r['frame'] for r in records]!=list(range(config['expected_video']['frames'])):raise ValueError('Final frame records incomplete')
        if read_json(runroot/'review/final-render-input-id.json')['fingerprint']!=fingerprint:raise ValueError('Final frames use different source/assets')
        temp=output.with_name(output.stem+'.rendering.mp4')
        command([ffmpeg,'-v','error','-y','-framerate','24','-start_number','0','-i',frames/'%05d.png',
                 '-i',runroot/'research/source-audio.m4s','-map','0:v:0','-map','1:a:0','-c:v','libx264',
                 '-crf','15','-preset','slow','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',temp])
        temp.replace(output);print('Encoded requested character PV:',output,flush=True)
    if args.verify:
        meta=probe(output,ffmpeg);validate_media(meta,config['expected_video'])
        # Compare decoded audio hashes, independently of the new video encoding.
        hashes={}
        for label,path in [('source',source),('output',output)]:
            hashes[label]=command([ffmpeg,'-v','error','-i',path,'-map','0:a:0','-f','hash','-hash','sha256','-']).stdout.strip()
        if hashes['source']!=hashes['output']:raise ValueError('Audio PCM changed')
        command([ffmpeg,'-v','error','-xerror','-i',output,'-f','null','-'])
        write_json(runroot/'review/new-output-verification.json',{'output':str(output),'sha256':digest(output),
            'technical':meta,'pcm_hash':hashes['output'],'source_and_assets_fingerprint':fingerprint,
            'strict_decode':True,'original_release_comparison':False})
        print('New output frame timeline and unchanged source audio verified',flush=True)
if __name__=='__main__':main()

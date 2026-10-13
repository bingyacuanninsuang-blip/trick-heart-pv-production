from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
W=ROOT/'work'
sys.path.insert(0,'<ORIGINAL_WORKSPACE>/work/python_lib')
from PIL import Image
G=Path('<USER_HOME>/.codex/generated_images/01a12612-48b8-76f1-a8ed-b1da38d8981f')
def info(p):
 d={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
 if p.suffix.lower() in ('.png','.jpg'):
  with Image.open(p) as im:d.update(pixel_size=list(im.size),mode=im.mode)
 return d
specs=[
 ('inhale','exec-7439fb51-5c5c-4538-a246-eb78f7e0813e.png',[2147,2151],['inhale-target.png','source-inhale.png','black-reference.jpg'],'Edit the black-haired girl with glasses into a distinct inhaling preparation: eyes squeezed shut, head tilted back slightly, preserving her identity, existing linework and costume. Use source frame2148 for pose and existing target for character style.'),
 ('blow','exec-bf2b4e1f-2e22-4ac6-9aa6-175e12cfcb73.png',[2151,2157],['blow-target.png','source-blow.png','black-reference.jpg'],'Edit the black-haired girl into a visible blowing action: small pursed oo lips, cheeks and head moved forward naturally, preserve identity, glasses and costume. Follow source frame2154 timing; do not add artificial breath.'),
 ('braid','exec-597f0a4d-b1cc-4f47-898f-6feb635bcc32.png',[3584,3630],['braid-target.png','source-braid.png','white-reference.png'],'Simplify the white-haired sailor character braid in the existing ending panel: broad braid segments, fewer hair details, flat anime colors and linework matching source frame3588. Preserve character identity and the existing central panel action.'),
 ('back','exec-005cbc2a-e21d-4348-8523-1f23c8a69cf9.png',[3630,3666],['back-target.png','source-back.png','white-reference.png'],'Correct the back-view white-haired sailor character: braid and triangular clips on character-left, viewer-left; braid toward the front shoulder. Preserve original bag position and motion without mirroring the whole character. Simplify style and keep the complete ahoge, following source frame3640.')
]
records=[]
for name,origin,interval,refs,brief in specs:
 records.append({'asset_id':name,'adopted_asset':info(W/'assets-v7'/f'{name}.png'),'generated_original':info(G/origin),'frames_half_open':interval,'tool':'image_gen.imagegen','prompt_record':{'kind':'reconstructed_brief','exact_prompt_available':False,'text':brief},'reference_set':{'provenance':'reference_set_reconstructed_from_session_summary','exact_tool_argument_paths_available':False,'entries':[info(W/'audit-motion'/x) for x in refs]},'whole_cel_normalization':[1920,1080],'local_anatomical_deformation':False})
out={'schema_version':'1.0','record_type':'v7_adopted_motion_art','provenance':{'source':'Root session summary plus verified local files; saved after the locked compositor and final MP4 verification.','exact_imagegen_call_history_available':False,'briefs_are_not_complete_original_prompts':True,'only_this_metadata_helper_and_record_created':True},'final_assets':records,'locked_compositor':info(W/'audit-motion/motion_patch.py'),'state_timeline':{'prepare_existing_v6':[2139,2147],'inhale':[2147,2151],'pursed_blow':[2151,2157],'relax_existing_v6':[2157,2169]},'source_ownership':'Original moving paper, lyrics, ending panel motion, background and butterflies are retained by compositor masks; generated paper is excluded.','implementation_evidence':[str(W/'audit-motion/motion_patch.py'),str(W/'audit-motion/preview/records.json')],'visual_review_evidence':[str(W/'v7-visual-review-log.json'),str(ROOT/'outputs/v7-comparison-late.jpg')],'manual_full_video_playback_claim':False}
p=W/'audit-motion/production-assets.json'
if p.exists():raise FileExistsError('Preserve already-created manifest: '+str(p))
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'record':str(p),'sha256':info(p)['sha256'],'asset_count':len(records)}))

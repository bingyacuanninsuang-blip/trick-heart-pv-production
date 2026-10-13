from pathlib import Path
import sys, os, json, shutil
sys.dont_write_bytecode = True
OLD=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
HERE=Path('<REVISION_WORKSPACE>/work/audit-mask')
sys.path.insert(0,str(OLD.parent/'python_lib'))
from PIL import Image
HERE.mkdir(parents=True,exist_ok=True)
crops=json.loads((OLD/'assets/v3-reference/crops.json').read_text())
items=[]
for ref,asset in [(600,'assets/paired-v6/hand-600.png'),(603,'assets/white-sailor/bare-603-v3.png'),(612,'assets/white-sailor/bare-612-v3.png'),(1084,'assets/paired-v6/hand-1084.png')]:
    original=OLD/asset
    shutil.copyfile(original,HERE/f'hand-{ref}-original.png')
    source=OLD/f'runs/white-sailor/frames/source/{ref:05d}.png'
    before=OLD/f'runs/paired-v6/frames/final/{ref:05d}.png'
    shutil.copyfile(source,HERE/f'source-{ref}-full.png')
    shutil.copyfile(before,HERE/f'before-{ref}-full.png')
    Image.open(source).crop(tuple(crops[str(ref)])).save(HERE/f'source-{ref}-crop.png')
    Image.open(before).crop(tuple(crops[str(ref)])).save(HERE/f'before-{ref}-crop.png')
    im=Image.open(original)
    items.append({'reference':ref,'original_asset':str(original),'local_original':str(HERE/f'hand-{ref}-original.png'),'original_size':list(im.size),'canvas_crop_xyxy':crops[str(ref)],'source_pose_crop':str(HERE/f'source-{ref}-crop.png'),'current_composite_crop':str(HERE/f'before-{ref}-crop.png'),'alpha':{'mode':im.mode,'expectation':'RGBA transparent outside complete hand and dark sleeve; no source coin/rabbit, no lyrics/background; preserve canvas size/pose/occupancy exactly'},'frames_half_open':[ref,603 if ref==600 else 606 if ref==603 else 621 if ref==612 else 1091]})
shutil.copyfile(OLD/'assets/white-sailor/full-1440.png',HERE/'full-1440-original.png')
shutil.copyfile(OLD/'assets/white-sailor/full-2388.png',HERE/'full-2388-original.png')
(HERE/'inputs.json').write_text(json.dumps(items,indent=2),encoding='utf-8')
print(json.dumps(items,indent=2))


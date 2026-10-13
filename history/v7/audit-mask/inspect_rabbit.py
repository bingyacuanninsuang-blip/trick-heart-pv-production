import sys
sys.dont_write_bytecode=True
from pathlib import Path
old=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
sys.path.insert(0,str(old.parent/'python_lib'));sys.path.insert(0,str(old/'tools'))
import revision6_composite as v6
import numpy as np
from hand_fixes import source_rabbit_mask
src=v6.src(1084);m=source_rabbit_mask(src,v6)
v6.Image.fromarray(m).save(Path(__file__).parent/'rabbit-mask.png')
for y,x in [(840,1010),(800,1020),(770,1050),(552,850),(840,900)]:
 print(y,x,src[y,x].tolist(),int(m[y,x]))
raw=v6.c.rabbit_mask(src,(600,0,1920,880),(900,0,1920,650))
num,lab,stats,cent=v6.cv2.connectedComponentsWithStats(raw,8)
print('raw',[(stats[i].tolist(),cent[i].tolist()) for i in range(1,num) if stats[i,4]>50])
print('lower',(m[720:]>0).sum(),'rawlower',(raw[720:]>0).sum())


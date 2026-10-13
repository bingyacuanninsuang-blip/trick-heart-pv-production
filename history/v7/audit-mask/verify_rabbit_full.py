from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
here=Path('<REVISION_WORKSPACE>/work/audit-mask')
p=here/'hand_fixes.py';s=p.read_text()
s=s.replace("if np.count_nonzero(gm)<350:return out,{'hand_visible':False}","if np.count_nonzero(gm)<350:return (src.copy() if n>=1082 else out),{'hand_visible':False,'zoom_source_exact':n>=1082}")
p.write_text(s)
old=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
sys.path.insert(0,str(old.parent/'python_lib'));sys.path.insert(0,str(old/'tools'))
import revision6_composite as v6
from hand_fixes import compose_hand,source_rabbit_mask
import numpy as np
report=[]
for n in range(1082,1091):
 src=v6.src(n);prior=v6.c.read(old/f'runs/paired-v6/frames/final/{n:05d}.png')
 out,rec=compose_hand(prior,src,n,v6,here.parent/'assets-v7')
 v6.Image.fromarray(out).save(here/f'handfix-{n:05d}.png')
 m=source_rabbit_mask(src,v6)>0
 white=src.min(2)>246
 r,g,b=src.astype(np.int16).transpose(2,0,1)
 red=(r>160)&(g<125)&(b>45)&(r>g*1.6)
 rec.update(frame=n,rabbit_matte_source_exact=bool(np.array_equal(out[m],src[m])),white_source_exact=bool(np.array_equal(out[white],src[white])),rabbit_red_source_exact=bool(np.array_equal(out[red&m],src[red&m])),fullframe_source_exact=bool(np.array_equal(out,src)))
 report.append(rec)
(here/'rabbit-fullcanvas-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))


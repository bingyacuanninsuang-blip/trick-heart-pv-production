import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
here=Path('<REVISION_WORKSPACE>/work/audit-mask')
old=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
sys.path.insert(0,str(old.parent/'python_lib'));sys.path.insert(0,str(old/'tools'))
import revision6_composite as v6
import numpy as np
report=json.loads((here/'rabbit-fullcanvas-verification.json').read_text())
for rec in report:
 n=rec['frame'];src=v6.src(n);out=v6.c.read(here/f'handfix-{n:05d}.png')
 white=v6.f.component((src.min(2)>246).astype(np.uint8)*255,200)>0
 rec['rabbit_white_instances_source_exact']=bool(np.array_equal(out[white],src[white]))
 raw=src.min(2)>246
 changed=raw&np.any(out!=src,axis=2)
 ys,xs=np.where(changed)
 rec['tiny_unowned_white_pixels_changed']=int(changed.sum())
 rec['tiny_unowned_white_bounds']=([int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None)
 print(n,rec['rabbit_matte_source_exact'],rec['rabbit_white_instances_source_exact'],rec['rabbit_red_source_exact'],rec['tiny_unowned_white_pixels_changed'],rec['tiny_unowned_white_bounds'])
(here/'rabbit-fullcanvas-verification.json').write_text(json.dumps(report,indent=2))


from pathlib import Path
import sys,os
sys.dont_write_bytecode=True
OLD=Path(r'<ORIGINAL_WORKSPACE>/work/trick-heart-project')
sys.path[:0]=[str(OLD/'tools'),str(OLD.parent/'python_lib')]
import revision6_composite as v6
import numpy as np
def anchor(n):
    s=v6.src(n);r,g,b=s.astype(int).transpose(2,0,1)
    m=(r>240)&(g>195)&(g<240)&(b>185)&(r-g>10)&(r-g<65)&(v6.c.rect((1450,350,1920,900))>0)
    count,lab,stats,centers=v6.cv2.connectedComponentsWithStats(m.astype(np.uint8),8)
    ix=max(range(1,count),key=lambda i:stats[i,4])
    return centers[ix],stats[ix].tolist()
a,_=anchor(2145)
for n in [2139,2145,2146,2147,2148,2150,2151,2153,2154,2155,2156,2157,2163,2168]:
    b,st=anchor(n)
    print(n,np.round(b-a,2).tolist(),st,flush=True)

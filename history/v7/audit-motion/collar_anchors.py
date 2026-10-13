from pathlib import Path
import sys
sys.dont_write_bytecode=True
OLD=Path(r'<ORIGINAL_WORKSPACE>/work/trick-heart-project')
sys.path[:0]=[str(OLD/'tools'),str(OLD.parent/'python_lib')]
import revision6_composite as v6
import numpy as np
def anchor(n):
 s=v6.src(n);m=(s.min(2)>228)&((s.max(2).astype(int)-s.min(2))<22)&(v6.c.rect((1500,760,1920,1030))>0)
 co,lab,st,cen=v6.cv2.connectedComponentsWithStats(m.astype(np.uint8),8)
 ix=max(range(1,co),key=lambda i:st[i,4]); yy,xx=np.where(lab==ix)
 top=yy<np.percentile(yy,28)
 return np.array([xx[top].mean(),yy[top].mean()]),st[ix]
a,_=anchor(2145)
for n in [2145,2147,2148,2150,2151,2154,2155,2156]:
 b,st=anchor(n); print(n,np.round(b-a,2).tolist(),st.tolist())

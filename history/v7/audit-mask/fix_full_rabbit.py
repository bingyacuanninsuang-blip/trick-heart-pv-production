from pathlib import Path
p=Path('<REVISION_WORKSPACE>/work/audit-mask/hand_fixes.py')
s=p.read_text(encoding='utf-8-sig')
a=s.index('def source_rabbit_mask(');b=s.index('def alternate_register(',a)
new='''def source_rabbit_mask(src,v6):
    c,np,cv2=v6.c,v6.np,v6.cv2
    r,g,b=src.astype(np.int16).transpose(2,0,1)
    white=v6.f.component((src.min(2)>246).astype(np.uint8)*255,200)
    red=(r>160)&(g<125)&(b>45)&(r>1.6*g)
    count,labels,stats,_=cv2.connectedComponentsWithStats(red.astype(np.uint8),8)
    contacts=np.bincount(labels[c.dilate(white,11)>0],minlength=count)
    ids=[i for i in range(1,count) if stats[i,4]>100 and contacts[i]>20]
    body=white|np.isin(labels,ids).astype(np.uint8)*255
    ink=(src.max(2)<110)&(c.dilate(body,9)>0)
    body|=ink.astype(np.uint8)*255
    from scipy.ndimage import binary_fill_holes
    return binary_fill_holes(body>0).astype(np.uint8)*255

'''
s=s[:a]+new+s[b:]
s=s.replace('for n in [600,601,602,603,605,606,612,620,1082,1084,1088]:','for n in [1082,1084,1087,1088,1089,1090]:')
p.write_text(s,encoding='utf-8')
print('Fullcanvas rabbit matte locked')


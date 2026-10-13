"""Non-art v7 local fixes; no writes to old project."""
def restore_ahoge(out, src, n, v6):
    c,f,v4=v6.c,v6.f,v6.v4
    shot=dict(next(s for s in f.SHOTS if s['start']<=n<s['end']))
    shot['roi']=(1080,0,1920,1080)
    rebuilt=v4.scene(src,n,shot,cup=False)
    rebuilt,count=v6.all_hands(rebuilt,src,n)
    return rebuilt,{'ahoge_roi_expanded':True,'roi':[1080,0,1920,1080],'adopted_joint_cup_cel':True,'hand_pixels':count}

def unify_face_hand_skin(out, src, n, v6):
    c,f,v4=v6.c,v6.f,v6.v4
    shot=dict(next(s for s in f.SHOTS if s['start']<=n<s['end']))
    rebuilt=v4.scene(src,n,shot)
    im,gm=f.layer(shot['asset'],tuple(shot.get('roi',f.FULL)),shot.get('border',False))
    track=v6.v2.TRACKS.get(shot['start'],shot.get('track'))
    matrix=c.tracking(c.reference(shot['ref']),src,track,n) if track else v6.np.float32([[1,0,0],[0,1,0]])
    owned=c.warp(gm,matrix,True)>0
    mask=v6.skin(rebuilt)&owned
    rebuilt,count=v6.grade(rebuilt,mask)
    return rebuilt,{'rebuilt_before_rectangular_grade':True,'character_skin_shared_palette':True,'skin_pixels':count}

if __name__=='__main__':
    import sys,json
    from pathlib import Path
    sys.dont_write_bytecode=True
    old=Path('<ORIGINAL_WORKSPACE>/work/trick-heart-project')
    here=Path('<REVISION_WORKSPACE>/work/audit-mask')
    sys.path.insert(0,str(old.parent/'python_lib'))
    sys.path.insert(0,str(old/'tools'))
    import revision6_composite as v6
    from PIL import Image,ImageDraw
    import numpy as np
    v6.cv2.setNumThreads(1)
    report=[]
    for n in [1401,1440,1466,2367,2388,2400]:
        src=v6.src(n)
        prior=v6.c.read(old/f'runs/paired-v6/frames/final/{n:05d}.png')
        after,meta=restore_ahoge(prior,src,n,v6) if n<2000 else unify_face_hand_skin(prior,src,n,v6)
        Image.fromarray(after).save(here/f'fix-{n:05d}.png')
        pair=Image.new('RGB',(1920,570),'#172029')
        d=ImageDraw.Draw(pair)
        d.text((5,5),f'v6 frame {n}',fill='white')
        d.text((965,5),f'v7 mask fix frame {n}',fill='white')
        pair.paste(Image.fromarray(prior).resize((960,540)),(0,30))
        pair.paste(Image.fromarray(after).resize((960,540)),(960,30))
        pair.save(here/f'compare-{n:05d}.jpg',quality=98)
        changed=np.any(prior!=after,axis=2)
        meta['frame']=n
        meta['changed_pixels']=int(changed.sum())
        meta['changed_below_y110']=int(changed[110:].sum()) if n<2000 else None
        report.append(meta)
    (here/'non-art-fix-review.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


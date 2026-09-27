"""Render source-specific scoring regions, without resampling annotation coordinates."""
import json,gzip
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def load(folder):
    m=json.loads((folder/'manifest.json').read_text())
    return m,np.frombuffer(gzip.decompress((folder/'volume.i16.gz').read_bytes()),'<i2').reshape(m['dimensions'],order='F')
def render(m,v,t,normal,outline=True):
    r=t['regions'][0];plane=r['plane'];axis={'axial':2,'coronal':1,'sagittal':0}[plane]
    i=round((normal-m['originLPS'][axis])/m['spacing'][axis]);i=max(0,min(i,v.shape[axis]-1))
    a=v[:,:,i].T if plane=='axial' else v[:,i,:].T[::-1] if plane=='coronal' else v[i,:,:].T[::-1]
    width=t['representative']['width'];level=t['representative']['level'];lo=level-.5-(width-1)/2
    im=Image.fromarray(np.uint8(np.clip((a-lo)/max(1,width-1),0,1)*255)).convert('RGB')
    if outline:
        points=[]
        for u,w in r['polygon']:
            if plane=='axial':x=(u-m['originLPS'][0])/m['spacing'][0];y=(w-m['originLPS'][1])/m['spacing'][1]
            else:x=(u-m['originLPS'][0 if plane=='coronal' else 1])/m['spacing'][0 if plane=='coronal' else 1];y=v.shape[2]-1-(-w-m['originLPS'][2])/m['spacing'][2]
            points.append((x,y))
        ImageDraw.Draw(im).polygon(points,outline='#73e8c0',width=1)
    axes={'axial':(0,1),'coronal':(0,2),'sagittal':(1,2)}[plane]
    ratio=(a.shape[0]*m['spacing'][axes[1]])/(a.shape[1]*m['spacing'][axes[0]])
    return im.resize((250,round(250*ratio)))
if __name__=='__main__':
    folder=ROOT/'cases/normal-head';m,v=load(folder);bm,bv=load(folder/'bone');c=json.loads((folder/'checkpoints.json').read_text());out=ROOT/'qa/contact-sheets';out.mkdir(parents=True,exist_ok=True)
    for p in c['phases']:
        canvas=Image.new('RGB',(1040,len(p['targets'])*290),'#0b1012');d=ImageDraw.Draw(canvas)
        for row,t in enumerate(p['targets']):
            r=t['regions'][0];rep=t['representative'];axis={'axial':2,'coronal':1,'sagittal':0}[r['plane']];n=rep['patient'][axis];mm,vv=(bm,bv) if rep['width']>1000 else (m,v)
            for col,(pos,outline) in enumerate([(n,False),(r['normal'][0],True),(n,True),(r['normal'][1],True)]):canvas.paste(render(mm,vv,t,pos,outline),(col*260,row*290+25))
            d.text((5,row*290+5),t['id']+' '+t['label']+' | '+r['plane']+' | clean / lower / centre / upper',fill='#cde0e1')
        canvas.save(out/(p['id']+'.jpg'),quality=88)
    print('Rendered',len(c['phases']),'phase sheets, all interval endpoints included')

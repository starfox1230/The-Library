"""Prepare regular CT geometry without copying source patient metadata."""
import argparse, gzip, hashlib, io, itertools, json, tarfile
from pathlib import Path
import numpy as np

def stack_slices(slices):
    if len(slices)<2: raise ValueError('At least two CT slices are required')
    first=slices[0]; orient=np.asarray(first.ImageOrientationPatient,float)
    normal=np.cross(orient[:3],orient[3:])
    slices=sorted(slices,key=lambda d:np.dot(d.ImagePositionPatient,normal))
    positions=np.array([d.ImagePositionPatient for d in slices],float)
    delta=np.diff(positions,axis=0); step=np.median(delta,axis=0)
    if np.linalg.norm(step)<0.01 or not np.allclose(delta,step,atol=.01):
        raise ValueError('Duplicate or nonuniform slice positions')
    for d in slices:
        if not np.allclose(d.ImageOrientationPatient,orient,atol=1e-5):raise ValueError('Inconsistent orientation')
        if not np.allclose(d.PixelSpacing,first.PixelSpacing):raise ValueError('Inconsistent pixel spacing')
        if d.SeriesInstanceUID!=first.SeriesInstanceUID:raise ValueError('Mixed series')
    v=np.stack([np.asarray(d.pixel_array,float).T*float(getattr(d,'RescaleSlope',1))+float(getattr(d,'RescaleIntercept',0)) for d in slices],axis=2)
    a=np.eye(4);a[:3,0]=orient[:3]*float(first.PixelSpacing[1]);a[:3,1]=orient[3:]*float(first.PixelSpacing[0]);a[:3,2]=step;a[:3,3]=positions[0]
    return v,a

def normalize_volume(values,affine_lps,spacing=None):
    v=np.asarray(values);a=np.asarray(affine_lps,float)
    if v.ndim!=3 or a.shape!=(4,4) or not np.isfinite(a).all() or abs(np.linalg.det(a[:3,:3]))<1e-8:raise ValueError('Invalid physical geometry')
    if not np.allclose(a[3],[0,0,0,1]):raise ValueError('Invalid affine bottom row')
    corners=np.array(list(itertools.product(*[(0,n-1) for n in v.shape])))
    points=corners@a[:3,:3].T+a[:3,3];origin=points.min(axis=0)
    s=np.asarray(spacing if spacing is not None else np.linalg.norm(a[:3,:3],axis=0),float)
    if s.shape!=(3,) or not np.isfinite(s).all() or (s<=0).any():raise ValueError('Invalid spacing')
    shape=np.ceil((points.max(axis=0)-origin)/s-1e-7).astype(int)+1
    if np.prod(shape)>200_000_000:raise ValueError('Output volume too large')
    inv=np.linalg.inv(a);out=np.full(tuple(shape),-1000,dtype=np.float32)
    xx,yy=np.meshgrid(np.arange(shape[0])*s[0]+origin[0],np.arange(shape[1])*s[1]+origin[1],indexing='ij')
    for z in range(shape[2]):
        p=np.stack([xx,yy,np.full_like(xx,z*s[2]+origin[2])],axis=-1)
        q=p@inv[:3,:3].T+inv[:3,3]
        valid=np.all((q>=-1e-6)&(q<=np.array(v.shape)-1+1e-6),axis=-1)
        q=np.clip(q,0,np.array(v.shape)-1);lo=np.floor(q).astype(int);hi=np.minimum(lo+1,np.array(v.shape)-1);f=q-lo
        plane=np.zeros(xx.shape,dtype=np.float32)
        for bits in itertools.product((0,1),repeat=3):
            idx=[hi[...,j] if bits[j] else lo[...,j] for j in range(3)]
            weight=np.prod([f[...,j] if bits[j] else 1-f[...,j] for j in range(3)],axis=0)
            plane+=v[tuple(idx)]*weight
        out[:,:,z]=np.where(valid,plane,-1000)
    return out,s,origin

def write_case(values_lps,spacing,origin_lps,metadata,output_dir):
    v=np.rint(values_lps)
    if not np.isfinite(v).all() or v.min()<-32768 or v.max()>32767:raise ValueError('HU exceeds int16')
    raw=v.astype('<i2').tobytes(order='F');compressed=gzip.compress(raw,mtime=0)
    if gzip.decompress(compressed)!=raw:raise ValueError('Compression verification failed')
    p=Path(output_dir);p.mkdir(parents=True,exist_ok=True)
    (p/'volume.i16.gz').write_bytes(compressed)
    manifest=dict(metadata,dimensions=list(v.shape),spacing=list(spacing),originLPS=list(origin_lps),volumeUrl='volume.i16.gz',encoding='gzip-i16le-hu',sha256=hashlib.sha256(raw).hexdigest())
    (p/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

def read_archive(path,series_number):
    import pydicom
    slices=[]
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if not member.isfile():continue
            try:d=pydicom.dcmread(io.BytesIO(archive.extractfile(member).read()))
            except pydicom.errors.InvalidDicomError:continue
            if getattr(d,'Modality','')=='CT' and str(getattr(d,'SeriesNumber',''))==str(series_number):slices.append(d)
    return slices

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('metadata');p.add_argument('output');p.add_argument('--series',required=True);p.add_argument('--spacing',nargs=3,type=float)
    args=p.parse_args();v,a=stack_slices(read_archive(args.archive,args.series));v,s,o=normalize_volume(v,a,args.spacing)
    result=write_case(v,s,o,json.loads(Path(args.metadata).read_text()),args.output)
    print(json.dumps({k:result[k] for k in ['dimensions','spacing','originLPS','sha256']}))

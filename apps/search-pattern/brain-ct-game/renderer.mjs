import {AXES,planeBounds,project,createViewTransform} from './geometry.mjs';
export function windowHU(hu,width,level){
 if(!Number.isFinite(width)||width<1||!Number.isFinite(level))throw Error('Invalid window width / level');
 const low=level-.5-(width-1)/2,high=level-.5+(width-1)/2;
 if(hu<=low)return 0;if(hu>high)return 255;return Math.round(((hu-(level-.5))/(width-1)+.5)*255);
}
export function sampleHU({manifest:m,values},patient){
 const q=patient.map((x,i)=>(x-m.originLPS[i])/m.spacing[i]);
 if(q.some((x,i)=>x<0||x>m.dimensions[i]-1))return -1000;
 const l=q.map(Math.floor),h=l.map((x,i)=>Math.min(x+1,m.dimensions[i]-1)),f=q.map((x,i)=>x-l[i]);let result=0;
 for(let b=0;b<8;b++){let w=1;const c=[];for(let i=0;i<3;i++){const bit=(b>>i)&1;c.push(bit?h[i]:l[i]);w*=bit?f[i]:1-f[i];}result+=w*values[c[0]+m.dimensions[0]*(c[1]+m.dimensions[1]*c[2])];}
 return result;
}
export function sampleSlice({manifest:m,values},plane,normalMm){
 const [u,v,n]=AXES[plane],width=m.dimensions[u],height=m.dimensions[v];
 const slice=Math.max(0,Math.min(m.dimensions[n]-1,Math.round((normalMm-m.originLPS[n])/m.spacing[n])));
 const hu=new Int16Array(width*height),stride=[1,m.dimensions[0],m.dimensions[0]*m.dimensions[1]],reverse=plane!=='axial';
 for(let y=0;y<height;y++){const base=slice*stride[n]+(reverse?height-1-y:y)*stride[v];for(let x=0;x<width;x++)hu[y*width+x]=values[base+x*stride[u]];}
 return {hu,width,height,bounds:planeBounds(m,plane),slice};
}
const caches=new WeakMap();
export function paintViewport(canvas,volume,view,overlay={}){
 const rect=canvas.getBoundingClientRect(),dpr=globalThis.devicePixelRatio||1;
 const W=Math.max(1,Math.round(rect.width*dpr)),H=Math.max(1,Math.round(rect.height*dpr));
 if(canvas.width!==W||canvas.height!==H){canvas.width=W;canvas.height=H;}
 let cache=caches.get(canvas);if(!cache){cache={off:document.createElement('canvas')};caches.set(canvas,cache);}
 const normal=project(view.focus,view.plane)[2],n=AXES[view.plane][2];
 const index=Math.round((normal-volume.manifest.originLPS[n])/volume.manifest.spacing[n]);
 const key=[view.plane,index,view.width,view.level].join(':');
 if(cache.key!==key||cache.volume!==volume){
  const slice=sampleSlice(volume,view.plane,normal);cache.off.width=slice.width;cache.off.height=slice.height;
  const ctx=cache.off.getContext('2d'),pixels=ctx.createImageData(slice.width,slice.height);
  const low=view.level-.5-(view.width-1)/2,range=Math.max(1,view.width-1);
  for(let i=0;i<slice.hu.length;i++){const b=Math.max(0,Math.min(255,Math.round((slice.hu[i]-low)/range*255))),j=i*4;pixels.data[j]=pixels.data[j+1]=pixels.data[j+2]=b;pixels.data[j+3]=255;}
  ctx.putImageData(pixels,0,0);cache.key=key;cache.volume=volume;cache.bounds=slice.bounds;
 }
 const t=createViewTransform({width:rect.width,height:rect.height,bounds:cache.bounds,zoom:view.zoom,pan:view.pan});
 const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#050708';ctx.fillRect(0,0,rect.width,rect.height);
 const [l,top,r,b]=cache.bounds,[x,y]=t.toScreen([l,top]),[x2,y2]=t.toScreen([r,b]);
 ctx.imageSmoothingEnabled=true;ctx.drawImage(cache.off,x,y,x2-x,y2-y);
 if(overlay.crosshairs){const [u,v]=project(view.focus,view.plane),[cx,cy]=t.toScreen([u,v]);ctx.strokeStyle='#83aaa966';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(cx,0);ctx.lineTo(cx,rect.height);ctx.moveTo(0,cy);ctx.lineTo(rect.width,cy);ctx.stroke();}
 if(overlay.region){ctx.beginPath();overlay.region.polygon.forEach((p,i)=>{const q=t.toScreen(p);i?ctx.lineTo(...q):ctx.moveTo(...q);});ctx.closePath();ctx.fillStyle='#8ed3b629';ctx.fill();ctx.strokeStyle='#8ed3b6';ctx.lineWidth=1.5;ctx.stroke();}
 const labels=view.plane==='axial'?['R','L','A','P']:view.plane==='coronal'?['R','L','S','I']:['A','P','S','I'];
 ctx.fillStyle='#91a4a9';ctx.font='11px system-ui';ctx.textAlign='center';ctx.fillText(labels[0],14,rect.height/2);ctx.fillText(labels[1],rect.width-14,rect.height/2);ctx.fillText(labels[2],rect.width/2,16);ctx.fillText(labels[3],rect.width/2,rect.height-10);
 return t;
}

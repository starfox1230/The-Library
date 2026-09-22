export const PLANES=['axial','sagittal','coronal'];
export const AXES={axial:[0,1,2],coronal:[0,2,1],sagittal:[1,2,0]};
export function project([x,y,z],plane){
 if(plane==='axial')return [x,y,z];if(plane==='coronal')return [x,-z,y];if(plane==='sagittal')return [y,-z,x];throw Error('Unknown plane');
}
export function unproject([u,v,n],plane){
 if(plane==='axial')return [u,v,n];if(plane==='coronal')return [u,n,-v];if(plane==='sagittal')return [n,u,-v];throw Error('Unknown plane');
}
export function planeBounds(m,plane){
 const p=m.originLPS.map((x,i)=>x-m.spacing[i]/2);
 const q=m.originLPS.map((x,i)=>x+m.spacing[i]*(m.dimensions[i]-.5));
 const a=project(p,plane),b=project(q,plane);
 return [Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[0],b[0]),Math.max(a[1],b[1])];
}
export function clampFocus(patient,m){return patient.map((x,i)=>Math.max(m.originLPS[i],Math.min(x,m.originLPS[i]+(m.dimensions[i]-1)*m.spacing[i])));}
export function createViewTransform({width,height,bounds,zoom=1,pan=[0,0]}){
 const [l,t,r,b]=bounds,scale=Math.min(width/(r-l),height/(b-t))*zoom;
 const cx=(l+r)/2,cy=(t+b)/2,ox=width/2+pan[0],oy=height/2+pan[1];
 return {scale,toScreen:([u,v])=>[(u-cx)*scale+ox,(v-cy)*scale+oy],toPlane:([x,y])=>[(x-ox)/scale+cx,(y-oy)/scale+cy]};
}

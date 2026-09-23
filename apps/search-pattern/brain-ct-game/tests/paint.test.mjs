import test from 'node:test';
import assert from 'node:assert/strict';
import {paintViewport} from '../renderer.mjs';
test('actual painted pixels respect width-one binary threshold',()=>{
 let pixels;
 const ctx={createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:p=>pixels=p.data,setTransform(){},fillRect(){},drawImage(){},fillText(){}};
 const previous=globalThis.document;
 globalThis.document={createElement:()=>({getContext:()=>ctx})};
 try{
  const canvas={getBoundingClientRect:()=>({width:100,height:100}),getContext:()=>ctx};
  const manifest={dimensions:[3,1,1],spacing:[1,1,1],originLPS:[0,0,0]};
  paintViewport(canvas,{manifest,values:new Int16Array([39,40,41])},{plane:'axial',focus:[0,0,0],width:1,level:40,zoom:1,pan:[0,0]});
  assert.deepEqual([pixels[0],pixels[4],pixels[8]],[0,255,255]);
 }finally{globalThis.document=previous;}
});

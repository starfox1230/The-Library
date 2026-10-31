/* A perspective laser-wave tunnel: broad frequency bands drive travelling harmonics.
   Stylized waveforms, not a reconstruction of raw audio samples. */
(() => {
 'use strict';if(window.AfterglowWaves)return;
 const palettes={neon:[[.02,.95,1.],[.85,.04,1.],[.4,1.,.04]],aurora:[[.05,.95,.85],[.45,.12,1.],[1.,.08,.6]],acid:[[.45,1.,.04],[.03,.9,.7],[1.,.25,.02]],ultraviolet:[[.12,.35,1.],[.6,.05,1.],[1.,.08,.65]],ember:[[1.,.12,.015],[1.,.65,.03],[.6,.05,1.]]};
 function seeds(count){const data=new Float32Array(count*6),segments=count/12;for(let i=0;i<count;i++){const ring=Math.floor(i/segments),j=i%segments;data.set([j/segments,ring,0,(j+1)/segments,ring,1],i*6);}return data;}
 const vertex=`precision highp float;
 attribute vec3 seed;uniform vec2 viewSize,worldSize,offset;
 uniform float time,beat,impact,density,bands[8];uniform lowp float pointMode;
 uniform vec3 c0,c1,c2;varying mediump vec3 color;varying mediump float opacity;
 void main(){
  float theta=seed.x*6.2831853,ring=seed.y;
  float low=bands[0]*.6+bands[1]*.4,mid=(bands[2]+bands[3]+bands[4])/3.,high=(bands[5]+bands[6]+bands[7])/3.;
  float phase=time*2.4+ring*.42;
  float wave=low*.15*sin(theta*3.+phase)+mid*.095*sin(theta*8.-phase*1.3)+high*.055*sin(theta*19.+phase*2.);
  float radius=1.35+impact*wave+beat*(.10+.045*sin(theta*5.-phase*2.+ring*.4));
  radius+=.006*sin(theta*4.+time+ring);
  // Each hoop travels from the vanishing point toward the viewer. Its fade
  // hides the wrap at either end, so a new hoop never teleports across the view.
  float depth=1.1+mod(ring-mod(time*.8,12.)+12.,12.);
  float fade=smoothstep(1.1,1.85,depth)*(1.-smoothstep(11.8,13.1,depth));
  depth=max(.9,depth-beat*.16);
  float angle=theta+time*.04;
  vec2 p=vec2(cos(angle),sin(angle))*radius;
  vec2 pixel=worldSize*vec2(.5,.53)+p*worldSize.y*.83/depth;
  vec2 local=(pixel-offset)/viewSize;gl_Position=vec4(local.x*2.-1.,1.-local.y*2.,0.,1.);
  float hue=fract(seed.x*.45+ring*.055+time*.012);
  color=mix(c0,c1,smoothstep(0.,.5,hue));color=mix(color,c2,smoothstep(.5,1.,hue));
  color=mix(color,vec3(.94,.87,1.),.25+beat*.15);
  opacity=fade*(pointMode>.5?.70:1.)*(.8+low*.2+beat*.4);
  gl_PointSize=clamp((14.+beat*8.+high*2.)*density*(1.3+8./depth),4.,64.);
 }`;
 const fragment=`precision mediump float;uniform lowp float pointMode;uniform float intensity;
 varying mediump vec3 color;varying mediump float opacity;
 void main(){float a=opacity;if(pointMode>.5){vec2 p=gl_PointCoord*2.-1.;float r=dot(p,p);if(r>1.)discard;a*=exp(-r*90.)*.8+exp(-r*5.)*.045;}gl_FragColor=vec4(color,a*intensity);}`;
 function gpu(canvas,gl){let program,buffer,attribute,count=0,loc={},alive=true;
  function init(){const compile=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
   const vs=compile(gl.VERTEX_SHADER,vertex),fs=compile(gl.FRAGMENT_SHADER,fragment);program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);gl.deleteShader(vs);gl.deleteShader(fs);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
   for(const key of ['viewSize','worldSize','offset','time','beat','impact','density','pointMode','intensity','bands[0]','c0','c1','c2'])loc[key]=gl.getUniformLocation(program,key);
   buffer=gl.createBuffer();attribute=gl.getAttribLocation(program,'seed');count=0;alive=true;
  }
  init();const ext=gl.getExtension('WEBGL_debug_renderer_info');
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();alive=false;});canvas.addEventListener('webglcontextrestored',()=>{try{init();}catch(_){alive=false;}});
  return {canvas,kind:'webgl',get particles(){return count;},info:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'WebGL',dispose(){gl.getExtension('WEBGL_lose_context')?.loseContext();},draw(s){
   if(!alive)return;const desired=Math.round(Math.max(600,Math.min(s.quality?3600:1200,s.particleCount??1800))/12)*12;
   gl.useProgram(program);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);if(count!==desired){count=desired;gl.bufferData(gl.ARRAY_BUFFER,seeds(count),gl.STATIC_DRAW);}
   gl.enableVertexAttribArray(attribute);gl.vertexAttribPointer(attribute,3,gl.FLOAT,false,12,0);gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.010,.004,.027,1);gl.clear(gl.COLOR_BUFFER_BIT);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
   gl.uniform2f(loc.viewSize,s.vw,s.vh);gl.uniform2f(loc.worldSize,s.w,s.h);gl.uniform2f(loc.offset,s.x,s.y);
   gl.uniform1f(loc.time,s.clubTime??s.time);gl.uniform1f(loc.beat,Math.min(1,s.clubBeat??s.pulse??0));gl.uniform1f(loc.impact,s.waveImpact??.9);gl.uniform1f(loc.density,canvas.width/s.vw);gl.uniform1f(loc.intensity,s.intensity*1.4);
   gl.uniform1fv(loc['bands[0]'],new Float32Array(s.waveBands||Array(8).fill(0)));const colors=palettes[s.palette]||palettes.neon;for(let i=0;i<3;i++)gl.uniform3fv(loc['c'+i],colors[i]);
   gl.uniform1f(loc.pointMode,0);gl.drawArrays(gl.LINES,0,count*2);gl.vertexAttribPointer(attribute,3,gl.FLOAT,false,24,0);gl.uniform1f(loc.pointMode,1);gl.drawArrays(gl.POINTS,0,count);
  }};
 }
 function cpu(canvas){const ctx=canvas.getContext('2d',{alpha:false});let count=0;
  return {canvas,kind:'canvas',get particles(){return count;},info:'Laser-wave tunnel (Canvas)',draw(s){
   const sx=canvas.width/s.vw,sy=canvas.height/s.vh,t=s.clubTime??s.time,k=Math.min(1,s.clubBeat??s.pulse??0),b=s.waveBands||Array(8).fill(0),impact=s.waveImpact??.9,colors=palettes[s.palette]||palettes.neon;
   const low=b[0]*.6+b[1]*.4,mid=(b[2]+b[3]+b[4])/3,high=(b[5]+b[6]+b[7])/3;
   const segments=Math.max(80,Math.min(200,Math.round((s.particleCount??1800)/12)));count=segments*12;
   ctx.setTransform(sx,0,0,sy,-s.x*sx,-s.y*sy);ctx.fillStyle='#030107';ctx.fillRect(0,0,s.w,s.h);ctx.globalCompositeOperation='screen';
   for(let ring=0;ring<12;ring++){
    const originalDepth=1.1+((ring-t*.8)%12+12)%12,depth=Math.max(.9,originalDepth-k*.16);
    const fade=Math.max(0,Math.min(1,(originalDepth-1.1)/.75,(13.1-originalDepth)/1.3));
    ctx.beginPath();const color=colors[ring%3].map(v=>v*.75+.25);ctx.strokeStyle=`rgb(${color.map(v=>Math.round(v*255)).join(',')})`;
    for(let j=0;j<=segments;j++){
     const theta=j/segments*Math.PI*2,phase=t*2.4+ring*.42;
     const wave=low*.15*Math.sin(theta*3+phase)+mid*.095*Math.sin(theta*8-phase*1.3)+high*.055*Math.sin(theta*19+phase*2);
     const r=1.35+impact*wave+k*(.10+.045*Math.sin(theta*5-phase*2+ring*.4))+.006*Math.sin(theta*4+t+ring),a=theta+t*.04;
     const x=s.w*.5+Math.cos(a)*r*s.h*.83/depth,y=s.h*.53+Math.sin(a)*r*s.h*.83/depth;if(!j)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.lineWidth=12/depth+3;ctx.globalAlpha=s.intensity*.12*fade;ctx.stroke();ctx.lineWidth=1.2+k*.7;ctx.globalAlpha=Math.min(1,s.intensity*(.8+low*.2+k*.4))*fade;ctx.stroke();
   }
   ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
  }};
 }
 window.AfterglowWaves=canvas=>{try{const gl=canvas.getContext('webgl',{alpha:false,depth:false,stencil:false,antialias:false,preserveDrawingBuffer:false,powerPreference:'high-performance'});if(gl)return gpu(canvas,gl);}catch(e){console.warn('Afterglow wave fallback:',String(e));const next=canvas.cloneNode();canvas.replaceWith(next);canvas=next;}return cpu(canvas);};
})();

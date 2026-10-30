/* Original GPU particle cloud inspired by the supplied tutorial's principles.
   Persistent seeded trajectories advance on integrated audio clocks; amplitude
   never directly rescales positions. Two batched draws, no per-frame uploads. */
(() => {
  'use strict';
  if(window.AfterglowParticles)return;
  const palettes={aurora:[[.08,.85,.90],[.45,.20,1.],[.96,.22,.58]],acid:[[.15,.85,.55],[.72,.95,.12],[1.,.45,.08]],ultraviolet:[[.22,.42,1.],[.60,.20,.96],[1.,.20,.58]],ember:[[1.,.19,.035],[1.,.70,.10],[.60,.18,1.]]};
  function seeds(count){
    const data=new Float32Array(count*10);let seed=73129;
    const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
    for(let i=0;i<count;i++){const values=[random(),random(),random(),random()];for(let tail=0;tail<2;tail++){data.set(values,i*10+tail*5);data[i*10+tail*5+4]=tail;}}
    return data;
  }
  const vertex=`precision highp float;
attribute vec4 seed;attribute float head;
uniform vec2 viewSize,worldSize,offset;uniform float times[8],camera,density;uniform lowp float pointMode;
uniform vec3 c0,c1,c2;varying mediump vec3 color;varying mediump float opacity;
vec3 path(float age){
 float angle=seed.y*6.2831853,phi=seed.z*2.-1.,radius=.27*pow(seed.x,.3333);
 vec3 p=radius*vec3(sqrt(1.-phi*phi)*cos(angle),phi,sqrt(1.-phi*phi)*sin(angle));
 p.x+=.70*(sin(angle+age*.43)-sin(angle))+.022*age*sin(seed.w*19.);
 p.y+=age*.105+.35*(sin(age*.24+angle)-sin(angle));
 p.z+=.70*(cos(angle+age*.37)-cos(angle))+.022*age*cos(seed.w*17.);
 return p;
}
void main(){
 int group=int(floor(seed.z*7.999));float clock=0.;for(int i=0;i<8;i++){if(i==group)clock=times[i];}
 float life=14.+seed.x*6.,age=mod(clock*2.2+seed.w*life,life);
 vec3 p=path(max(0.,age-(1.-head)*.11));p.y-=.85;
 float yaw=camera,pitch=.16*sin(camera*.43)+.08;
 p=vec3(cos(yaw)*p.x+sin(yaw)*p.z,p.y,-sin(yaw)*p.x+cos(yaw)*p.z);
 p=vec3(p.x,cos(pitch)*p.y-sin(pitch)*p.z,sin(pitch)*p.y+cos(pitch)*p.z);
 float depth=4.4-p.z;vec2 pixel=worldSize*vec2(.5,.52)+vec2(p.x,-p.y)*worldSize.y*1.42/depth;
 vec2 local=(pixel-offset)/viewSize;
 gl_Position=vec4(local.x*2.-1.,1.-local.y*2.,0.,1.);
 float a=age/life;color=mix(c0,c1,smoothstep(.05,.65,a));color=mix(color,c2,smoothstep(.50,1.,a));
 opacity=smoothstep(0.,.10,a)*(1.-smoothstep(.75,1.,a));
 opacity*=pointMode>.5?.42:mix(.025,.75,head);
 gl_PointSize=clamp((4.2/depth+1.2)*density,1.,4.5);
}`;
  const fragment=`precision mediump float;uniform lowp float pointMode;uniform float intensity;varying mediump vec3 color;varying mediump float opacity;
void main(){float a=opacity;if(pointMode>.5){vec2 p=gl_PointCoord*2.-1.;a*=pow(max(0.,1.-dot(p,p)),2.);}gl_FragColor=vec4(color*1.15,a*intensity);}`;
  function gpu(canvas,gl){
    let program,buffer,loc={},count=0,alive=true;
    function init(){
      const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
      const vs=compile(gl.VERTEX_SHADER,vertex),fs=compile(gl.FRAGMENT_SHADER,fragment);
      program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);gl.deleteShader(vs);gl.deleteShader(fs);
      if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
      buffer=gl.createBuffer();count=0;
      for(const key of ['viewSize','worldSize','offset','camera','pointMode','density','intensity','c0','c1','c2','times[0]'])loc[key]=gl.getUniformLocation(program,key);
      alive=true;
    }
    init();
    canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();alive=false;});
    canvas.addEventListener('webglcontextrestored',()=>{try{init();}catch(_){alive=false;}});
    const ext=gl.getExtension('WEBGL_debug_renderer_info');
    return {canvas,kind:'webgl',info:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'WebGL',dispose(){gl.getExtension('WEBGL_lose_context')?.loseContext();},draw(s){
      if(!alive)return;const desired=s.quality?12000:5000;
      gl.useProgram(program);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
      if(count!==desired){count=desired;gl.bufferData(gl.ARRAY_BUFFER,seeds(count),gl.STATIC_DRAW);}
      const a=gl.getAttribLocation(program,'seed'),b=gl.getAttribLocation(program,'head');
      gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,4,gl.FLOAT,false,20,0);gl.enableVertexAttribArray(b);gl.vertexAttribPointer(b,1,gl.FLOAT,false,20,16);
      gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.005,.008,.021,1);gl.clear(gl.COLOR_BUFFER_BIT);
      gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
      gl.uniform2f(loc.viewSize,s.vw,s.vh);gl.uniform2f(loc.worldSize,s.w,s.h);gl.uniform2f(loc.offset,s.x,s.y);
      gl.uniform1f(loc.camera,s.camera??s.time*.12);gl.uniform1f(loc.density,canvas.width/s.vw);
      gl.uniform1fv(loc['times[0]'],new Float32Array(s.clocks||Array(8).fill(s.time)));
      gl.uniform1f(loc.intensity,s.intensity*(.85+s.level*.15));
      const palette=palettes[s.palette]||palettes.aurora;for(let i=0;i<3;i++)gl.uniform3fv(loc['c'+i],palette[i]);
      gl.uniform1f(loc.pointMode,0);gl.drawArrays(gl.LINES,0,count*2);
      gl.uniform1f(loc.pointMode,1);gl.drawArrays(gl.POINTS,0,count*2);
    }};
  }
  function cpu(canvas){
    const ctx=canvas.getContext('2d',{alpha:false}),data=seeds(900);
    return {canvas,kind:'canvas',info:'Simplified Canvas particles',draw(s){
      const sx=canvas.width/s.vw,sy=canvas.height/s.vh;ctx.setTransform(sx,0,0,sy,-s.x*sx,-s.y*sy);ctx.fillStyle='#020408';ctx.fillRect(0,0,s.w,s.h);
      const yaw=s.camera??s.time*.12,c=Math.cos(yaw),n=Math.sin(yaw),palette=palettes[s.palette]||palettes.aurora;
      ctx.globalCompositeOperation='screen';ctx.globalAlpha=s.intensity*.7;
      for(let i=0;i<900;i++){
        const k=i*10,a=data[k],b=data[k+1],d=data[k+2],phase=data[k+3],life=14+a*6,age=((s.clocks?.[Math.min(7,Math.floor(d*8))]??s.time)*2.2+phase*life)%life,angle=b*Math.PI*2;
        const x=.2*Math.cos(angle)+.7*(Math.sin(angle+age*.43)-Math.sin(angle)),y=age*.105+.35*(Math.sin(age*.24+angle)-Math.sin(angle))-.85,z=.2*Math.sin(angle)+.7*(Math.cos(angle+age*.37)-Math.cos(angle));
        const px=c*x+n*z,pz=-n*x+c*z,scale=s.h*1.42/(4.4-pz),u=age/life,color=palette[Math.min(2,Math.floor(u*3))];
        ctx.fillStyle=`rgb(${color.map(v=>Math.round(v*255)).join(',')})`;ctx.globalAlpha=s.intensity*Math.min(1,u/.1,(1-u)/.25)*.75;
        ctx.fillRect(s.w*.5+px*scale,s.h*.52-y*scale,1.3,1.3);
      }
      ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
    }};
  }
  window.AfterglowParticles=canvas=>{
    try{const gl=canvas.getContext('webgl',{alpha:false,depth:false,stencil:false,antialias:false,preserveDrawingBuffer:false,powerPreference:'high-performance'});if(gl)return gpu(canvas,gl);}
    catch(error){console.warn('Afterglow particle graphics fallback:',String(error));const next=canvas.cloneNode();canvas.replaceWith(next);canvas=next;}
    return cpu(canvas);
  };
})();

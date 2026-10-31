/* Original neon ribbon visual. One point-sprite draw, seeded geometry, no
   textures or dependencies. The beat changes position as well as light. */
(() => {
  'use strict';
  if(window.AfterglowClub)return;
  const palettes={aurora:[[.05,.95,.85],[.45,.12,1.],[1.,.08,.6]],acid:[[.45,1.,.04],[.03,.9,.7],[1.,.25,.02]],ultraviolet:[[.12,.35,1.],[.6,.05,1.],[1.,.08,.65]],ember:[[1.,.12,.015],[1.,.65,.03],[.6,.05,1.]],neon:[[.02,.95,1.],[.85,.04,1.],[.4,1.,.04]]};
  function seeds(count){
    const data=new Float32Array(count*4);let seed=29173;
    const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
    for(let i=0;i<count;i++)data.set([(i%240)/240,Math.floor(i/240),random(),random()],i*4);
    return data;
  }
  const vertex=`precision highp float;
attribute vec4 seed;
uniform vec2 viewSize,worldSize,offset;
uniform float time,beat,drive,density;uniform vec3 c0,c1,c2;
varying mediump vec3 color;varying mediump float opacity;
void main(){
 float strand=seed.y,theta=seed.x*6.2831853;
 float spin=time*.24+strand*.61;
 float a=theta+spin;
 float rip=sin(theta*3.+strand*1.4+time*.45);
 float radius=.56+mod(strand,4.)*.15+.075*rip;
 // Beats deform the ribbon and throw it outward, rather than just illuminating it.
 float kick=beat*(.28+.17*(.5+.5*sin(theta*4.-strand*.8)));
 radius+=kick;
 a+=beat*.26*sin(theta*2.+strand);
 vec3 p=vec3(cos(a)*radius,sin(a)*radius,
   .50*sin(theta*2.+strand*.77+time*.25)+.14*(mod(strand,3.)-1.)+beat*.38);
 p.xy+=vec2(.10*sin(time*.13+strand),.08*cos(time*.17+strand));
 float depth=3.2-p.z,zoom=2.8/depth;
 vec2 pixel=worldSize*.5+vec2(p.x*worldSize.x*.44,p.y*worldSize.y*.44)*zoom;
 vec2 local=(pixel-offset)/viewSize;
 gl_Position=vec4(local.x*2.-1.,1.-local.y*2.,0.,1.);
 float hue=fract(seed.x+strand*.17+time*.018);
 color=mix(c0,c1,smoothstep(0.,.5,hue));color=mix(color,c2,smoothstep(.5,1.,hue));
 color=mix(color,vec3(.8,.94,1.),beat*.16);
 // Gaps keep the ribbons airy, like beads in the supplied reference.
 float gap=smoothstep(.10,.36,sin(theta*5.+strand+time*.3)*.5+.5);
 opacity=gap*(.40+seed.w*.45)*(.6+drive*.25+beat*.75);
 gl_PointSize=clamp((4.+seed.z*4.+beat*5.)*zoom*density,1.,17.);
}`;
  const fragment=`precision mediump float;
uniform float intensity;varying mediump vec3 color;varying mediump float opacity;
void main(){vec2 p=gl_PointCoord*2.-1.;float r=dot(p,p);if(r>1.)discard;
 float core=exp(-r*16.),glow=pow(1.-r,2.)*.23;
 gl_FragColor=vec4(color*(.85+core*.4),(core+glow)*opacity*intensity);
}`;
  function gpu(canvas,gl){
    let program,buffer,count=0,loc={},alive=true,attribute;
    function init(){
      const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
      const vs=compile(gl.VERTEX_SHADER,vertex),fs=compile(gl.FRAGMENT_SHADER,fragment);
      program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);gl.deleteShader(vs);gl.deleteShader(fs);
      if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
      for(const key of ['viewSize','worldSize','offset','time','beat','drive','density','intensity','c0','c1','c2'])loc[key]=gl.getUniformLocation(program,key);
      attribute=gl.getAttribLocation(program,'seed');buffer=gl.createBuffer();count=0;alive=true;
    }
    init();const ext=gl.getExtension('WEBGL_debug_renderer_info');
    canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();alive=false;});
    canvas.addEventListener('webglcontextrestored',()=>{try{init();}catch(_){alive=false;}});
    return {canvas,kind:'webgl',get particles(){return count;},info:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'WebGL',dispose(){gl.getExtension('WEBGL_lose_context')?.loseContext();},draw(s){
      if(!alive)return;
      const desired=Math.round(Math.max(600,Math.min(s.quality?4200:1200,s.particleCount??1800)));
      gl.useProgram(program);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
      if(count!==desired){count=desired;gl.bufferData(gl.ARRAY_BUFFER,seeds(count),gl.STATIC_DRAW);}
      gl.enableVertexAttribArray(attribute);gl.vertexAttribPointer(attribute,4,gl.FLOAT,false,16,0);
      gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.003,.004,.018,1);gl.clear(gl.COLOR_BUFFER_BIT);
      gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
      gl.uniform2f(loc.viewSize,s.vw,s.vh);gl.uniform2f(loc.worldSize,s.w,s.h);gl.uniform2f(loc.offset,s.x,s.y);
      gl.uniform1f(loc.time,s.clubTime??s.time);gl.uniform1f(loc.beat,Math.min(1,s.clubBeat??s.pulse??0));
      gl.uniform1f(loc.drive,s.level||0);gl.uniform1f(loc.density,canvas.width/s.vw);gl.uniform1f(loc.intensity,s.intensity*1.4);
      const colors=palettes[s.palette]||palettes.neon;for(let i=0;i<3;i++)gl.uniform3fv(loc['c'+i],colors[i]);
      gl.drawArrays(gl.POINTS,0,count);
    }};
  }
  function cpu(canvas){
    const ctx=canvas.getContext('2d',{alpha:false});let count=0;
    return {canvas,kind:'canvas',info:'Simplified neon ribbons',get particles(){return count;},draw(s){
      const sx=canvas.width/s.vw,sy=canvas.height/s.vh,t=s.clubTime??s.time,k=Math.min(1,s.clubBeat??s.pulse??0),colors=palettes[s.palette]||palettes.neon;
      count=Math.min(650,Math.max(200,Math.round((s.particleCount??1800)/4)));
      ctx.setTransform(sx,0,0,sy,-s.x*sx,-s.y*sy);ctx.fillStyle='#010105';ctx.fillRect(0,0,s.w,s.h);ctx.globalCompositeOperation='screen';
      for(let i=0;i<count;i++){
        const strand=Math.floor(i/90),theta=(i%90)/90*Math.PI*2,a=theta+t*.24+strand*.61+k*.26*Math.sin(theta*2+strand);
        const radius=.56+(strand%4)*.15+.075*Math.sin(theta*3+strand*1.4+t*.45)+k*(.28+.17*(.5+.5*Math.sin(theta*4-strand*.8)));
        const zoom=2.8/(3.2-.5*Math.sin(theta*2+strand*.77+t*.25)-k*.38);
        const color=colors[Math.floor((i/90+t*.018)%3)];ctx.fillStyle=`rgb(${color.map(v=>Math.round(v*255)).join(',')})`;
        ctx.globalAlpha=Math.min(1,s.intensity*(.35+k*.65))*Math.max(0,Math.sin(theta*5+strand+t*.3)*.5+.5);
        ctx.beginPath();ctx.arc(s.w*.5+Math.cos(a)*radius*s.w*.44*zoom,s.h*.5+Math.sin(a)*radius*s.h*.44*zoom,(2+k*2)*zoom,0,Math.PI*2);ctx.fill();
      }
      ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
    }};
  }
  window.AfterglowClub=canvas=>{
    try{const gl=canvas.getContext('webgl',{alpha:false,depth:false,stencil:false,antialias:false,preserveDrawingBuffer:false,powerPreference:'high-performance'});if(gl)return gpu(canvas,gl);}
    catch(e){console.warn('Afterglow club fallback:',String(e));const next=canvas.cloneNode();canvas.replaceWith(next);canvas=next;}
    return cpu(canvas);
  };
})();

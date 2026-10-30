/* Original Afterglow renderer: a music-driven liquid color wall. No mouse input,
   third-party engine, remote assets, fluid-simulation buffers or geometry scene. */
(() => {
  'use strict';
  if(window.AfterglowLiquid)return;
  const colors={aurora:[[.04,.80,.76],[.48,.16,.92],[.92,.16,.52]],acid:[[.04,.70,.65],[.40,.85,.16],[.95,.48,.08]],ultraviolet:[[.46,.12,.90],[.12,.38,.91],[.90,.12,.57]],ember:[[1.,.19,.035],[1.,.70,.10],[.60,.18,1.]]};
  const hues={aurora:[180,270,330],acid:[165,90,35],ultraviolet:[270,225,320],ember:[12,42,270]};
  const vertex='attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}';
  const fragment=`
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 resolution,viewSize,worldSize,offset;
uniform float flow,energy,bass,push,intensity;
uniform vec3 c0,c1,c2;
float hash(vec2 p){vec3 q=fract(vec3(p.xyx)*vec3(.1031,.1137,.1379));q+=dot(q,q.yzx+19.19);return fract((q.x+q.y)*q.z);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
float field(vec2 p){float f=0.;float a=.57;for(int i=0;i<3;i++){f+=a*noise(p);p=mat2(1.64,-1.12,1.12,1.64)*p+vec2(3.1,7.3);a*=.47;}return f;}
void main(){
 vec2 pixel=vec2(gl_FragCoord.x,resolution.y-gl_FragCoord.y)/resolution*viewSize+offset;
 vec2 p=(pixel-worldSize*.5)/worldSize.y;
 float t=flow;
 p+=push*.075*vec2(sin(p.y*3.+t*.3),cos(p.x*3.-t*.2));
 vec2 drift=vec2(t*.12,-t*.085);
 vec2 q=vec2(field(p*1.4+drift),field(p*1.4+vec2(4.7,8.3)-drift*.7));
 vec2 r=vec2(field(p*1.7+q*(1.8+bass*.75)+vec2(1.3,t*.035)),field(p*1.7+q*1.6+vec2(8.1,3.7)-drift*.3));
 float liquid=field(p*1.9+r*2.0+q*.55);
 float bend=p.x*.78+p.y*.43+q.x*.65+r.y*1.4+liquid*.7-t*.065;
 float ribbon=.5+.5*sin(bend*6.8);
 float fold=pow(1.-abs(sin((bend+liquid*.12)*6.8)),7.);
 float pool=smoothstep(.15,.86,liquid);
 vec3 color=mix(c0,c1,smoothstep(.08,.92,ribbon));
 color=mix(color,c2,smoothstep(.46,.86,liquid+q.y*.18)*.72);
 // Preserve saturated light and deep troughs instead of washing the wall white
 // on every kick. Most beat response is fluid displacement and fold depth.
 float low=min(color.r,min(color.g,color.b));color=max(vec3(0.),color-low*.65);
 color/=max(.2,max(color.r,max(color.g,color.b)));
 float light=.10+pow(pool,1.8)*.80+fold*.30+energy*.08+push*.22;
 color*=intensity*light*(.78+.12*smoothstep(.05,1.1,length(p)));
 color=vec3(1.)-exp(-color*1.65);
 gl_FragColor=vec4(mix(vec3(.012,.017,.035),color,.96),1.);
}`;
  function gpu(canvas,gl){
    let program,loc={},ready=false;
    function init(){
      function compile(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));return s;}
      const vs=compile(gl.VERTEX_SHADER,vertex),fs=compile(gl.FRAGMENT_SHADER,fragment);
      program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);gl.deleteShader(vs);gl.deleteShader(fs);
      if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(program));
      gl.useProgram(program);const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
      const a=gl.getAttribLocation(program,'a');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
      for(const name of ['resolution','viewSize','worldSize','offset','flow','energy','bass','push','intensity','c0','c1','c2'])loc[name]=gl.getUniformLocation(program,name);
      ready=true;
    }
    init();
    canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();ready=false;});
    canvas.addEventListener('webglcontextrestored',()=>{try{init();}catch(_){ready=false;}});
    return {canvas,kind:'webgl',dispose(){gl.getExtension('WEBGL_lose_context')?.loseContext();},draw(s){
      if(!ready)return;
      gl.viewport(0,0,canvas.width,canvas.height);gl.useProgram(program);
      gl.uniform2f(loc.resolution,canvas.width,canvas.height);gl.uniform2f(loc.viewSize,s.vw,s.vh);gl.uniform2f(loc.worldSize,s.w,s.h);gl.uniform2f(loc.offset,s.x,s.y);
      for(const [key,value] of Object.entries({flow:s.time,energy:s.level,bass:s.bass,push:s.pulse,intensity:s.intensity}))gl.uniform1f(loc[key],value);
      const palette=colors[s.palette]||colors.aurora;
      for(let i=0;i<3;i++)gl.uniform3fv(loc['c'+i],palette[i]);
      gl.drawArrays(gl.TRIANGLES,0,6);
    }};
  }
  function cpu(canvas){
    const ctx=canvas.getContext('2d',{alpha:false});let cacheKey='',glows=[],bands=[];
    function cache(s){
      const key=s.palette+':'+s.w+':'+s.h;
      if(key===cacheKey)return;cacheKey=key;glows=[];bands=[];ctx.setTransform(1,0,0,1,0,0);
      for(const hue of hues[s.palette]||hues.aurora){
        const image=document.createElement('canvas');image.width=image.height=256;
        const c=image.getContext('2d'),g=c.createRadialGradient(128,128,0,128,128,128);
        g.addColorStop(0,`hsla(${hue},90%,58%,.9)`);g.addColorStop(.3,`hsla(${hue},90%,45%,.55)`);g.addColorStop(1,`hsla(${hue},90%,35%,0)`);c.fillStyle=g;c.fillRect(0,0,256,256);glows.push(image);
        const band=ctx.createLinearGradient(0,0,s.w,s.h);
        band.addColorStop(0,`hsla(${hue},85%,55%,.02)`);band.addColorStop(.45,`hsla(${hue},85%,50%,.40)`);band.addColorStop(1,`hsla(${hue+25},85%,60%,.04)`);bands.push(band);
      }
    }
    return {canvas,kind:'canvas',draw(s){
      cache(s);const {w,h,time:t}=s,sx=canvas.width/s.vw,sy=canvas.height/s.vh;
      ctx.setTransform(sx,0,0,sy,-s.x*sx,-s.y*sy);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.fillStyle='#060a18';ctx.fillRect(0,0,w,h);ctx.globalCompositeOperation='screen';
      for(let i=0;i<3;i++){
        const r=w*(.55+s.bass*.08),x=w*(.16+i*.34+.16*Math.sin(t*.20+i*2)),y=h*(.43+.26*Math.cos(t*.16+i*2));
        ctx.globalAlpha=Math.min(1,s.intensity*(.5+s.pulse*.65+s.level*.18));ctx.drawImage(glows[i],x-r,y-r*.65,r*2,r*1.3);
      }
      ctx.globalAlpha=s.intensity*(.65+s.pulse*.35);
      for(let i=0;i<7;i++){
        const y=h*(-.25+i*.25),a=h*(.28+s.bass*.16),b=Math.sin(t*.21+i)*a,c=Math.cos(t*.17+i*1.3)*a;
        ctx.beginPath();ctx.moveTo(-w*.15,y+b);ctx.bezierCurveTo(w*.2,y-a+c,w*.55,y+a+b,w*1.15,y+c);ctx.lineTo(w*1.15,y+h*.32+c);ctx.bezierCurveTo(w*.55,y+h*.32+a+b,w*.2,y+h*.32-a+c,-w*.15,y+h*.32+b);ctx.closePath();ctx.fillStyle=bands[i%3];ctx.fill();
      }
      ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
    }};
  }
  window.AfterglowLiquid=canvas=>{
    try{
      const gl=canvas.getContext('webgl',{alpha:false,depth:false,stencil:false,antialias:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
      if(gl)return gpu(canvas,gl);
    }catch(_){
      const replacement=canvas.cloneNode();canvas.replaceWith(replacement);canvas=replacement;
    }
    return cpu(canvas);
  };
})();

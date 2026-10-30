(() => {
  'use strict';
  if (window.Afterglow) return;
  const canvas = document.createElement('canvas');
  canvas.id = 'afterglow-canvas';
  canvas.hidden=true;
  canvas.setAttribute('aria-hidden', 'true');
  const ctx = canvas.getContext('2d', {alpha:false});
  const root = document.documentElement;
  let config = {enabled:false, intensity:65, motion:55, contrast:70, quality:1, palette:'aurora', clear_backgrounds:true, impact:80, immersive:true, show_meter:true};
  let state = {}, raf = 0, last = 0, time = 0, pulse = 0, level = 0, gain = .03, nextBeat = 0;
  let width = 1, height = 1, dirty = true, configKey = '';
  let surface=null, received=0, sceneAt=0, lastHit=0, attack=0, previousBass=0;
  let hud, meter, caption, meterTick=0;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const palettes = {aurora:[185,267,324], acid:[155,80,38], ultraviolet:[260,218,313]};
  const clamp = (v, a, b) => Math.max(a,Math.min(b,v));
  function mount() {
    if (!document.body) return;
    if (!canvas.isConnected) document.body.prepend(canvas);
    if (!hud) {
      hud=document.createElement('aside');hud.id='afterglow-meter';hud.hidden=true;hud.setAttribute('aria-live','off');
      caption=document.createElement('span');caption.textContent='Afterglow · Waiting for sound';
      const track=document.createElement('div');meter=document.createElement('i');track.append(meter);hud.append(caption,track);document.body.append(hud);
    }
  }
  function resize() {
    const scale = Math.min(1.25, devicePixelRatio || 1, 1440 / (surface?.width||innerWidth), 1000 / (surface?.height||innerHeight));
    const w = Math.max(1,Math.round(innerWidth * scale)), h = Math.max(1,Math.round(innerHeight * scale));
    if (canvas.width !== w || canvas.height !== h) {canvas.width=w;canvas.height=h;width=w;height=h;dirty=true;}
  }
  function protectText(refresh=false) {
    const qa = document.getElementById('qa') || (state.primary===false ? document.body : null);
    if (!qa || !config.enabled) return;
    for (const el of [qa,...qa.querySelectorAll('*')]) {
      if(el.closest('#afterglow-meter'))continue;
      if(!refresh && el.dataset.agTone)continue;
      if (!Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim())) continue;
      const color = getComputedStyle(el).color.match(/[\d.]+/g);
      if (!color || color.length < 3) continue;
      const lum = .2126 * +color[0] + .7152 * +color[1] + .0722 * +color[2];
      el.dataset.agTone = lum > 135 ? 'light' : 'dark';
    }
  }
  let textTimer;
  const observer = new MutationObserver(records => {
    if (records.some(r => r.type === 'childList' && r.target !== canvas && !r.target.parentElement?.closest('#afterglow-meter') && r.target !== caption)) {
      clearTimeout(textTimer);textTimer=setTimeout(protectText,40);
    }
  });
  function glow(x,y,r,hue,alpha,squash=1) {
    ctx.save();ctx.translate(x,y);ctx.scale(1,squash);
    const gradient=ctx.createRadialGradient(0,0,0,0,0,r);
    gradient.addColorStop(0,`hsla(${hue},95%,64%,${alpha})`);
    gradient.addColorStop(.30,`hsla(${hue},95%,49%,${alpha*.55})`);
    gradient.addColorStop(1,`hsla(${hue},95%,30%,0)`);
    ctx.fillStyle=gradient;ctx.fillRect(-r,-r,r*2,r*2);ctx.restore();
  }
  function frame(ms) {
    raf=0;
    if (!config.enabled || document.hidden) return;
    const moving = config.motion > 0 && !reduced.matches;
    const budget = config.quality ? 15 : 31;
    if (ms-last < budget) {raf=requestAnimationFrame(frame);return;}
    const dt=Math.min(.08,(ms-last)/1000 || .016);last=ms;
    if (moving) time=state.scene_time!==undefined ? (sceneAt+(ms-received)/1000)*(.18+config.motion/110) : time+dt*(.18+config.motion/110);
    const now=ms/1000;
    const energy=Number(state.energy)||0;
    const fresh = ms-received<600;
    gain = Math.max(.00005,gain+(energy-gain)*Math.min(1,dt*.7));
    const target=fresh&&energy>.00003 ? clamp(energy/(gain*1.7),0,1):0;
    level+=(target-level)*Math.min(1,dt*(target>level?30:9));
    attack*=Math.exp(-dt*8);
    let beat=0;
    if (fresh && state.period && state.confidence>.64 && now-nextBeat<1) {
      const p=state.period;
      const d=((now-nextBeat+p/2)%p+p)%p-p/2;
      beat=Math.exp(-((d/.065)**2));
    }
    const desired=moving ? Math.max(beat,attack,level*.22)*config.impact/80 : 0;
    pulse+=(desired-pulse)*Math.min(1,dt*(desired>pulse?35:10));
    if (!moving && !dirty) return;
    dirty=false;
    const w=surface?.width||innerWidth,h=surface?.height||innerHeight,t=time,intensity=config.intensity/100;
    ctx.setTransform(width/innerWidth,0,0,height/innerHeight,-(surface?.x||0)*width/innerWidth,-(surface?.y||0)*height/innerHeight);
    const hues=palettes[config.palette]||palettes.aurora;
    ctx.globalCompositeOperation='source-over';ctx.fillStyle='#050812';ctx.fillRect(0,0,w,h);
    ctx.globalCompositeOperation='screen';
    // Large soft fields move around the perimeter, leaving air around the words.
    glow(w*(.08+.1*Math.sin(t*.27)),h*(.28+.15*Math.cos(t*.21)),w*(.60+pulse*.18),hues[0],intensity*(.48+pulse*.95),.72);
    glow(w*(.92+.08*Math.sin(t*.22)),h*(.35+.20*Math.sin(t*.16)),w*(.56+pulse*.15),hues[1],intensity*(.55+pulse*.95),.82);
    glow(w*(.5+.30*Math.cos(t*.13)),h*1.07,w*.62,hues[2],intensity*(.4+pulse*.65),.38);
    // Slowly sweeping light fans, with diffuse edges and a quiet center.
    for(let side=0;side<2;side++)for(let j=0;j<4;j++) {
      const x=side?w*.98:w*.02;
      const end=w*(.16+j*.2+(.12+pulse*.05)*Math.sin(t*.18+j+side));
      const beam=ctx.createLinearGradient(x,0,end,h);
      beam.addColorStop(0,`hsla(${hues[side]},95%,75%,${clamp(intensity*(.08+pulse*.40),0,1)})`);
      beam.addColorStop(1,`hsla(${hues[side]},95%,60%,0)`);
      ctx.fillStyle=beam;ctx.beginPath();ctx.moveTo(x-2,0);ctx.lineTo(end-w*.05,h);ctx.lineTo(end+w*.05,h);ctx.lineTo(x+2,0);ctx.fill();
    }
    // Expanding edge arcs provide an unmistakable musical accent without whitening the card.
    if(pulse>.03)for(let side=0;side<2;side++) {
      ctx.beginPath();ctx.ellipse(side?w:0,h*.5,w*(.25+pulse*.25),h*(.35+pulse*.20),0,0,Math.PI*2);
      ctx.lineWidth=1+pulse*3;ctx.strokeStyle=`hsla(${hues[side]},95%,70%,${clamp(pulse*intensity*.6,0,1)})`;ctx.stroke();
    }
    // Long, flowing filament ribbons, rather than hard strobe flashes.
    for(let j=0;j<9;j++) {
      const hue=hues[j%3]+12*Math.sin(t*.12+j);
      ctx.beginPath();
      for(let i=0;i<=48;i++) {
        const x=w*i/48, u=i/48;
        const edge=j<5 ? .08 : .88;
        const y=h*(edge+.065*Math.sin(u*5+t*.23+j*.85)+.055*Math.cos(u*9-t*.16+j));
        if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);
      }
      ctx.strokeStyle=`hsla(${hue},95%,68%,${intensity*(.09+pulse*.04)})`;
      ctx.lineWidth=(j%3===0?2: .8)*(w/1000);ctx.stroke();
    }
    // A distant dance-floor grid gives the light show depth.
    const horizon=h*.73;
    ctx.lineWidth=.7;ctx.strokeStyle=`hsla(${hues[0]},80%,65%,${intensity*.15})`;
    for(let i=-10;i<=10;i++) {
      ctx.beginPath();ctx.moveTo(w*.5+i*w*.018,horizon);ctx.lineTo(w*.5+i*w*.18,h);ctx.stroke();
    }
    for(let i=0;i<12;i++) {
      const z=((i+t*.16)%12)/12;
      const y=horizon+(h-horizon)*z*z;
      ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();
    }
    // Sparse drifting pinpoints stay bounded even in long review sessions.
    for(let i=0;i<52;i++) {
      const x=((Math.sin(i*173.13)*.5+.5)*w+Math.sin(t*.12+i)*12+w)%w;
      const y=((i*.61803398875+t*.002)%1)*h;
      ctx.fillStyle=`hsla(${hues[i%3]},75%,85%,${intensity*(.12+.12*Math.sin(i+t*.3)**2)})`;
      ctx.fillRect(x,y,i%8===0?1.5: .8,i%8===0?1.5:.8);
    }
    ctx.globalCompositeOperation='source-over';
    const shade=ctx.createRadialGradient(w*.5,h*.42,0,w*.5,h*.45,Math.max(w,h)*.7);
    shade.addColorStop(0,'rgba(3,6,16,.55)');shade.addColorStop(.46,'rgba(3,6,16,.20)');shade.addColorStop(1,'rgba(0,2,10,.42)');
    ctx.fillStyle=shade;ctx.fillRect(0,0,w,h);
    if(moving)raf=requestAnimationFrame(frame);
  }
  function wake() { if(config.enabled&&!document.hidden&&!raf)raf=requestAnimationFrame(frame); }
  function update(data) {
    const oldSurface=JSON.stringify(surface);
    surface=data.surface||null;
    state=data;received=performance.now();sceneAt=Number(data.scene_time)||0;
    const bass=Number(data.bass)||0;
    if(data.hit_id && data.hit_id!==lastHit){attack=1;lastHit=data.hit_id;}
    attack=Math.max(attack,clamp((bass-previousBass)/Math.max(gain,.0001)*3,0,1));previousBass=bass;
    if(oldSurface!==JSON.stringify(surface)){resize();dirty=true;}
    const key=JSON.stringify(data.config);
    if(key!==configKey) {
      configKey=key;config={...config,...data.config};mount();resize();dirty=true;
      root.classList.toggle('ag-on',!!config.enabled);
      root.classList.toggle('ag-clear',!!config.clear_backgrounds);
      root.classList.toggle('ag-immersive',!!config.immersive);
      root.classList.toggle('ag-chrome',data.primary===false);
      root.style.setProperty('--ag-outline',(.25+config.contrast*.006).toFixed(2));
      root.style.setProperty('--ag-radius',(1+config.contrast*.045)+'px');
      canvas.hidden=!config.enabled;protectText(true);
    }
    if(hud){
      hud.hidden=!config.enabled||!config.show_meter||data.primary===false;
      meter.style.transform=`scaleX(${clamp(Math.sqrt(Number(data.energy)||0)*4,0,1)})`;
      if(received-meterTick>250){
        meterTick=received;
        const hearing=(Number(data.energy)||0)>.00003;
        caption.textContent=hearing?`${data.device||'System audio'} · ${reduced.matches?'Reduced motion':!config.motion?'Motion paused':data.bpm?Math.round(data.bpm)+' BPM':'Hearing music'}`:(data.status&&data.status!=='Listening to system audio'?data.status:'Afterglow · Waiting for sound');
      }
    }
    if(data.period)nextBeat=performance.now()/1000+data.next_in;
    wake();
  }
  window.Afterglow={update};
  addEventListener('resize',()=>{resize();wake();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(raf);raf=0;}else{dirty=true;wake();}});
  reduced.addEventListener('change',()=>{dirty=true;wake();});
  function ready(){mount();resize();observer.observe(document.body,{childList:true,subtree:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
})();

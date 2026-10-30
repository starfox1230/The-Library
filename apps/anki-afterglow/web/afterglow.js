(() => {
  'use strict';
  if (window.Afterglow) return;
  const canvas = document.createElement('canvas');
  canvas.id = 'afterglow-canvas';
  canvas.setAttribute('aria-hidden', 'true');
  const ctx = canvas.getContext('2d', {alpha:false});
  const root = document.documentElement;
  let config = {enabled:false, intensity:65, motion:55, contrast:70, quality:1, palette:'aurora', clear_backgrounds:true};
  let state = {}, raf = 0, last = 0, time = 0, pulse = 0, level = 0, gain = .03, nextBeat = 0;
  let width = 1, height = 1, dirty = true, configKey = '';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const palettes = {aurora:[185,267,324], acid:[155,80,38], ultraviolet:[260,218,313]};
  const clamp = (v, a, b) => Math.max(a,Math.min(b,v));
  function mount() { if (document.body && !canvas.isConnected) document.body.prepend(canvas); }
  function resize() {
    const scale = Math.min(1.25, devicePixelRatio || 1, 1440 / innerWidth, 1000 / innerHeight);
    const w = Math.max(1,Math.round(innerWidth * scale)), h = Math.max(1,Math.round(innerHeight * scale));
    if (canvas.width !== w || canvas.height !== h) {canvas.width=w;canvas.height=h;width=w;height=h;dirty=true;}
  }
  function protectText() {
    const qa = document.getElementById('qa');
    if (!qa || !config.enabled) return;
    for (const el of [qa,...qa.querySelectorAll('*')]) {
      if (!Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim())) continue;
      const color = getComputedStyle(el).color.match(/[\d.]+/g);
      if (!color || color.length < 3) continue;
      const lum = .2126 * +color[0] + .7152 * +color[1] + .0722 * +color[2];
      el.dataset.agTone = lum > 135 ? 'light' : 'dark';
    }
  }
  let textTimer;
  const observer = new MutationObserver(records => {
    if (records.some(r => r.type === 'childList' && r.target !== canvas)) {
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
    if (moving) time+=dt*(.18+config.motion/110);
    const now=ms/1000;
    const energy=Number(state.energy)||0;
    gain = Math.max(.009,gain+(energy-gain)*Math.min(1,dt*.7));
    const target=clamp(energy/(gain*2.8),0,1);
    level+=(target-level)*Math.min(1,dt*9);
    let beat=0;
    if (state.period && state.confidence>.64 && now-nextBeat<1) {
      const p=state.period;
      const d=((now-nextBeat+p/2)%p+p)%p-p/2;
      beat=Math.exp(-((d/.065)**2));
    }
    const desired=moving ? Math.max(beat*.85,level*.3) : 0;
    pulse+=(desired-pulse)*Math.min(1,dt*(desired>pulse?22:7));
    if (!moving && !dirty) return;
    dirty=false;
    const w=width,h=height, t=time, intensity=config.intensity/100;
    const hues=palettes[config.palette]||palettes.aurora;
    ctx.globalCompositeOperation='source-over';ctx.fillStyle='#050812';ctx.fillRect(0,0,w,h);
    ctx.globalCompositeOperation='screen';
    // Large soft fields move around the perimeter, leaving air around the words.
    glow(w*(.08+.1*Math.sin(t*.27)),h*(.28+.15*Math.cos(t*.21)),w*.65,hues[0],intensity*(.65+pulse*.25),.72);
    glow(w*(.92+.08*Math.sin(t*.22)),h*(.35+.20*Math.sin(t*.16)),w*.59,hues[1],intensity*(.75+pulse*.25),.82);
    glow(w*(.5+.30*Math.cos(t*.13)),h*1.07,w*.62,hues[2],intensity*.6,.38);
    // Slowly sweeping light fans, with diffuse edges and a quiet center.
    for(let side=0;side<2;side++)for(let j=0;j<4;j++) {
      const x=side?w*.98:w*.02;
      const end=w*(.16+j*.2+.12*Math.sin(t*.18+j+side));
      const beam=ctx.createLinearGradient(x,0,end,h);
      beam.addColorStop(0,`hsla(${hues[side]},95%,75%,${intensity*(.13+pulse*.06)})`);
      beam.addColorStop(1,`hsla(${hues[side]},95%,60%,0)`);
      ctx.fillStyle=beam;ctx.beginPath();ctx.moveTo(x-2,0);ctx.lineTo(end-w*.05,h);ctx.lineTo(end+w*.05,h);ctx.lineTo(x+2,0);ctx.fill();
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
    state=data;
    const key=JSON.stringify(data.config);
    if(key!==configKey) {
      configKey=key;config={...config,...data.config};mount();resize();dirty=true;
      root.classList.toggle('ag-on',!!config.enabled);
      root.classList.toggle('ag-clear',!!config.clear_backgrounds);
      root.style.setProperty('--ag-outline',(.25+config.contrast*.006).toFixed(2));
      root.style.setProperty('--ag-radius',(1+config.contrast*.045)+'px');
      canvas.hidden=!config.enabled;protectText();
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

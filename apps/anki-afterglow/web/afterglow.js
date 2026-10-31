(() => {
  'use strict';
  if (window.Afterglow) return;
  let canvas = document.createElement('canvas');
  canvas.id = 'afterglow-canvas';
  canvas.hidden=true;
  canvas.setAttribute('aria-hidden', 'true');
  let currentVisual='particles';
  let visual = null, decorationOnly=false;
  const root = document.documentElement;
  let config = {enabled:false, intensity:65, motion:55, contrast:70, quality:1, palette:'aurora', clear_backgrounds:true, impact:80, immersive:true, show_meter:true,visual:'particles'};
  let state = {}, raf = 0, last = 0, time = 0, pulse = 0, level = 0, gain = .03, nextBeat = 0;
  let dirty = true, configKey = '';
  let surface=null, received=0, lastHit=0, attack=0, previousBass=0, lastAttack=-1000;
  let hud, meter, caption, meterTick=0;
  let camera=0,clocks=Array(8).fill(0),clockMotion=55,clubTime=0,clubBeat=0,waveBands=Array(8).fill(0);
  const timings=[];let drawCost=0,drawCount=0,lastScene=null;
  // Synchronous readback is only for QA; normal frames use disposable GPU buffers.
  function paint(){if(visual&&lastScene&&!decorationOnly)visual.draw(lastScene);}
  function metrics(){const samples=timings.slice(1).map((t,i)=>t-timings[i]).sort((a,b)=>a-b);return {frames:drawCount,particles:visual?.particles||0,renderer:decorationOnly?'decorator':visual?.kind||'idle',device:visual?.info||visual?.kind||'none',fps:decorationOnly?state.scene_fps||0:timings.length>1?(timings.length-1)*1000/(timings.at(-1)-timings[0]):0,p95_ms:samples[Math.floor(samples.length*.95)]||0,draw_ms:drawCount?drawCost/drawCount:0,visual:currentVisual};}
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
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
    // Qt supplies device-independent WINDOW pixels. Browser CSS pixels and DPR
    // change with card zoom; neither may resize or shift the background scene.
    const vw=surface?.view_width||innerWidth,vh=surface?.view_height||innerHeight;
    const scale = Math.min(1.25, surface?.dpr||devicePixelRatio||1, (config.quality?1024:720) / (surface?.width||vw), (config.quality?720:480) / (surface?.height||vh));
    const w = Math.max(1,Math.round(vw * scale)), h = Math.max(1,Math.round(vh * scale));
    if (canvas.width !== w || canvas.height !== h) {canvas.width=w;canvas.height=h;dirty=true;}
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
  function frame(ms) {
    const started=performance.now();
    raf=0;
    if (!config.enabled || document.hidden || decorationOnly || !visual) return;
    const moving = config.motion > 0 && !reduced.matches;
    // Smooth mode follows the display clock. A 15 ms gate drops valid frames
    // when Qt delivers uneven timestamps even on a 60 Hz display.
    const budget = config.quality ? 0 : 31;
    if (ms-last < budget) {raf=requestAnimationFrame(frame);return;}
    const dt=Math.min(.08,(ms-last)/1000 || .016);last=ms;
    const now=ms/1000;
    const energy=Number(state.energy)||0;
    const fresh = ms-received<600;
    gain = Math.max(.00005,gain+(energy-gain)*Math.min(1,dt*.7));
    const target=fresh&&energy>.00003 ? clamp(energy/(gain*1.7),0,1):0;
    level+=(target-level)*Math.min(1,dt*(target>level?30:9));
    if(level<.001)level=0;
    attack*=Math.exp(-dt*12);
    let beat=0;
    if (fresh && state.period && state.confidence>.64 && now-nextBeat<1) {
      const p=state.period;
      const d=((now-nextBeat+p/2)%p+p)%p-p/2;
      beat=Math.exp(-((d/.035)**2));
    }
    const desired=moving ? Math.max(beat,attack,fresh?(Number(state.music_push)||0):0)*config.impact/100 : 0;
    pulse+=(desired-pulse)*(1-Math.exp(-dt*(desired>pulse?60:14)));
    if(pulse<.001)pulse=0;
    for(let i=0;i<8;i++){
      const raw=state.bands?.[i]??energy;
      const target=moving&&fresh?clamp(raw/Math.max(.00005,gain*.65),0,1):0;
      waveBands[i]+=(target-waveBands[i])*(1-Math.exp(-dt*(target>waveBands[i]?35:10)));
      if(waveBands[i]<.001)waveBands[i]=0;
    }
    if (!moving && !dirty) return;
    dirty=false;
    const musicLevel=fresh?Number(state.music_level ?? level):level;
    const musicBass=fresh?Number(state.music_bass ?? Math.min(1,(Number(state.bass)||0)/Math.max(gain,.0001))):0;
    if(moving){
      if(state.flow_time!==undefined){const age=(ms-received)/1000;time=(Number(state.flow_time)+Math.min(.6,age)*Number(state.flow_rate??.1)+Math.max(0,age-.6)*.1)*config.motion/55;}
      else time+=dt*(.10+musicLevel*.48+musicBass*.22+pulse*.16)*config.motion/55;
      const age=Math.min(.6,(ms-received)/1000);
      const resync=config.motion!==clockMotion;clockMotion=config.motion;
      // A falling rate can make a new extrapolation land behind the last frame.
      // Hold briefly instead of moving particles/camera backward between updates.
      clocks=state.particle_phases?state.particle_phases.map((p,i)=>{const target=(p+age*(state.particle_rates?.[i]??.1))*config.motion/55;return resync?target:Math.max(clocks[i],target);}):clocks.map((p,i)=>p+dt*(.1+musicLevel*.65+pulse*(i<3?1.8:.85))*config.motion/55);
      if(state.camera_phase!==undefined){const target=(state.camera_phase+age*(state.camera_rate||0))*config.motion/55;camera=resync?target:Math.max(camera,target);}
      else camera+=dt*(.025+pulse*.30)*config.motion/55;
      const clubTarget=Math.min(1,pulse*1.4);
      clubBeat+=(clubTarget-clubBeat)*(1-Math.exp(-dt*(clubTarget>clubBeat?35:9)));
      if(state.club_time!==undefined){const target=(state.club_time+age*(state.club_rate||0))*config.motion/55;clubTime=resync?target:Math.max(clubTime,target);}
      else clubTime+=dt*(.12+musicLevel*.5+clubBeat*3.8)*config.motion/55;
    }
    lastScene={w:surface?.width||innerWidth,h:surface?.height||innerHeight,
      vw:surface?.view_width||innerWidth,vh:surface?.view_height||innerHeight,
      x:surface?.x||0,y:surface?.y||0,time,intensity:config.intensity/100,
      palette:config.palette,level:moving?musicLevel:0,bass:moving?musicBass*config.impact/100:0,
      pulse:moving?pulse:0,clubBeat:moving?clubBeat:0,clubTime,waveBands:moving?waveBands.slice():Array(8).fill(0),waveImpact:config.impact/100,quality:config.quality,particleCount:config.particle_count??4200,clocks,camera};
    visual.draw(lastScene);
    timings.push(ms);if(timings.length>120)timings.shift();drawCost+=performance.now()-started;drawCount++;
    if(moving)raf=requestAnimationFrame(frame);
  }
  function wake() { if(config.enabled&&!decorationOnly&&!document.hidden&&!raf)raf=requestAnimationFrame(frame); }
  function update(data) {
    const oldSurface=JSON.stringify(surface);
    surface=data.surface||null;
    state=data;received=performance.now();
    const bass=Number(data.bass)||0;
    if(data.hit_id && data.hit_id!==lastHit){attack=1;lastHit=data.hit_id;lastAttack=received;}
    const flux=(bass-previousBass)/Math.max(gain,.0001);
    if(flux>.15&&received-lastAttack>160){attack=Math.max(attack,clamp(flux*2,0,1));lastAttack=received;}
    previousBass=bass;
    if(oldSurface!==JSON.stringify(surface)){resize();dirty=true;}
    const modeChanged=decorationOnly!==!!data.decoration_only;
    decorationOnly=!!data.decoration_only;
    const key=JSON.stringify(data.config)+decorationOnly;
    if(key!==configKey) {
      configKey=key;config={...config,...data.config};mount();resize();dirty=true;
      if(modeChanged || config.visual!==currentVisual || (!visual&&!decorationOnly)){
        visual?.dispose?.();visual=null;
        cancelAnimationFrame(raf);raf=0;
        const next=canvas.cloneNode();canvas.replaceWith(next);canvas=next;
        currentVisual=['liquid','club','waves'].includes(config.visual)?config.visual:'particles';
        if(!decorationOnly){visual=({liquid:window.AfterglowLiquid,club:window.AfterglowClub,waves:window.AfterglowWaves,particles:window.AfterglowParticles}[currentVisual])(canvas);canvas=visual.canvas;}
        mount();resize();
        timings.length=0;drawCost=drawCount=0;
      }
      root.classList.toggle('ag-on',!!config.enabled);
      root.classList.toggle('ag-shared',decorationOnly);
      root.classList.toggle('ag-clear',!!config.clear_backgrounds);
      root.classList.toggle('ag-immersive',!!config.immersive);
      root.classList.toggle('ag-chrome',data.primary===false);
      root.style.setProperty('--ag-outline',(.25+config.contrast*.006).toFixed(2));
      root.style.setProperty('--ag-radius',(1+config.contrast*.045)+'px');
      canvas.hidden=!config.enabled||decorationOnly;protectText(true);
    }
    if(hud){
      hud.hidden=!config.enabled||!config.show_meter||data.primary===false;
      meter.style.transform=`scaleX(${clamp(Math.sqrt(Number(data.energy)||0)*4,0,1)})`;
      if(received-meterTick>250){
        meterTick=received;
        const hearing=(Number(data.energy)||0)>.00003;
        const fps=config.motion&&!reduced.matches?` · ${Math.round(metrics().fps)} FPS`:'';
        caption.textContent=(hearing?`${data.device||'System audio'} · ${reduced.matches?'Reduced motion':!config.motion?'Motion paused':data.bpm?Math.round(data.bpm)+' BPM':'Hearing music'}`:(data.status&&data.status!=='Listening to system audio'?data.status:'Afterglow · Waiting for sound'))+fps;
      }
    }
    if(data.period)nextBeat=performance.now()/1000+data.next_in;
    wake();
  }
  window.Afterglow={update,metrics,paint,get renderer(){return decorationOnly?'decorator':visual?.kind||'idle';}};
  addEventListener('resize',()=>{resize();wake();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(raf);raf=0;}else{dirty=true;wake();}});
  reduced.addEventListener('change',()=>{dirty=true;wake();});
  function ready(){mount();resize();observer.observe(document.body,{childList:true,subtree:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
})();

/* Clock-derived appearance only: never changes targets, pauses, or earnings. */
(function(root,factory) {
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;else root.AfterglowTheme=api;
})(typeof globalThis!=='undefined'?globalThis:this,function() {
  'use strict';
  const clamp=x=>Math.max(0,Math.min(1,x));
  const rgb=hex=>hex.slice(1).match(/../g).map(n=>parseInt(n,16));
  const hex=channels=>'#'+channels.map(n=>Math.round(Math.max(0,Math.min(255,n))).toString(16).padStart(2,'0')).join('');
  // Oklab interpolation avoids a muddy midpoint between the night and ruby palettes.
  // Conversion model: https://www.w3.org/TR/css-color-4/#color-conversion-code
  function lab(color) {
    const [r,g,b]=rgb(color).map(n=>{const c=n/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4;});
    const l=Math.cbrt(.4122214708*r+.5363325363*g+.0514459929*b);
    const m=Math.cbrt(.2119034982*r+.6806995451*g+.1073969566*b);
    const s=Math.cbrt(.0883024619*r+.2817188376*g+.6299787005*b);
    return [.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s];
  }
  function fromLab([L,a,b]) {
    const l=(L+.3963377774*a+.2158037573*b)**3;
    const m=(L-.1055613458*a-.0638541728*b)**3;
    const s=(L-.0894841775*a-1.291485548*b)**3;
    return hex([4.0767416621*l-3.3077115913*m+.2309699292*s,-1.2684380046*l+2.6097574011*m-.3413193965*s,-.0041960863*l-.7034186147*m+1.707614701*s].map(c=>255*(c<=.0031308?12.92*c:1.055*Math.max(0,c)**(1/2.4)-.055)));
  }
  function mix(a,b,t) {
    if(t<=0)return a;if(t>=1)return b;
    const x=lab(a),y=lab(b);
    return fromLab(x.map((v,i)=>v+(y[i]-v)*t));
  }
  const keys=['bg','text','muted','accent','buttonA','buttonB','ink'];
  const stops=[
    [0,   ['#080b15','#edf3ff','#8c9ab5','#78f4ed','#9df8e6','#72deed','#10232a']],
    [.35, ['#29162f','#fff0fa','#c7adca','#e8bbf2','#eac5f4','#c6c6ff','#2a1838']],
    [.65, ['#64192f','#fff2f2','#f1c5d0','#ffc9c2','#ffddd2','#ffb4bd','#41172c']],
    [.85, ['#981c36','#fff4ec','#ffdfd7','#ffdac1','#ffe6ca','#ffc1b3','#461a28']],
    [1,   ['#b51c31','#fff5ed','#ffe5dc','#ffe4c7','#ffebd6','#ffcaba','#461a23']]
  ];
  const named=values=>Object.fromEntries(keys.map((key,i)=>[key,values[i]]));
  const paused=named(['#f4c75f','#3b2c12','#66491f','#684719','#fff1c0','#f3d086','#3b2c12']);
  const overtime=named(['#30205e','#f5efff','#d6c9f2','#c8b7ff','#e7d5ff','#b7daff','#25163f']);
  function countdown(progress) {
    const t=clamp(progress);
    const i=Math.max(1,stops.findIndex(stop=>stop[0]>=t));
    const [start,a]=stops[i-1],[end,b]=stops[i];
    const fraction=(t-start)/(end-start), eased=fraction*fraction*(3-2*fraction);
    return named(a.map((value,k)=>mix(value,b[k],eased)));
  }
  function variables(p,phase) {
    const rgba=(color,opacity)=>`rgba(${rgb(color).join(',')},${opacity})`;
    const gold=phase==='paused';
    const panelA=mix(p.bg,gold?'#fff4d0':'#080b15',.14);
    const panelB=mix(p.bg,gold?'#d5a03b':'#080b15',.27);
    return {
      '--timer-bg':p.bg,'--timer-text':p.text,'--timer-muted':p.muted,'--timer-accent':p.accent,
      '--timer-secondary':mix(p.muted,p.text,.3),'--timer-button-a':p.buttonA,'--timer-button-b':p.buttonB,'--timer-ink':p.ink,
      '--timer-panel-a':panelA,'--timer-panel-b':panelB,'--timer-edge':rgba(p.accent,.23),
      '--timer-track':mix(p.bg,p.accent,.18),'--timer-ticks':mix(p.bg,p.accent,.45),
      '--timer-glow':rgba(p.accent,.23),'--timer-soft-glow':rgba(p.accent,.09),
      '--timer-halo-a':rgba(p.accent,.055),'--timer-halo-b':rgba(p.buttonA,.035),
      '--timer-arc-a':mix(p.accent,gold?'#805326':'#a58dff',gold?.15:.25),
      '--timer-arc-b':p.accent,'--timer-arc-c':mix(p.accent,p.text,.35),
      '--timer-hold-a':mix(p.buttonA,p.text,.35),'--timer-hold-b':mix(p.buttonB,p.text,.35)
    };
  }
  function resolve({active=false,targetMs=1080000,elapsedMs=0,paused:pause=false,holding=false,motion=true}={}) {
    const target=Number.isFinite(targetMs)&&targetMs>0?targetMs:1080000;
    const spent=Number.isFinite(elapsedMs)?Math.max(0,elapsedMs):0;
    const over=active&&spent>target, remaining=target-spent;
    const phase=!active?'idle':pause?'paused':over?'overtime':'running';
    const warning=active&&!pause&&!over&&remaining<=120000;
    const pulse=warning&&!holding&&motion?(remaining<=30000?'fast':'slow'):'off';
    const progress=active?clamp(spent/target):0;
    const palette=phase==='paused'?paused:phase==='overtime'?overtime:countdown(progress);
    return {phase,progress,warning,pulse,over,palette,vars:variables(palette,phase)};
  }
  function createRenderer({root,body,themeColor}) {
    const previous={};
    return {update(input) {
      const look=resolve(input);
      body.dataset.theme=look.phase;body.dataset.pulse=look.pulse;
      for(const [key,value] of Object.entries(look.vars)) {
        if(previous[key]!==value){root.style.setProperty(key,value);previous[key]=value;}
      }
      if(themeColor&&themeColor.getAttribute('content')!==look.palette.bg)themeColor.setAttribute('content',look.palette.bg);
      return look;
    }};
  }
  return {resolve,createRenderer,mix,rgb};
});

(() => {
  'use strict';
  if (window.top !== window) return;
  const records = new Map();
  let prefs={rememberAudio:true,audioMuted:false,audioVolume:1},ready=false;
  function isVimeo(element) {try {const u=new URL(element.src);return u.hostname==='player.vimeo.com'&&u.protocol==='https:'&&/^\/video\/\d+\/?$/.test(u.pathname);}catch{return false;}}
  function bounded(promise) {let timer;return Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Player timeout')),3000);})]).finally(()=>clearTimeout(timer));}
  async function restore(record,force=false) {
    if(!ready || (!prefs.rememberAudio&&!force) || record.busy || !record.element.isConnected)return;
    record.busy=true;
    try {
      const muted=force?false:prefs.audioMuted;
      if(record.player) {
        const actual=await bounded(record.player.getMuted());
        if(actual!==muted)await bounded(record.player.setMuted(muted));
        if(!muted && prefs.audioVolume>0 && await bounded(record.player.getVolume())===0)await bounded(record.player.setVolume(prefs.audioVolume));
      } else {
        record.element.muted=muted;
        if(!muted && record.element.volume===0)record.element.volume=prefs.audioVolume || 1;
      }
      record.error='';
    } catch {record.error='Sound could not be restored automatically. Click Restore sound.';globalThis.MedalityAudioNotice?.(record.error);}
    finally {record.busy=false;}
  }
  function scan() {
    if(!location.pathname.includes('/unit/'))return;
    for(const [element,r]of records)if(!element.isConnected){if(r.player){r.player.off('loaded',r.loaded);r.player.off('play',r.loaded);}element.removeEventListener('load',r.loaded);records.delete(element);}
    for(const element of [...document.querySelectorAll('iframe')].filter(isVimeo).concat([...document.querySelectorAll('video')])) {
      if(records.has(element)){const r=records.get(element);if(r.src!==element.getAttribute('src')){r.src=element.getAttribute('src');r.remaining=3;}continue;}
      const r={element,src:element.getAttribute('src'),busy:false,remaining:3};records.set(element,r);
      r.loaded=()=>{r.remaining=3;void restore(r);};
      if(element.tagName==='IFRAME'){try{r.player=new Vimeo.Player(element);r.player.on('loaded',r.loaded);r.player.on('play',r.loaded);element.addEventListener('load',r.loaded);}catch{records.delete(element);continue;}}
      else {element.addEventListener('loadedmetadata',r.loaded);element.addEventListener('play',r.loaded);}
      void restore(r);
    }
  }
  async function remember(muted) {
    if(!ready)return;
    prefs.audioMuted=muted;
    try{await chrome.storage.local.set({audioMuted:muted});}catch{}
  }
  // Medality renders its audio controls outside the Vimeo iframe. Record only
  // deliberate controls, never the browser/site's automatic mute-on-autoplay.
  document.addEventListener('click',event=>{
    if(!event.isTrusted)return;
    const button=event.target.closest?.('button');if(!button)return;
    const name=button.getAttribute('aria-label')||button.getAttribute('title')||button.textContent.trim();
    if(/^unmute\b/i.test(name))void remember(false);
    else if(/^mute\b/i.test(name))void remember(true);
  },true);
  document.addEventListener('keydown',event=>{
    if(event.isTrusted&&event.key.toLowerCase()==='m'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!event.target.closest?.('input,textarea,[contenteditable="true"]'))void remember(!prefs.audioMuted);
  },true);
  chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local')for(const key of Object.keys(prefs))if(changes[key])prefs[key]=changes[key].newValue;});
  chrome.runtime.onMessage.addListener((message,_sender,reply)=>{
    if(message?.type!=='medality-restore-audio')return;
    remember(false).then(()=>Promise.all([...records.values()].map(r=>restore(r,true)))).then(()=>reply({ok:[...records.values()].length>0&&[...records.values()].every(r=>!r.error)}));return true;
  });
  globalThis.MedalityRestoreAudio=async()=>{
    await remember(false);await Promise.all([...records.values()].map(r=>restore(r,true)));
    return records.size>0&&[...records.values()].every(r=>!r.error);
  };
  new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
  chrome.storage.local.get(prefs).then(value=>{prefs={...prefs,...value};ready=true;scan();}).catch(()=>{ready=true;scan();});
  setInterval(()=>{scan();for(const r of records.values())if(r.remaining>0){r.remaining--;void restore(r);}},1000);
})();

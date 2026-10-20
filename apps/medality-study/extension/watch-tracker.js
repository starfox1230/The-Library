(() => {
  'use strict';
  if (window.top !== window) return;
  const players = new Map(), attempted = new Set(), lessonVideos = new Map(), videoLessons = new Map();
  let enabled = true, initialized = false, pending = false, nativeSequence = 0;
  function lesson() { try { return MedalityTranscript.canonical(location.href); } catch { return null; } }
  function status(text) { globalThis.MedalityTrackingNotice?.(text); }
  function identity(element) {
    try {
      const url = new URL(element.getAttribute('src'));
      return url.protocol === 'https:' && url.hostname === 'player.vimeo.com' && /^\/video\/\d+\/?$/.test(url.pathname) ? url.pathname.split('/')[2] : null;
    } catch { return null; }
  }
  function bounded(promise) {
    let timer;
    return Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Player not responding')),3000);})]).finally(()=>clearTimeout(timer));
  }
  async function sample(record, event) {
    if (!initialized || !enabled || record.busy || !record.element.isConnected) return;
    const url = lesson(); if (!url) return;
    record.busy = true;
    try {
      const expected = record.vimeo ? identity(record.element) : record.element.currentSrc || record.element.getAttribute('src') || record.nativeId;
      const actual = record.vimeo ? String(await bounded(record.player.getVideoId())) : expected;
      if (!actual || actual !== expected || lesson() !== url || !record.element.isConnected) return;
      // Reject the old video under the new URL, and the new video under the old URL.
      if ((lessonVideos.has(url) && lessonVideos.get(url) !== actual) || (videoLessons.has(actual) && videoLessons.get(actual) !== url)) return;
      lessonVideos.set(url,actual); videoLessons.set(actual,url);
      const values = record.vimeo ? {seconds:await bounded(record.player.getCurrentTime()),duration:await bounded(record.player.getDuration())} : {seconds:record.element.currentTime,duration:record.element.duration};
      if (lesson() !== url || (record.vimeo && identity(record.element) !== actual)) return;
      const duration = Number(values.duration), seconds = Number(values.seconds);
      if (!(duration > 0) || !Number.isFinite(duration) || !Number.isFinite(seconds)) return;
      if (!attempted.has(url)) status(`Tracking this lesson: ${Math.min(100,Math.floor(100*seconds/duration))}% · saves at 90%`);
      if (seconds/duration < .9 || attempted.has(url)) return;
      attempted.add(url);
      await MedalityAutoCapture(url,Math.min(1,seconds/duration));
    } catch { status('Waiting for the current player to respond…'); }
    finally { record.busy = false; }
  }
  function subscribe(record) {
    record.player.off('timeupdate',record.progress);record.player.off('loaded',record.loaded);
    record.player.on('timeupdate',record.progress);record.player.on('loaded',record.loaded);
  }
  function scan() {
    pending = false;
    for (const [element,record] of players) {
      if (!element.isConnected || (record.vimeo && !identity(element))) {
        if(record.vimeo) {record.player.off('timeupdate',record.progress);record.player.off('loaded',record.loaded);element.removeEventListener('load',record.loaded);}
        else {element.removeEventListener('timeupdate',record.progress);element.removeEventListener('loadedmetadata',record.loaded);}
        players.delete(element);
      }
    }
    if (!lesson()) return;
    for (const element of [...document.querySelectorAll('iframe')].filter(identity).concat([...document.querySelectorAll('video')])) {
      if(players.has(element)) continue;
      const record={element,vimeo:element.tagName==='IFRAME',busy:false,nativeId:`native-${++nativeSequence}`};players.set(element,record);
      record.progress=data=>void sample(record,data);
      record.loaded=()=>{if(record.vimeo)subscribe(record);void sample(record);};
      if(record.vimeo) {
        try {record.player=new Vimeo.Player(element);subscribe(record);element.addEventListener('load',record.loaded);}
        catch {players.delete(element);continue;}
      } else {element.addEventListener('timeupdate',record.progress);element.addEventListener('loadedmetadata',record.loaded);}
      void sample(record);
    }
  }
  new MutationObserver(()=>{if(!pending){pending=true;queueMicrotask(scan);}}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
  chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local' && changes.autoCapture){enabled=changes.autoCapture.newValue!==false;if(!enabled)status('Automatic transcript saving is paused.');}});
  chrome.storage.local.get({autoCapture:true}).then(value=>{enabled=value.autoCapture!==false;initialized=true;scan();}).catch(()=>{initialized=true;scan();});
  setInterval(()=>{scan();players.forEach(record=>void sample(record));},1500);
})();

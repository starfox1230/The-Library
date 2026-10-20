(() => {
  'use strict';
  // Public page code stores data only in this browser. The extension bridge
  // supplies captures on the user's desktop; phones can import a backup.
  const key = 'medality-watched-v1', listeners = [];
  let state = {}, requestId = crypto.randomUUID(), connected = false;
  try { state = JSON.parse(localStorage.getItem(key) || '{}'); if (!state || Array.isArray(state) || typeof state !== 'object') state = {}; } catch {}
  const emit = () => listeners.forEach(fn=>fn({},'local'));
  const save = next => {localStorage.setItem(key,JSON.stringify(next));state=next;emit();};
  window.MedalityStorage = {local:{
    get:async()=>({...state}),
    set:async values=>{save({...state,...values});}
  },onChanged:{addListener:fn=>listeners.push(fn)}};
  const automatic = document.getElementById('automatic'); automatic.parentElement.hidden = true;
  const intro = document.querySelector('header .small');
  intro.textContent = 'On your computer, the extension fills this page automatically. On your phone, import a library backup. Automatic saving is controlled in the extension. Your transcripts stay in this browser.';
  function request() {window.postMessage({channel:'medality-study',type:'request-history',requestId},location.origin);}
  window.addEventListener('message',event=>{
    if (event.source!==window || event.origin!==location.origin || event.data?.channel!=='medality-study' || event.data.requestId!==requestId || event.data.type!=='history') return;
    const items=event.data.items;
    if (!Array.isArray(items) || items.length>1000) return;
    const next={...state};
    for (const raw of items) {
      try {
        const item=MedalityHistory.clean(raw);
        if(item.text.trim())next[`transcript:${item.url}`]=item;
        if(item.watchedAt)next[`watch:${item.url}`]={url:item.url,title:item.title,course:item.course,watchedAt:item.watchedAt};
      } catch {}
    }
    try {save(next);connected=true;intro.textContent='Connected to your extension. New watched lectures appear automatically. Nothing is uploaded to GitHub. Export a backup to take this library to your phone.';}
    catch {document.getElementById('status').textContent='Browser storage is full. Open Recently watched from the extension and export a backup.';}
  });
  window.addEventListener('focus',request);
  window.addEventListener('storage',event=>{if(event.key===key){try{state=JSON.parse(event.newValue||'{}');emit();}catch{}}});
  request();
})();

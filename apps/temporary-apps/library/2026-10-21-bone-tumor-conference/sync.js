/* Durable per-field merging, with a browser-persisted queue for offline edits. */
(() => {
  'use strict';
  const id = row => JSON.stringify([row.key,row.field]);
  const newer = (a,b) => !b || a.updated>b.updated || (a.updated===b.updated&&JSON.stringify(a.value)>JSON.stringify(b.value));
  function create({snapshot,apply,status,storage=localStorage,fetcher=fetch,now=Date.now,automatic=true}) {
    const cacheKey='library-bone-tumor-sync-v1';
    let rows=new Map(),pending=new Set(),offset=0,lastClock=0,busy=false,timer,initial=true,seeded=false,stopped=false,owner=null;
    try {const saved=JSON.parse(storage.getItem(cacheKey)||'{}');rows=new Map((saved.records||[]).map(row=>[id(row),row]));pending=new Set(saved.pending||[]);owner=saved.owner||null;}catch{}
    function persist(){try{storage.setItem(cacheKey,JSON.stringify({owner,records:[...rows.values()],pending:[...pending]}));}catch{status('storage');}}
    function capture(schedule=true){
      for(const row of snapshot()) {
        const key=id(row),previous=rows.get(key);
        if(previous&&JSON.stringify(previous.value)===JSON.stringify(row.value))continue;
        // Preserve historical annotation times during migration; new edits use the server-adjusted clock.
        const updated=!seeded&&!previous ? (row.updated||1) : Math.max(now()+offset,lastClock+1,(previous?.updated||0)+1);
        lastClock=Math.max(lastClock,updated);rows.set(key,{key:row.key,field:row.field,value:row.value,updated});pending.add(key);
      }
      seeded=true;persist();
      if(schedule){status('pending');clearTimeout(timer);if(automatic)timer=setTimeout(sync,600);}
    }
    function merge(remote){
      if(owner&&owner!==remote.userId)throw Error('Account changed. Reload to sync.');
      owner=remote.userId;offset=remote.serverTime-now();
      for(const row of remote.records){const key=id(row),local=rows.get(key);if(newer(row,local)){rows.set(key,row);pending.delete(key);}else if(local&&local.updated===row.updated&&JSON.stringify(local.value)===JSON.stringify(row.value))pending.delete(key);}
      persist();apply([...rows.values()],{initial});initial=false;
    }
    async function request(method='GET',records){
      const body=records?JSON.stringify({records}):undefined;
      const response=await fetcher('/api/progress',{method,credentials:'same-origin',cache:'no-store',redirect:'error',keepalive:!body||new TextEncoder().encode(body).length<60000,signal:AbortSignal.timeout(15000),headers:method==='POST'?{'Content-Type':'application/json'}:{},...(body?{body}:{})});
      if(response.status===401){const error=Error('signin');error.signin=true;throw error;}
      if(!response.ok)throw Error('Sync unavailable');
      const value=await response.json();if(!Array.isArray(value.records)||!value.userId||!Number.isFinite(value.serverTime))throw Error('Invalid sync response');return value;
    }
    async function sync(){
      if(busy||stopped)return;busy=true;clearTimeout(timer);
      capture(false);status('syncing');
      try {
        merge(await request());
        // Each request stays below the API limit, including large notes.
        while(pending.size){
          const batch=[];let size=0;
          for(const key of pending){const row=rows.get(key),bytes=new TextEncoder().encode(JSON.stringify(row)).length;if(batch.length&&(batch.length>=100||size+bytes>500000))break;batch.push({...row});size+=bytes;}
          merge(await request('POST',batch));
        }
        status('synced');
      }catch(error){status(error.signin?'signin':navigator.onLine===false?'offline':'error');}
      finally{busy=false;}
    }
    function start(){capture(false);sync();if(automatic){setInterval(()=>{if(document.visibilityState==='visible')sync();},15000);addEventListener('online',sync);addEventListener('focus',sync);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')sync();else{capture(false);sync();}});}}
    return {start,capture,sync,stop(){stopped=true;clearTimeout(timer);},inspect:()=>({records:[...rows.values()],pending:[...pending]})};
  }
  const api={create,newer};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else window.StudySync=api;
})();

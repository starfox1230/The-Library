export function recordKey({caseId,caseVersion,checkpointVersion,mode}){return 'brain-ct-game:v1:'+JSON.stringify([caseId,caseVersion,checkpointVersion,mode]);}
export function readBest(storage,key){try{const raw=storage.getItem(key);if(raw===null)return null;const n=Number(raw);return Number.isFinite(n)&&n>0?n:null;}catch{return null;}}
export function saveBest(storage,key,snapshot){
 const old=readBest(storage,key);
 if(snapshot.status!=='complete'||!snapshot.eligible||snapshot.mode!=='timed'||!Number.isFinite(snapshot.elapsedMs)||snapshot.elapsedMs<=0)return old;
 const next=old===null?snapshot.elapsedMs:Math.min(old,snapshot.elapsedMs);
 try{storage.setItem(key,String(next));return next;}catch{return old;}
}

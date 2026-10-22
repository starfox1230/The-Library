// Sites dispatch supplies the visitor identity. Never accept a user ID from JSON.
const documents = new Set(['helms2','helms3','helms4','acr','rsna']);
const headers = {'Content-Type':'application/json','Cache-Control':'private, no-store','Vary':'Cookie'};
const json = (value,status=200) => new Response(JSON.stringify(value),{status,headers});
export function validRecord(record, now=Date.now()) {
  if(!record || typeof record!=='object' || typeof record.key!=='string' || record.key.length>300 || !Number.isSafeInteger(record.updated) || record.updated<0 || record.updated>now+300000)return false;
  if(record.key==='reader') {
    if(record.field==='source')return documents.has(record.value);
    if(record.field==='zoom')return ['page','width','1.25','1.5','2','3'].includes(record.value);
    if(record.field==='theme')return ['light','dark'].includes(record.value);
    if(record.field?.startsWith('position:')&&documents.has(record.field.slice(9)))return Number.isInteger(record.value)&&record.value>=0&&record.value<10000;
    return false;
  }
  if(!/^(g|f|b|p):[\w:.-]+$/.test(record.key))return false;
  return ['done','key','review'].includes(record.field) ? typeof record.value==='boolean' : record.field==='note'&&typeof record.value==='string'&&record.value.length<=100000;
}
export async function handleProgress(request, db) {
  const userId=request.headers.get('oai-authenticated-user-id');
  if(!userId)return json({error:'Sign in to sync'},401);
  if(!db)return json({error:'Sync unavailable'},503);
  if(!['GET','POST'].includes(request.method))return json({error:'Method not allowed'},405);
  if(request.method==='POST') {
    if(request.headers.get('origin')!==new URL(request.url).origin || request.headers.get('sec-fetch-site')==='cross-site')return json({error:'Origin rejected'},403);
    if(!request.headers.get('content-type')?.startsWith('application/json'))return json({error:'JSON required'},415);
    if(Number(request.headers.get('content-length'))>1000000)return json({error:'Batch too large'},413);
    let body;
    try {const text=await request.text();if(text.length>1000000)return json({error:'Batch too large'},413);body=JSON.parse(text);}catch{return json({error:'Invalid JSON'},400);}
    const now=Date.now();
    if(!Array.isArray(body.records)||body.records.length>500||body.records.some(record=>!validRecord(record,now)))return json({error:'Invalid records'},400);
    if(body.records.length)await db.batch(body.records.map(record=>db.prepare(`INSERT INTO study_progress (user_id, item_key, field, value, updated) VALUES (?, ?, ?, ?, ?)
      ON CONFLICT(user_id, item_key, field) DO UPDATE SET value=excluded.value, updated=excluded.updated
      WHERE excluded.updated>study_progress.updated OR (excluded.updated=study_progress.updated AND excluded.value>study_progress.value)`)
      .bind(userId,record.key,record.field,JSON.stringify(record.value),record.updated)));
  }
  const result=await db.prepare('SELECT item_key AS key, field, value, updated FROM study_progress WHERE user_id=?').bind(userId).all();
  return json({userId,serverTime:Date.now(),records:result.results.map(row=>({...row,value:JSON.parse(row.value)}))});
}

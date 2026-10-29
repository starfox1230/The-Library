// Synthetic local server: exercise real incremental browser reads, never Azure.
const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.join(__dirname,'qa-output');
const html=fs.readFileSync(path.join(out,'preview.html'),'utf8');
const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixtures.json'),'utf8'))[0];
const defaultPrompt=JSON.parse(html.match(/<script id="default-prompt" type="application\/json">([\s\S]*?)<\/script>/)[1]);
let scenario='held', rendered='',expectedPrompt=defaultPrompt;
let batchRequests=[],held=[],active=0,peak=0,retryPrompt='';
function jobs(n,large=false){return Array.from({length:n},(_,i)=>({...fixture,id:'g'+(i+1),source_numbers:[i+1],case_label:String(i+1),status:'queued',status_message:'Waiting to analyze',revisions:[],
 resident_report:large?'FINDINGS:\n'+('界'.repeat(70000))+'\nCase '+i:fixture.resident_report+'\nSynthetic identifier '+i,
 attending_report:large?'FINDINGS:\n'+('界'.repeat(70000))+'\nCase '+i:fixture.attending_report+'\nSynthetic identifier '+i}));}
function setScenario(n,name,large=false){
 scenario=name;expectedPrompt=defaultPrompt;batchRequests=[];held=[];active=0;peak=0;
 rendered=html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_m,a,b)=>a+JSON.stringify(jobs(n,large))+b).replace('const syntheticPreview=true;','const syntheticPreview=false;');
}
function result(id){
 const value={...fixture,id,source_numbers:[999],status:'complete',title:'<img src=x onerror="window.injected=1">',revisions:fixture.revisions.map(r=>({...r}))};
 value.revisions[0].resident_summary='Partial obstruction';
 value.revisions[0].attending_summary='Closed-loop obstruction';
 value.revisions[0].reason='Description => refined interpretation';
 value.revisions[0].resident_quote='Exact source -> wording';
 if(id==='g37'){value.status='error';value.revisions=[];value.status_message='Synthetic temporary Azure rate limit. Retry this case.';}
 return value;
}
function send(res,event){res.write(JSON.stringify(event)+'\n');}
function finish(entry,skip=[]){for(const c of [...entry.payload.cases].reverse()){if(!skip.includes(c.id))send(entry.res,{type:'case',id:c.id,result:result(c.id)});}send(entry.res,{type:'done',total:entry.payload.cases.length});entry.res.end();}
const server=http.createServer(async(req,res)=>{
 if(req.method==='GET'){res.writeHead(200,{'Content-Type':'text/html'});res.end(rendered);return;}
 const chunks=[];for await(const chunk of req)chunks.push(chunk);const text=Buffer.concat(chunks).toString('utf8');
 const payload=JSON.parse(text);
 assert.equal(req.headers['x-csrf-token'],'synthetic-preview');
 if(req.url==='/analyze'){
  retryPrompt=payload.custom_prompt;res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({...result(payload.id),status:'complete',revisions:fixture.revisions}));return;
 }
 assert.equal(req.url,'/analyze-batch');assert(payload.cases.length<=100);assert(Buffer.byteLength(text)<=4_500_000);
 assert.equal(payload.custom_prompt,expectedPrompt);
 batchRequests.push(payload);active++;peak=Math.max(peak,active);
 res.on('close',()=>active--);
 res.writeHead(200,{'Content-Type':'application/x-ndjson'});send(res,{type:'started',total:payload.cases.length});
 const entry={res,payload};if(scenario==='held'||scenario==='interrupted'||scenario==='clear')held.push(entry);else finish(entry);
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>route.request().url().startsWith(base)?route.continue():route.abort());
 setScenario(100,'held');await page.goto(base);
 await page.waitForFunction(()=>[...document.querySelectorAll('#case-list .badge')].filter(n=>n.textContent==='Analyzing…').length===100);
 await new Promise((resolve,reject)=>{const until=Date.now()+5000;function check(){if(held.length)return resolve();if(Date.now()>until)return reject(new Error('Batch never reached the local server'));setTimeout(check,10);}check();});
 assert.equal(batchRequests.length,1);assert.equal(batchRequests[0].cases.length,100);
 assert.match(await page.locator('#progress-count').innerText(),/0 of 100 report pairs · 0%/);
 assert.equal(await page.locator('#revision-totals .major').innerText(),'0 major');
 assert.equal(await page.locator('.badge').filter({hasText:'Analyzing…'}).count(),100);
 send(held[0].res,{type:'case',id:'g1',result:result('g1')});
 await page.waitForFunction(()=>document.getElementById('progress-track').getAttribute('aria-valuenow')==='1');
 assert.match(await page.locator('#progress-count').innerText(),/1 of 100 report pairs · 1%/);
 assert.equal(await page.locator('#revision-totals .major').innerText(),'2 major','totals grow with completed results');
 await page.locator('#case-0').click();
 assert.equal(await page.locator('#row-0 h4').first().textContent(),'Partial obstruction → Closed-loop obstruction');
 assert.equal(await page.locator('#row-0 .reason').first().textContent(),'Description → refined interpretation');
 assert.equal(await page.locator('#row-0 blockquote').first().textContent(),'Exact source -> wording');
 await page.locator('#evidence-0').click();
 await page.locator('#case-1').click();
 assert.equal(await page.locator('.case-number').first().innerText(),'CASE\n1');
 assert.equal(await page.locator('.case-title img').count(),0);assert.equal(await page.evaluate(()=>window.injected),undefined);
 await page.locator('#combined-view').check();assert.equal(batchRequests.length,1);
 // Editing in-flight does not change the submitted prompt; retry uses the edit.
 await page.locator('#input-disclosure > summary').click();await page.locator('.customize > summary').click();
 await page.locator('#custom-prompt').fill('Current edited replacement instructions.');
 finish(held[0],['g1']);
 await page.waitForFunction(()=>document.getElementById('progress-track').getAttribute('aria-valuenow')==='100');
 assert.match(await page.locator('#progress-count').innerText(),/100 of 100 report pairs · 100%/);
 assert.match(await page.locator('#progress-note').innerText(),/1 analysis needs attention/);
 assert.equal(await page.locator('#row-1 .evidence:not([hidden])').count(),0,'streamed results inherit global hidden wording');
 assert.equal(await page.locator('#evidence-1').textContent(),'Show report wording');
 await page.locator('#evidence-1').click();
 assert.equal(await page.locator('#case-list .evidence[hidden]').count(),0,'a streamed case can restore wording globally');
 assert.equal(await page.locator('.case').count(),100);
 await page.locator('#case-36').click();await page.locator('#row-36').getByRole('button',{name:'Retry analysis'}).click();
 await page.waitForFunction(()=>document.querySelector('#row-36 .badge.major')!==null);
 assert.equal(retryPrompt,'Current edited replacement instructions.');

 setScenario(205,'automatic');await page.goto(base);
 await page.waitForFunction(()=>document.getElementById('progress-count').textContent.includes('205 of 205'));
 assert.deepEqual(batchRequests.map(b=>b.cases.length),[100,100,5]);assert.equal(peak,1);
 assert.equal(new Set(batchRequests.flatMap(b=>b.cases.map(c=>c.id))).size,205);

 // UTF-8 payload bytes can split a group below 100, with no lost/truncated text.
 setScenario(11,'automatic',true);await page.goto(base);
 await page.waitForFunction(()=>document.getElementById('progress-count').textContent.includes('11 of 11'));
 assert.deepEqual(batchRequests.map(b=>b.cases.length),[10,1]);
 assert(batchRequests[0].cases[0].resident_report===jobs(11,true)[0].resident_report,'UTF-8 source text must remain exact');

 setScenario(4,'interrupted');await page.goto(base);
 await page.waitForFunction(()=>document.body.textContent.includes('4 still analyzing'));
 send(held[0].res,{type:'case',id:'g1',result:result('g1')});
 await page.waitForFunction(()=>document.getElementById('progress-track').getAttribute('aria-valuenow')==='25');
 held[0].res.destroy();
 await page.waitForFunction(()=>document.getElementById('progress-track').getAttribute('aria-valuenow')==='100');
 assert.equal(await page.locator('.badge').filter({hasText:'Analysis unavailable'}).count(),3);
 assert.equal(await page.locator('#case-list .badge.major').count(),1,'finished result retained after disconnect');

 setScenario(4,'clear');await page.goto(base);
 await page.waitForFunction(()=>document.body.textContent.includes('4 still analyzing'));
 await page.locator('#input-disclosure > summary').click();await page.locator('#clear-button').click();
 assert.equal(await page.locator('.case').count(),0);assert(await page.locator('#analysis-progress').isHidden());
 await page.waitForTimeout(150);assert.equal(batchRequests.length,1);assert.equal(await page.locator('.case').count(),0);
 assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(out,'batch-browser-results.json'),JSON.stringify({passed:true,checks:['100 in one server batch','incremental 0/1/100 percent','source identity','safe model text','edited-prompt retry','205 split as 100/100/5','UTF-8 byte bound','interrupted-stream preservation','clear cancels browser batch','no analysis for view changes']},null,2));
 await browser.close();await new Promise(resolve=>server.close(resolve));console.log('Batch browser checks passed: 100-case streaming, 205-case grouping, byte limits, retries, interrupted streams and clear.');
})().catch(error=>{console.error(error);server.close();process.exit(1);});

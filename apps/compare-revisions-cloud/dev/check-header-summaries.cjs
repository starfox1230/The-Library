// Complete clinical header lists on the website and in self-contained downloads.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output');
const records=html=>JSON.parse(html.match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const context=await browser.newContext({viewport:{width:1280,height:950},acceptDownloads:true}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const u=new URL(route.request().url());return u.hostname==='127.0.0.1'||u.protocol==='file:'||u.protocol==='data:'?route.continue():route.abort();});
 const dense=JSON.parse(fs.readFileSync(path.join(out,'fixtures.json'),'utf8'))[0];
 const cases=[structuredClone(dense),structuredClone(dense),structuredClone(dense),structuredClone(dense)];
 cases.forEach((c,i)=>{c.id='g'+(i+1);c.source_numbers=[i+1];c.case_label=String(i+1);c.status='complete';c.status_message='Analysis complete';c.analysis_warnings=[];});
 cases[1].revisions=[];
 cases[2].revisions=cases[2].revisions.filter(r=>r.importance==='wording');
 cases[3].revisions=[{...cases[3].revisions[0],importance:'review'}];
 // Interleave categories so the assertions cover clinical ordering, not just count.
 cases[0].revisions.reverse();
 await page.route('**/qa',async route=>{const response=await route.fetch(),html=await response.text();await route.fulfill({response,body:html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+JSON.stringify(cases).replaceAll('<','\\u003c')+b)});});
 const expected=cases[0].revisions.filter(r=>r.importance==='major').concat(cases[0].revisions.filter(r=>r.importance==='minor')).map(r=>r.importance);
 assert.ok(expected.length>2);
 async function check(p){
  assert.deepEqual(await p.locator('#row-0 .preview-item').evaluateAll(ns=>ns.map(n=>n.classList.contains('major')?'major':'minor')),expected);
  assert.equal(await p.locator('.preview-item.wording,.preview-item.review,.change-preview .more').count(),0);
  for(const i of [1,2,3])assert.equal(await p.locator('#row-'+i+' .change-preview').count(),0,'nonclinical/completed header stays blank');
  assert.ok(!(await p.locator('.case-header').allInnerTexts()).join(' ').includes('Analysis complete'));
  for(const width of [1280,375,320]){
   await p.setViewportSize({width,height:950});
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'header fits width '+width);
   const sizes=await p.locator('#row-0 .preview-item').evaluateAll(ns=>ns.map(n=>({height:n.getBoundingClientRect().height,scroll:n.scrollHeight,client:n.clientHeight})));
   assert.ok(sizes.every(s=>s.height>0&&s.scroll<=s.client+1),'every summary is fully visible');
  }
  await p.setViewportSize({width:1280,height:950});
  await p.locator('#case-0').click();
  assert.equal(await p.locator('#row-0 .revision').count(),dense.revisions.length,'expanded list keeps wording items');
  await p.locator('#case-0').click();
 }
 await page.goto('http://127.0.0.1:8766/qa');await check(page);
 await page.screenshot({path:path.join(out,'header-summaries.png'),fullPage:true});
 const event=page.waitForEvent('download');await page.locator('#export-review').click();const file=path.join(out,'header-summaries.html');await(await event).saveAs(file);
 const saved=records(fs.readFileSync(file,'utf8'));assert.equal(saved[0].revisions.length,dense.revisions.length);assert.equal(saved[3].revisions[0].importance,'review');
 const offline=await context.newPage();offline.on('pageerror',e=>errors.push(e.message));await offline.goto('file:///'+file.replaceAll('\\','/'));await check(offline);
 assert.deepEqual(errors,[]);console.log('Passed: all Major/Minor header summaries, severity order, no wording/review/completion fallback or +more, expanded full lists, 320–1280px layout and actual offline export.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

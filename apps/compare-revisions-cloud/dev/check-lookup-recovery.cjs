// Production UI/server, synthetic source rows only. No model or external services.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output');
const report=n=>`Case ${n}\nAttending Report:\nFINDINGS:\nSynthetic finding ${n}.\nIMPRESSION:\nSynthetic finding ${n}.\nResident Report:\nFINDINGS:\nSynthetic finding ${n}.\nIMPRESSION:\nSynthetic finding ${n}.\n`;
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const context=await browser.newContext({viewport:{width:1280,height:1000},acceptDownloads:true}),page=await context.newPage(),errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const u=new URL(route.request().url());if(!['127.0.0.1','localhost','file:'].includes(u.hostname)&&u.protocol!=='file:'){external.push(u.href);return route.abort();}return route.continue();});
 // Expose closure state only in intercepted test pages, never in production.
 await page.route(/^http:\/\/127\.0\.0\.1:8766\/(?:qa)?$/,async route=>{
  const response=await route.fetch(),html=await response.text();
  const hook="window.lookupQA={get rows(){return lookupRows},set rows(v){lookupRows=v},images:lookupImages,show:showLookupImage,table:lookupTable,update:updateReview,get focus(){return currentImage?.focusY},set busy(v){ocrBusy=v}};";
  await route.fulfill({response,body:html.replace('})();',hook+'})();')});
 });
 await page.goto('http://127.0.0.1:8766/qa');await page.locator('#input-disclosure > summary').click();
 // A long source image/table exercises the actual View row handler, including
 // its per-image details toggle, at a nonzero inner-table scroll position.
 await page.evaluate(async()=>{
  const c=document.createElement('canvas');c.width=500;c.height=1600;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,500,1600);x.fillStyle='black';x.font='20px Arial';
  for(let i=1;i<=47;i++)x.fillText(i+'     CT900001'+String(i).padStart(3,'0'),10,30*i);
  const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Synthetic screenshot · 47 rows';details.className='lookup-screenshot';details.append(summary);document.querySelector('#lookup-images').append(details);
  const img={id:'synthetic-scroll',bitmap:await createImageBitmap(c),details,summary,label:'Synthetic screenshot',rowsReady:true};lookupQA.images.push(img);
  lookupQA.rows=Array.from({length:47},(_,i)=>({case_number:i+1,accession:'CT900001'+String(i+1).padStart(3,'0'),imageId:img.id,rowY:30*(i+1),source:'Synthetic screenshot'}));
  details.addEventListener('toggle',()=>{if(details.open){lookupQA.show(img);lookupQA.table();}else if(document.querySelector('#lookup-editor').parentElement===details)document.querySelector('#lookup-editor').hidden=true;});
  details.open=true;lookupQA.show(img);lookupQA.table();
 });
 await page.waitForTimeout(100);
 for(const index of [20,35,35]){
  const row=page.locator('#lookup-rows tr').nth(index),view=row.getByRole('button',{name:'View row',exact:true});await view.scrollIntoViewIfNeeded();
  const before=await page.evaluate(()=>({table:document.querySelector('.lookup-table-wrap').scrollTop,page:scrollY}));assert(before.table>300);
  await view.click();await page.waitForTimeout(100);
  const after=await page.evaluate(()=>({table:document.querySelector('.lookup-table-wrap').scrollTop,page:scrollY,image:document.querySelector('#lookup-image').scrollTop,focus:lookupQA.focus}));
  assert.equal(after.table,before.table,'View row must preserve the list scroll');assert(Math.abs(after.page-before.page)<2,'View row must preserve page position');assert(after.image>0);assert.equal(after.focus,30*(index+1));
 }
 await page.screenshot({path:path.join(out,'lookup-scroll-preserved.png')});
 // Explicit list rebuilds (e.g. details toggle/row edit) also retain its offset.
 const offset=await page.locator('.lookup-table-wrap').evaluate(n=>n.scrollTop);await page.evaluate(()=>lookupQA.table());assert.equal(await page.locator('.lookup-table-wrap').evaluate(n=>n.scrollTop),offset);
 // Screenshot-level warnings must follow edits, including conflicts introduced
 // or removed from a previously ready image.
 await page.evaluate(()=>{lookupQA.rows[0].caseIssue='Case number may be incomplete';lookupQA.table();});assert((await page.locator('.lookup-screenshot > summary').textContent()).includes('needs correction'));
 await page.locator('#lookup-rows tr').first().locator('input').first().fill('1');assert((await page.locator('.lookup-screenshot > summary').textContent()).includes('ready'));
 await page.locator('#lookup-rows tr').first().locator('input').first().fill('2');assert((await page.locator('.lookup-screenshot > summary').textContent()).includes('needs correction'));
 await page.locator('#lookup-rows tr').first().locator('input').first().fill('1');assert((await page.locator('.lookup-screenshot > summary').textContent()).includes('ready'));
 // The actual normal POST must retain all unresolved rows and their crops,
 // while report preparation and known-good accession copying still work.
 await page.goto('http://127.0.0.1:8766/');await page.locator('#report-text').fill(report(68)+report(69));
 await page.evaluate(()=>{
  const c=document.createElement('canvas');c.width=10;c.height=2;const crop=c.toDataURL('image/png');
  lookupQA.rows=[
   {case_number:68,accession:'CT900001068',source_row:crop},
   {case_number:69,accession:'CT900001069',caseIssue:'Case number may be incomplete',source_row:crop},
   {case_number:70,accession:'OT900001070',accessionIssue:'Check accession length'},
   {case_number:71,accession:'CT900001071',caseIssue:'Case number may be incomplete'},{case_number:71,accession:'CT900001072'},
   {case_number:null,accession:'CT900001073'},{case_number:72,accession:''}
  ];lookupQA.table();lookupQA.update();
 });
 let message='';page.once('dialog',async d=>{message=d.message();await d.dismiss();});await page.locator('#analyze-button').click();assert(message.includes('6 lookup rows need attention'));assert(await page.locator('#analyze-button').isEnabled());assert((await page.locator('#form-status').innerText()).includes('Analysis not started'));
 page.once('dialog',d=>d.accept());await Promise.all([page.waitForNavigation(),page.locator('#analyze-button').click()]);
 const rows=JSON.parse(await page.locator('#lookup-data').textContent());assert.equal(rows.length,7);assert.equal(rows[1].caseIssue,'Case number may be incomplete');assert(rows[1].source_row);assert.equal(rows[2].accessionIssue,'Check accession length');assert.equal(rows[5].case_number,null);
 const cases=JSON.parse(await page.locator('#review-data').textContent());assert(cases.length>0);assert(!JSON.stringify(cases).includes('CT900001'));
 assert((await page.locator('#lookup-count').textContent()).includes('6 need checking'),await page.locator('#lookup-count').textContent());assert.equal(await page.locator('#row-0 .case-copy-accession').count(),1);assert.equal(await page.locator('#row-1 .case-copy-accession').count(),0);
 if(!await page.locator('#lookup-manual').isVisible())await page.locator('#input-disclosure > summary').click();await page.locator('#lookup-manual > summary').click();await page.locator('#lookup-rows tr').nth(1).getByRole('button',{name:'View row',exact:true}).click();assert(await page.locator('#lookup-rows tr').nth(1).locator('img').evaluate(n=>n.complete&&n.naturalWidth>0),'source crop must remain available after analysis');
 // Correcting a retained warning attaches its exact case without a fresh analysis.
 await page.locator('#lookup-rows tr').nth(1).locator('input').first().fill('69');assert.equal(await page.locator('#row-1 .case-copy-accession').count(),1);
 // Export proceeds with only usable, unambiguous mappings; conflicts never
 // become arbitrary first/last-wins identifiers in the reader.
 page.once('dialog',d=>d.accept());const downloadPromise=page.waitForEvent('download');await page.locator('#export-review').click();const download=await downloadPromise,file=path.join(out,'lookup-best-available.html');await download.saveAs(file);
 const html=fs.readFileSync(file,'utf8'),match=html.match(/<script id="lookup-data" type="application\/json">([\s\S]*?)<\/script>/);assert.deepEqual(JSON.parse(match[1]).map(r=>r.case_number),[68,69]);assert(!html.includes('CT900001071'));assert(!html.includes('CT900001072'));
 // Busy OCR is also a choice, not an unconditional Analyze blocker.
 await page.goto('http://127.0.0.1:8766/');await page.locator('#report-text').fill(report(68));await page.evaluate(()=>{lookupQA.busy=true;lookupQA.rows=[{case_number:68,accession:'CT900001068'}];});
 page.once('dialog',async d=>{assert(d.message().includes('OCR is still running'));await d.accept();});await Promise.all([page.waitForNavigation(),page.locator('#analyze-button').click()]);assert.equal(JSON.parse(await page.locator('#lookup-data').textContent()).length,1);
 // A clean batch requires no confirmation at all.
 if(!await page.locator('#report-text').isVisible())await page.locator('#input-disclosure > summary').click();page.once('dialog',d=>{errors.push('Unexpected confirmation for clean rows');return d.dismiss();});await Promise.all([page.waitForNavigation(),page.locator('#analyze-button').click()]);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);console.log('View-row scroll, cancel/proceed, retained warnings/source crops, exact usable joins, partial export, busy OCR and clean submission checks passed.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

// Actual OCR worker + actual production template/export endpoint; loopback synthetic data only.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:1000},acceptDownloads:true});
  const page=await context.newPage(),errors=[],unexpected=[],posts=[];
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/*',route=>{const u=new URL(route.request().url());if(u.protocol==='file:')return route.continue();if(!['127.0.0.1','localhost'].includes(u.hostname)){unexpected.push(u.href);return route.abort();}if(route.request().method()==='POST')posts.push(route.request().postData());return route.continue();});
  await page.goto('http://127.0.0.1:8766/qa');await page.locator('#input-disclosure > summary').click();
  await page.evaluate(()=>{window.ocrStatuses=[];new MutationObserver(records=>{for(const r of records)for(const n of r.addedNodes)window.ocrStatuses.push(n.textContent);}).observe(document.querySelector('#ocr-status'),{childList:true});});
  async function checkProgress(phase,total){const messages=await page.evaluate(()=>window.ocrStatuses),values=messages.filter(s=>s.includes(phase+'…')).map(s=>Number(s.match(/\((\d+)%\)$/)?.[1]));assert(values.length>=3,'must expose completed work, not per-recognition percentages');assert.equal(values[0],0);assert.equal(values.at(-1),100);assert(values.every((v,i)=>Number.isFinite(v)&&(i===0||v>=values[i-1])),'progress must never jump backward within a pass');assert(messages.some(s=>s.includes(phase+'… '+total+' of '+total+' (100%)')));}
  async function pasteImage(buffer,name='synthetic.png'){
   await page.locator('#lookup-paste-zone').evaluate((zone,data)=>{const bytes=Uint8Array.from(atob(data.base64),c=>c.charCodeAt(0)),transfer=new DataTransfer();transfer.items.add(new File([bytes],data.name,{type:'image/png'}));zone.dispatchEvent(new ClipboardEvent('paste',{bubbles:true,clipboardData:transfer}));},{name,base64:buffer.toString('base64')});
  }
  const tableImage=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=700;c.height=410;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,700,410);x.fillStyle='black';x.font='28px Consolas';x.fillText('Case',24,36);x.fillText('Accession',200,36);for(const [i,n] of [68,69,70,71,74,78].entries()){x.fillText(String(n),24,90+i*48);x.fillText('CT9012'+n+'345',200,90+i*48);}return c.toDataURL('image/png').split(',')[1];});
  fs.writeFileSync(path.join(out,'lookup-synthetic.png'),Buffer.from(tableImage,'base64'));
  assert.equal(await page.locator('.phi-banner').count(),0);
  await pasteImage(Buffer.from(tableImage,'base64'));
  await page.waitForFunction(()=>document.querySelectorAll('#lookup-rows tr').length===6,{},{timeout:90000});
  await checkProgress('Reading columns',2);
  const values=await page.locator('#lookup-rows tr').evaluateAll(rows=>rows.map(r=>[...r.querySelectorAll('input')].slice(0,2).map(i=>i.value)));
  assert.deepEqual(values,[68,69,70,71,74,78].map(n=>[String(n),'CT9012'+n+'345']));
  assert.equal(await page.locator('.copy-accession').count(),4,'valid OCR attaches without individual approval');assert.equal(await page.locator('#lookup-rows input[type=checkbox]').count(),0);
  assert.equal(await page.locator('#export-review').isDisabled(),false);
  await pasteImage(Buffer.from(tableImage,'base64'));
  await page.waitForFunction(()=>document.querySelectorAll('#lookup-images button').length===2&&!document.querySelector('#export-review').disabled,{},{timeout:90000});
  assert.equal(await page.locator('#lookup-rows tr').count(),6,'overlapping identical screenshot rows are deduplicated');
  assert.equal(await page.locator('.copy-accession').count(),4);
  await page.locator('#lookup-rows input').first().focus();await page.screenshot({path:path.join(out,'lookup-preparation-dark.png'),fullPage:true});
  await page.evaluate(()=>{window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>window.copied.push(value)}});});
  await page.locator('#row-0 .case-copy-accession').click();
  assert.deepEqual(await page.evaluate(()=>window.copied),['CT901268345']);
  assert.equal(await page.locator('#row-0 .case-copy-accession .accession-copy-feedback').innerText(),'Accession copied');assert.equal(await page.locator('#case-0').getAttribute('aria-expanded'),'false','copy must not expand a case');assert.equal(await page.locator('#row-0 .accession-tools').count(),0);
  // Sorting must not alter source membership or primary copied accession.
  await page.locator('#order').selectOption('newest');await page.locator('#row-0 .case-copy-accession').click();
  assert.deepEqual(await page.evaluate(()=>window.copied),['CT901268345','CT901268345']);
  await page.locator('#order').selectOption('oldest');
  const downloadPromise=page.waitForEvent('download');await page.locator('#export-review').click();const download=await downloadPromise;
  const exported=path.join(out,'clinical-review.html');await download.saveAs(exported);
  const html=fs.readFileSync(exported,'utf8');for(const text of ['EXCLUDE_COMPARISON','EXCLUDE_TECHNIQUE','EXCLUDE_SIGNATURE','EXCLUDE_RAW_WARNING','EXCLUDE_RAW_INPUT','lookup-panel','custom-prompt','/ocr-assets/','/analyze-batch'])assert(!html.includes(text),text+' leaked');
  assert(html.includes('CT901268345'));assert(html.includes('Contains PHI.'));
  // Offline reader must issue no requests and retain its ordinary controls.
  const offlineContext=await browser.newContext();await offlineContext.addInitScript(()=>{Storage.prototype.getItem=()=>null;Storage.prototype.setItem=()=>{throw Error('Storage unavailable');};});await offlineContext.route('**/*',route=>new URL(route.request().url()).protocol==='file:'?route.continue():route.abort());
  const reader=await offlineContext.newPage(),requests=[];reader.on('pageerror',e=>errors.push(e.message));reader.on('request',r=>requests.push(r.url()));
  await reader.goto('file:///'+exported.replaceAll('\\','/'));requests.length=0;
  assert.equal(await reader.locator('.case').count(),4);assert.equal(await reader.locator('.phi-banner').count(),1);
  await reader.locator('#case-0').click();assert.equal(await reader.locator('#row-0 .accession-line').count(),2);assert.equal(await reader.locator('#case-0').getAttribute('aria-expanded'),'true');
  await reader.locator('#theme-toggle').click();await reader.locator('#combined-view').uncheck();
  await reader.locator('#tab-0-reports').click();assert((await reader.locator('#view-0').innerText()).toLowerCase().includes('resident clinical report'));
  await reader.locator('#search').fill('CT901269345');assert.equal(await reader.locator('.case').count(),1);
  await reader.locator('#search').fill('');await reader.locator('#order').selectOption('newest');
  await reader.screenshot({path:path.join(out,'export-reader-light.png'),fullPage:true});
  await reader.locator('#theme-toggle').click();await reader.waitForFunction(()=>getComputedStyle(document.querySelector('.case:not(.is-open)')).backgroundColor==='rgb(25, 31, 40)');await reader.screenshot({path:path.join(out,'export-reader-dark.png'),fullPage:true});
  assert.deepEqual(requests,[]);assert.deepEqual(unexpected,[]);assert.deepEqual(errors,[]);
  assert(posts.length===1,'OCR must not upload screenshots or contact analysis');
  await reader.locator('#search').fill('CT901268345');
  await reader.evaluate(()=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:undefined});document.execCommand=command=>{window.offlineCopy={command,value:document.activeElement.value};return true;};});
  await reader.locator('#row-0 .case-copy-accession').click();assert.deepEqual(await reader.evaluate(()=>window.offlineCopy),{command:'copy',value:'CT901268345'});
  // Filtered exports omit other entries and their identifiers from serialized data.
  await page.locator('#search').fill('78');await page.locator('#export-filtered').check();
  const subsetDownload=page.waitForEvent('download');await page.locator('#export-review').click();const subset=await subsetDownload;
  const subsetPath=path.join(out,'clinical-review-subset.html');await subset.saveAs(subsetPath);const subsetHTML=fs.readFileSync(subsetPath,'utf8');assert(subsetHTML.includes('CT901278345'));assert(!subsetHTML.includes('CT901268345'));assert(!subsetHTML.includes('CT901269345'));
  await page.locator('#search').fill('');await page.locator('#export-filtered').uncheck();
  // Conflict/manual correction and partial coverage, no positional reassignment.
  await page.locator('#lookup-add').click();let last=page.locator('#lookup-rows tr').last();await last.locator('input').nth(0).fill('68');await last.locator('input').nth(1).fill('DIFFERENT0001');await last.locator('input').nth(1).blur();
  assert.equal(await page.locator('#export-review').isDisabled(),true);await page.locator('#row-0 .case-copy-accession').click();assert.equal(await page.evaluate(()=>window.copied.at(-1)),'CT901269345');
  await page.locator('#lookup-rows tr').last().getByRole('button',{name:'Remove'}).click();
  const originalInput=await page.locator('#report-text').inputValue();if(!await page.locator('#report-text').isVisible())await page.locator('#input-disclosure > summary').click();await page.locator('#report-text').fill('Changed report batch');assert.equal(await page.locator('.copy-accession').count(),0);assert.equal(await page.locator('#export-review').isDisabled(),true);await page.locator('#report-text').fill(originalInput);
  // Explicit range fallback must not run without acknowledgement or with a
  // count mismatch. It changes case labels only, never accession strings.
  await page.getByRole('button',{name:'Screenshot 1',exact:true}).click();await page.locator('#lookup-range-tools > summary').click();await page.locator('#lookup-range-first').fill('68');await page.locator('#lookup-range-last').fill('73');
  const beforeRange=await page.locator('#lookup-rows input[aria-label^="Accession"]').evaluateAll(xs=>xs.map(x=>x.value));
  await page.locator('#lookup-range-apply').click();assert((await page.locator('#lookup-range-status').innerText()).includes('Check that every case'));assert.equal(await page.locator('#lookup-rows input[aria-label^="Case number"]').last().inputValue(),'78');
  await page.locator('#lookup-range-checked').check();await page.locator('#lookup-range-last').fill('74');await page.locator('#lookup-range-apply').click();assert((await page.locator('#lookup-range-status').innerText()).includes('7 cases, but 6'));
  // Deliberate operator override for testing only; this synthetic source has
  // nonconsecutive labels, so automatic repair correctly leaves them unchanged.
  await page.locator('#lookup-range-last').fill('73');await page.locator('#lookup-range-apply').click();assert.deepEqual(await page.locator('#lookup-rows input[aria-label^="Case number"]').evaluateAll(xs=>xs.map(x=>x.value)),['68','69','70','71','72','73']);assert.deepEqual(await page.locator('#lookup-rows input[aria-label^="Accession"]').evaluateAll(xs=>xs.map(x=>x.value)),beforeRange);assert.equal(await page.locator('#lookup-rows input[type=checkbox]:checked').count(),0);
  await page.locator('#lookup-clear').click();assert.equal(await page.locator('.copy-accession').count(),0);
  assert.equal(await page.locator('#lookup-rows tr').count(),0);
  // Headerless images require explicit visual column selection, not guessing.
  const image=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=1350;c.height=410;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,c.width,c.height);x.fillStyle='black';x.font='28px Consolas';for(const [i,n] of [68,69,70,71,74,78].entries()){x.fillText(String(n),24,40+i*53);x.fillText('9876543',170,40+i*53);x.fillText('CT9012'+n+'345',430,40+i*53);}return c.toDataURL('image/png').split(',')[1];});
  await pasteImage(Buffer.from(image,'base64'),'synthetic-no-header.png');
  await page.waitForFunction(()=>document.querySelectorAll('#lookup-rows tr').length===6,{},{timeout:90000});
  assert.equal(await page.locator('#mark-case,#mark-accession,#read-columns,input[type=file]').count(),0);
  assert.deepEqual(await page.locator('#lookup-rows tr').evaluateAll(rs=>rs.map(r=>[...r.querySelectorAll('input')].slice(0,2).map(i=>i.value))),values);
  await page.locator('#lookup-clear').click();
  // A narrow screenshot makes two OCR calls per row. Worker progress restarts
  // for every call; visible progress must instead count completed rows once.
  await page.evaluate(()=>{window.ocrStatuses=[];});
  const narrow=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=210;c.height=200;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,c.width,c.height);x.fillStyle='black';x.font='16px Consolas';x.fillText('Case',8,20);x.fillText('Accession',80,20);for(let i=0;i<6;i++){x.fillText(String(i+1),12,48+i*26);x.fillText('CT90000000'+(i+1),80,48+i*26);}return c.toDataURL('image/png').split(',')[1];});
  await pasteImage(Buffer.from(narrow,'base64'),'synthetic-narrow.png');
  await page.waitForFunction(()=>document.querySelector('#ocr-status').textContent.startsWith('Read 6 rows.'),{},{timeout:90000});
  await checkProgress('Reading rows',6);await page.waitForTimeout(200);assert((await page.locator('#ocr-status').innerText()).startsWith('Read 6 rows.'),'late worker events must not overwrite completion');
  await page.locator('#lookup-clear').click();await page.waitForTimeout(200);assert.equal(await page.locator('#ocr-status').innerText(),'');
  // Partly overlapping screenshots retain original numbers without approvals.
  // 55–59 plus 57–61 must yield seven mappings, with 57–59 appearing once.
  const overlapImage=async first=>page.evaluate(first=>{const c=document.createElement('canvas');c.width=700;c.height=340;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,c.width,c.height);x.fillStyle='black';x.font='28px Consolas';x.fillText('Case',24,36);x.fillText('Accession',200,36);for(let i=0;i<5;i++){const n=first+i;x.fillText(String(n),24,90+i*48);x.fillText('CT9012'+n+'345',200,90+i*48);}return c.toDataURL('image/png').split(',')[1];},first);
  for(const [index,first] of [55,57].entries()){
   await pasteImage(Buffer.from(await overlapImage(first),'base64'),'synthetic-overlap-'+index+'.png');
   await page.waitForFunction(count=>document.querySelector('#ocr-status').textContent.startsWith('Read 5 rows.')&&document.querySelectorAll('#lookup-rows tr').length===count,index===0?5:7,{timeout:90000});
   assert.equal(await page.locator('#lookup-rows input[type=checkbox]').count(),0);
  }
  assert.deepEqual(await page.locator('#lookup-rows tr').evaluateAll(rs=>rs.map(r=>[...r.querySelectorAll('input')].slice(0,2).map(i=>i.value))),[55,56,57,58,59,60,61].map(n=>[String(n),'CT9012'+n+'345']));
  assert(!(await page.locator('#lookup-coverage').innerText()).includes('Duplicate case numbers'),'identical overlap is not a conflict');
  await page.locator('#lookup-clear').click();
  await page.setViewportSize({width:375,height:900});await page.locator('#lookup-add').click();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'lookup must not overflow mobile viewport');
  const guardPage=await context.newPage();await guardPage.goto('http://127.0.0.1:8766/qa');const normalPageHTML=await guardPage.content();let invalidDownloads=0;guardPage.on('download',()=>invalidDownloads++);await guardPage.route('**/export-review',route=>route.fulfill({contentType:'text/html',body:normalPageHTML}));await guardPage.locator('#export-review').click();await guardPage.waitForFunction(()=>document.querySelector('#export-status').textContent.includes('sign-in expired'));assert.equal(invalidDownloads,0,'login/main-page HTML must not be downloaded as a review');
  const formPage=await context.newPage();await formPage.goto('http://127.0.0.1:8766/qa');await formPage.locator('#input-disclosure > summary').click();await formPage.locator('#lookup-add').click();await formPage.locator('#lookup-rows input').nth(0).fill('68');
  await formPage.locator('#report-text').fill('New report batch for intercepted synthetic form test.');await formPage.locator('#analyze-button').click();assert((await formPage.locator('#form-status').innerText()).includes('incomplete or conflicting'));
  await formPage.locator('#lookup-rows input').nth(1).fill('CT901268345');let submitted;
  await formPage.route('**/qa',route=>{if(route.request().method()==='POST'){submitted=new URLSearchParams(route.request().postData());return route.fulfill({contentType:'text/html',body:'<title>Synthetic submission captured</title>'});}return route.continue();});
  await formPage.locator('#analyze-button').click();await formPage.waitForFunction(()=>document.title==='Synthetic submission captured');assert.deepEqual(JSON.parse(submitted.get('lookup_json')),[{case_number:68,accession:'CT901268345',confirmed:true}]);assert.equal(submitted.get('reports_text'),'New report batch for intercepted synthetic form test.');
  assert.deepEqual(errors,[]);console.log('Real OCR, steady row/column progress, automatic lookup acceptance, exact case joins, grouped accession copying, conflict handling, private-data exclusions and offline reader checks passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

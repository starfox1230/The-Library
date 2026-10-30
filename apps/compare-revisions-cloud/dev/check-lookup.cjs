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
  await page.goto('http://127.0.0.1:8766/qa');await page.locator('#lookup-panel > summary').click();
  assert.equal(await page.locator('.phi-banner').count(),0);
  await page.locator('#lookup-files').setInputFiles(path.join(out,'lookup-synthetic.png'));
  await page.waitForFunction(()=>document.querySelectorAll('#lookup-rows tr').length===6,{},{timeout:90000});
  const values=await page.locator('#lookup-rows tr').evaluateAll(rows=>rows.map(r=>[...r.querySelectorAll('input')].slice(0,2).map(i=>i.value)));
  assert.deepEqual(values,[68,69,70,71,74,78].map(n=>[String(n),'00000'+n+'001']));
  assert.equal(await page.locator('.copy-accession').count(),0,'unconfirmed OCR must never attach');
  assert.equal(await page.locator('#export-review').isDisabled(),true);
  for(const checkbox of await page.locator('#lookup-rows input[type=checkbox]').all())await checkbox.check();
  await page.locator('#lookup-files').setInputFiles(path.join(out,'lookup-synthetic.png'));
  await page.waitForFunction(()=>document.querySelectorAll('#lookup-images button').length===2&&!document.querySelector('#export-review').disabled,{},{timeout:90000});
  assert.equal(await page.locator('#lookup-rows tr').count(),6,'overlapping identical screenshot rows are deduplicated');
  assert.equal(await page.locator('.copy-accession').count(),4);
  await page.locator('#lookup-rows input').first().focus();await page.screenshot({path:path.join(out,'lookup-preparation-dark.png'),fullPage:true});
  await page.evaluate(()=>{window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>window.copied.push(value)}});});
  await page.locator('#row-0 .copy-accession').click();
  assert.deepEqual(await page.evaluate(()=>window.copied),['0000068001']);
  assert.equal(await page.locator('#row-0 .copy-accession').innerText(),'Accession copied');
  // Sorting must not alter source membership or primary copied accession.
  await page.locator('#order').selectOption('newest');await page.locator('#row-0 .copy-accession').click();
  assert.deepEqual(await page.evaluate(()=>window.copied),['0000068001','0000068001']);
  await page.locator('#order').selectOption('oldest');
  const downloadPromise=page.waitForEvent('download');await page.locator('#export-review').click();const download=await downloadPromise;
  const exported=path.join(out,'clinical-review.html');await download.saveAs(exported);
  const html=fs.readFileSync(exported,'utf8');for(const text of ['EXCLUDE_COMPARISON','EXCLUDE_TECHNIQUE','EXCLUDE_SIGNATURE','EXCLUDE_RAW_WARNING','EXCLUDE_RAW_INPUT','lookup-panel','custom-prompt','/ocr-assets/','/analyze-batch'])assert(!html.includes(text),text+' leaked');
  assert(html.includes('0000068001'));assert(html.includes('Contains PHI.'));
  // Offline reader must issue no requests and retain its ordinary controls.
  const reader=await context.newPage(),requests=[];reader.on('pageerror',e=>errors.push(e.message));reader.on('request',r=>requests.push(r.url()));
  await reader.goto('file:///'+exported.replaceAll('\\','/'));requests.length=0;
  assert.equal(await reader.locator('.case').count(),4);assert.equal(await reader.locator('.phi-banner').count(),1);
  await reader.locator('#case-0').click();assert.equal(await reader.locator('#case-0').getAttribute('aria-expanded'),'true');
  await reader.locator('#theme-toggle').click();await reader.locator('#combined-view').uncheck();
  await reader.locator('#tab-0-reports').click();assert((await reader.locator('#view-0').innerText()).toLowerCase().includes('resident clinical report'));
  await reader.locator('#search').fill('0000069001');assert.equal(await reader.locator('.case').count(),1);
  await reader.locator('#search').fill('');await reader.locator('#order').selectOption('newest');
  await reader.screenshot({path:path.join(out,'export-reader-light.png'),fullPage:true});
  await reader.locator('#theme-toggle').click();await reader.waitForFunction(()=>getComputedStyle(document.querySelector('.case:not(.is-open)')).backgroundColor==='rgb(25, 31, 40)');await reader.screenshot({path:path.join(out,'export-reader-dark.png'),fullPage:true});
  assert.deepEqual(requests,[]);assert.deepEqual(unexpected,[]);assert.deepEqual(errors,[]);
  assert(posts.length===1,'OCR must not upload screenshots or contact analysis');
  await reader.locator('#search').fill('0000068001');
  await reader.evaluate(()=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:undefined});document.execCommand=command=>{window.offlineCopy={command,value:document.activeElement.value};return true;};});
  await reader.locator('#row-0 .copy-accession').click();assert.deepEqual(await reader.evaluate(()=>window.offlineCopy),{command:'copy',value:'0000068001'});
  // Filtered exports omit other entries and their identifiers from serialized data.
  await page.locator('#search').fill('78');await page.locator('#export-filtered').check();
  const subsetDownload=page.waitForEvent('download');await page.locator('#export-review').click();const subset=await subsetDownload;
  const subsetPath=path.join(out,'clinical-review-subset.html');await subset.saveAs(subsetPath);const subsetHTML=fs.readFileSync(subsetPath,'utf8');assert(subsetHTML.includes('0000078001'));assert(!subsetHTML.includes('0000068001'));assert(!subsetHTML.includes('0000069001'));
  await page.locator('#search').fill('');await page.locator('#export-filtered').uncheck();
  // Conflict/manual correction and partial coverage, no positional reassignment.
  await page.locator('#lookup-add').click();let last=page.locator('#lookup-rows tr').last();await last.locator('input').nth(0).fill('68');await last.locator('input').nth(1).fill('DIFFERENT0001');await last.locator('input').nth(1).blur();
  assert.equal(await page.locator('#export-review').isDisabled(),true);assert.equal(await page.locator('#row-0 .copy-accession').getAttribute('title'),'Copy 0000069001 (source case 69)');
  await page.locator('#lookup-rows tr').last().getByRole('button',{name:'Remove'}).click();
  const originalInput=await page.locator('#report-text').inputValue();await page.locator('#input-disclosure > summary').click();await page.locator('#report-text').fill('Changed report batch');assert.equal(await page.locator('.copy-accession').count(),0);assert.equal(await page.locator('#export-review').isDisabled(),true);await page.locator('#report-text').fill(originalInput);
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
  const image=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=1350;c.height=410;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,c.width,c.height);x.fillStyle='black';x.font='28px Consolas';for(const [i,n] of [68,69,70,71,74,78].entries()){x.fillText(String(n),24,40+i*53);x.fillText('9876543',170,40+i*53);x.fillText('00000'+n+'001',430,40+i*53);}return c.toDataURL('image/png').split(',')[1];});
  await page.locator('#lookup-files').setInputFiles({name:'synthetic-no-header.png',mimeType:'image/png',buffer:Buffer.from(image,'base64')});
  await page.waitForFunction(()=>document.querySelector('#ocr-status').textContent.startsWith('Screenshot read.'),{},{timeout:90000});
  assert.equal(await page.locator('#lookup-rows tr').count(),0);
  for(const [button,x0,x1] of [['#mark-case',0,120],['#mark-accession',400,670]]){await page.locator(button).click();await page.locator('#lookup-canvas').scrollIntoViewIfNeeded();const box=await page.locator('#lookup-canvas').boundingBox(),scale=box.width/1350,y=box.y+40;await page.mouse.move(box.x+x0*scale+1,y);await page.mouse.down();await page.mouse.move(box.x+x1*scale,y);await page.mouse.up();}
  await page.locator('#read-columns').click();await page.waitForFunction(()=>document.querySelectorAll('#lookup-rows tr').length===6,{},{timeout:90000});
  assert.deepEqual(await page.locator('#lookup-rows tr').evaluateAll(rs=>rs.map(r=>[...r.querySelectorAll('input')].slice(0,2).map(i=>i.value))),values);
  await page.locator('#lookup-clear').click();await page.setViewportSize({width:375,height:900});await page.locator('#lookup-add').click();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'lookup must not overflow mobile viewport');
  console.log('Real OCR, confirmation, exact case joins, grouped accession copying, conflict handling, private-data exclusions and offline reader checks passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

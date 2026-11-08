// Size-to-content controls, pinned details, all-case offers, hover timeout and sticky downloads.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output');
async function download(page,selector,file){const event=page.waitForEvent('download');await page.locator(selector).click();await(await event).saveAs(file);return fs.readFileSync(file,'utf8');}
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const context=await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const u=new URL(route.request().url());return u.hostname==='127.0.0.1'||u.protocol==='file:'||u.protocol==='data:'?route.continue():route.abort();});
 await page.route('**/qa',async route=>{
  const response=await route.fetch(),html=await response.text(),match=html.match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/),cases=JSON.parse(match[1]);
  for(const c of cases.slice(0,2)){
   c.revisions=structuredClone(cases[0].revisions.slice(0,1));c.revisions[0].reason='Synthetic first explanation.';
   c.revisions[0].resident_summary='Small pleural effusion with a deliberately long synthetic description to verify a wrapped summary';c.revisions[0].attending_summary='Moderate pleural effusion with additional synthetic descriptive wording';
   const second=structuredClone(c.revisions[0]);second.reason='Synthetic second explanation.';second.resident_summary='Small renal cyst';second.attending_summary='Stable small renal cyst';c.revisions.push(second);
  }
  await route.fulfill({response,body:html.replace(match[1],JSON.stringify(cases).replaceAll('<','\\u003c'))});
 });
 await page.goto('http://127.0.0.1:8766/qa');
 assert.ok((await page.locator('#filter-major').boundingBox()).width<130);assert.ok((await page.locator('#search').boundingBox()).width<=320);
 const filters=await page.locator('#filter-all,#filter-major,#filter-minor,#filter-wording,#filter-review,#filter-favorite,#filter-flagged,#more-filters').evaluateAll(ns=>ns.map(n=>n.getBoundingClientRect().top));assert.ok(filters.every(y=>Math.abs(y-filters[0])<2));
 await page.locator('#case-0').click();await page.locator('#case-1').click();
 assert.equal(await page.locator('.evidence:visible,.reason:visible').count(),0);
 await page.locator('#revision-0-0').hover();await page.waitForTimeout(200);assert.equal(await page.locator('.evidence:visible,.reason:visible').count(),0);
 const heights=await page.evaluate(async()=>{
  const card=document.querySelector('#row-0 [data-revision-index="0"]'),details=card.querySelector('.revision-details');card.querySelector('.revision-link').click();
  const first=details.getBoundingClientRect().height;await new Promise(r=>setTimeout(r,80));const middle=details.getBoundingClientRect().height;await new Promise(r=>setTimeout(r,200));return [first,middle,details.getBoundingClientRect().height];
 });assert.ok(heights[1]>heights[0]&&heights[1]<heights[2],JSON.stringify(heights));
 assert.equal(await page.locator('#row-0 .reason:visible').count(),1);assert.equal(await page.locator('#row-0 .evidence:visible').count(),1);assert.equal(await page.locator('#row-1 .reason:visible,#row-1 .evidence:visible').count(),0);
 await page.locator('#revision-0-1').click();assert.equal(await page.locator('#row-0 [data-revision-index="0"] .reason').isVisible(),false);assert.ok(await page.locator('#row-0 [data-revision-index="1"] .evidence').isVisible());await page.locator('#revision-0-1').click();
 await page.locator('#explanation-0').click();await page.locator('#explanation-all-0').click();assert.equal(await page.locator('.reason:visible').count(),4);assert.equal(await page.locator('.evidence:visible').count(),0);
 await page.locator('#explanation-0').click();await page.locator('#explanation-all-0').click();assert.equal(await page.locator('.reason:visible').count(),0);
 await page.locator('#evidence-0').click();await page.locator('#wording-all-0').click();assert.equal(await page.locator('.evidence:visible').count(),4);
 await page.locator('#evidence-0').click();await page.locator('#wording-all-0').click();assert.equal(await page.locator('.evidence:visible').count(),0);
 const centers=await page.locator('#row-0 .revision-heading').first().evaluate(n=>{const a=n.querySelector('.action').getBoundingClientRect(),h=n.querySelector('h4').getBoundingClientRect();return [a.top+a.height/2,h.top+h.height/2,h.height];});assert.ok(centers[2]>25);assert.ok(Math.abs(centers[0]-centers[1])<1);
 await page.clock.install();await page.locator('#favorite-0').click();await page.locator('#review-toast').hover();await page.clock.fastForward(12000);assert.ok(await page.locator('#review-toast').isVisible());
 await page.mouse.move(1,1);await page.clock.fastForward(3900);assert.ok(await page.locator('#review-toast').isVisible());await page.clock.fastForward(200);assert.equal(await page.locator('#review-toast').isVisible(),false);
 await page.locator('#feedback-0').click();await page.locator('#feedback-done').click();
 const file=path.join(out,'revision-details-export.html');await download(page,'#export-review',file);
 const offline=await context.newPage();offline.on('pageerror',e=>errors.push(e.message));await offline.setViewportSize({width:1280,height:650});await offline.goto('file:///'+file.replaceAll('\\','/'));
 assert.equal(await offline.locator('#banner-save-review').isVisible(),false);const height=(await offline.locator('.phi-banner').boundingBox()).height;
 await offline.locator('#case-0').click();await offline.evaluate(()=>scrollTo(0,550));await offline.waitForFunction(()=>!document.querySelector('.phi-downloads').hidden);
 assert.equal((await offline.locator('.phi-banner').boundingBox()).height,height);assert.ok(await offline.locator('#banner-save-review').isVisible());
 await download(offline,'#banner-save-review',path.join(out,'revision-details-banner-copy.html'));const feedback=await download(offline,'#banner-feedback',path.join(out,'revision-details-banner-feedback.html'));assert.equal(JSON.parse(feedback.match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/)[1]).length,1);
 await offline.screenshot({path:path.join(out,'revision-details-banner.png')});
 await offline.evaluate(()=>scrollTo(0,0));await offline.waitForFunction(()=>document.querySelector('.phi-downloads').hidden);assert.equal((await offline.locator('.phi-banner').boundingBox()).height,height);
 await offline.setViewportSize({width:390,height:650});await offline.waitForTimeout(100);const mobileHeight=(await offline.locator('.phi-banner').boundingBox()).height;await offline.evaluate(()=>scrollTo(0,900));await offline.waitForFunction(()=>!document.querySelector('.phi-downloads').hidden);
 assert.equal((await offline.locator('.phi-banner').boundingBox()).height,mobileHeight);assert.ok(await offline.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await offline.screenshot({path:path.join(out,'revision-details-mobile.png')});
 assert.deepEqual(errors,[]);console.log('Passed: intrinsic filters/search, hidden wording, per-item animated details, independent all-case offers, centered wrapped tags, hover-reset reminder, and fixed-height responsive sticky download actions.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

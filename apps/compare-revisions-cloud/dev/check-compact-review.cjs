// Compact controls, per-case reasons, hover states and transient downloads. Fictional data only.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output');
const data=html=>JSON.parse(html.match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const color=(page,selector)=>page.locator(selector).evaluate(n=>getComputedStyle(n).color);
async function download(page,selector,file){const event=page.waitForEvent('download');await page.locator(selector).click();await(await event).saveAs(file);return fs.readFileSync(file,'utf8');}
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const context=await browser.newContext({viewport:{width:1280,height:1000},acceptDownloads:true}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const url=new URL(route.request().url());return url.hostname==='127.0.0.1'||url.protocol==='file:'||url.protocol==='data:'?route.continue():route.abort();});
 await page.route('**/qa',async route=>{
  const response=await route.fetch(),html=await response.text(),cases=data(html);
  cases[0].revisions[0].reason='AI_EXPLANATION_CASE_0';
  cases[1].revisions=structuredClone(cases[0].revisions);cases[1].revisions[0].reason='AI_EXPLANATION_CASE_1';
  for(const side of ['resident','attending'])cases[1][side+'_report']=cases[0][side+'_report'];
  await route.fulfill({response,body:html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+JSON.stringify(cases).replaceAll('<','\\u003c')+b)});
 });
 await page.goto('http://127.0.0.1:8766/qa');await page.clock.install();
 assert.equal(await page.locator('#mark-counts,#mark-status').count(),0);
 assert.ok(!(await page.locator('body').innerText()).includes('Sterling'));
 assert.equal(await page.locator('#filter-favorite').innerText(),'0');assert.match(await page.locator('#filter-favorite').getAttribute('aria-label'),/Marked for later/);
 assert.equal(await page.locator('#filter-flagged').innerText(),'0');assert.match(await page.locator('#filter-flagged').getAttribute('aria-label'),/Project feedback/);
 assert.equal(await page.locator('#filter-pending').isVisible(),false);await page.locator('#more-filters-label').click();assert.ok(await page.locator('#filter-pending').isVisible());
 await page.locator('#filter-none').click();assert.equal(await page.locator('#more-filters-label').innerText(),'More (1)');await page.keyboard.press('Escape');await page.locator('#reset-filters').click();
 await page.locator('#case-0').click();await page.locator('#case-1').click();
 assert.equal(await page.locator('#row-0 .reason').isVisible(),false);assert.equal(await page.locator('#row-1 .reason').isVisible(),false);
 await page.locator('#explanation-0').click();assert.ok(await page.locator('#row-0 .reason').isVisible());assert.equal(await page.locator('#row-1 .reason').isVisible(),false);
 assert.equal(await page.locator('#explanation-0').innerText(),'Hide AI Explanation');
 const evidenceBefore=await page.locator('#row-0 .evidence').isVisible();await page.locator('#explanation-0').click();assert.equal(await page.locator('#row-0 .evidence').isVisible(),evidenceBefore);
 const positions=await page.locator('#row-0 .summary-tools').evaluate(n=>({explanation:n.querySelector('.explanation-toggle').getBoundingClientRect().left,wording:n.querySelector('.wording-tools:not(.explanation-tools)').getBoundingClientRect().left}));assert.ok(positions.explanation<positions.wording);
 await page.locator('#favorite-0').click();assert.ok(await page.locator('#review-toast').isVisible());
 assert.equal(await color(page,'#favorite-0'),await color(page,'#filter-favorite svg'));
 await page.clock.fastForward(4500);assert.equal(await page.locator('#review-toast').isVisible(),false);
 await page.locator('#favorite-0').click();assert.ok(await page.locator('#review-toast').isVisible());assert.equal(await page.locator('#favorite-0').getAttribute('aria-pressed'),'false');
 await page.locator('#favorite-0').click();await page.locator('#feedback-0').click();assert.ok(await page.locator('#feedback-dialog #review-toast').isVisible());
 await page.locator('#feedback-comment').fill('Synthetic compact UI feedback');
 const modalHTML=await download(page,'#review-toast-download',path.join(out,'compact-modal-download.html'));assert.equal(data(modalHTML)[0].review_marks.comment,'Synthetic compact UI feedback');
 await page.locator('#feedback-remove').click();await page.waitForFunction(()=>document.getElementById('feedback-0').getAttribute('aria-pressed')==='false');assert.ok(await page.locator('#review-toast').isVisible());assert.equal(await page.locator('#feedback-0').getAttribute('aria-pressed'),'false');
 await page.locator('#feedback-0').click();await page.locator('#feedback-done').click();
 for(const theme of ['dark','light']){
  if(await page.locator('#theme-toggle').getAttribute('aria-checked')!==(theme==='dark'?'true':'false'))await page.locator('#theme-toggle').click();
  assert.equal(await color(page,'#feedback-0'),await color(page,'#filter-flagged svg'));assert.notEqual(await color(page,'#favorite-0'),await color(page,'#feedback-0'));
  await page.clock.fastForward(250);await page.locator('#favorite-0').hover();await page.clock.fastForward(250);
  const hover=await page.locator('#favorite-0').evaluate(n=>{const c=getComputedStyle(n),header=getComputedStyle(n.closest('.case-header')),head=getComputedStyle(n.closest('.case-header').querySelector('.case-head'));return {style:c.outlineStyle,border:c.borderColor,background:c.backgroundColor,header:header.backgroundColor,head:head.backgroundColor};});
  assert.equal(hover.style,'none');assert.equal(hover.border,'rgba(0, 0, 0, 0)');assert.notEqual(hover.background,'rgba(0, 0, 0, 0)');assert.notEqual(hover.header,'rgba(0, 0, 0, 0)');assert.equal(hover.head,'rgba(0, 0, 0, 0)');
  await page.screenshot({path:path.join(out,'compact-'+theme+'.png'),fullPage:true});
 }
 await page.locator('#favorite-0').focus();await page.keyboard.press('Tab');
 assert.equal(await page.evaluate(()=>document.activeElement.id),'feedback-0');assert.notEqual(await page.locator('#feedback-0').evaluate(n=>getComputedStyle(n).outlineWidth),'0px');
 await page.locator('#filter-favorite').click();await page.locator('#export-filtered').check();await page.locator('#favorite-0').click();
 const full=await download(page,'#review-toast-download',path.join(out,'compact-full-download.html'));assert.equal(data(full).length,4);assert.equal(data(full)[0].revisions[0].reason,'AI_EXPLANATION_CASE_0');
 const offline=await context.newPage();offline.on('pageerror',e=>errors.push(e.message));await offline.goto('file:///'+path.join(out,'compact-full-download.html').replaceAll('\\','/'));await offline.locator('#case-0').click();assert.equal(await offline.locator('#row-0 .reason').isVisible(),false);assert.equal(await offline.locator('#review-toast').isVisible(),false);
 await offline.locator('#favorite-0').click();await download(offline,'#review-toast-download',path.join(out,'compact-offline-download.html'));
 await page.locator('#reset-filters').click();await page.setViewportSize({width:390,height:844});await page.locator('#more-filters-label').click();
 await page.waitForFunction(()=>{const r=document.getElementById('status-filters').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth;});const menu=await page.locator('#status-filters').boundingBox();assert.ok(menu.x>=0&&menu.x+menu.width<=390);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.screenshot({path:path.join(out,'compact-mobile.png'),fullPage:true});assert.deepEqual(errors,[]);
 console.log('Passed: full-row and neutral icon hover in both themes, gold/red selection, keyboard focus, compact counted filters/More, per-case hidden explanations, transient reminders on add/remove, clickable modal/live/offline full-copy downloads, and mobile layout.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

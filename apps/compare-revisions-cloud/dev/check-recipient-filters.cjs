// Administrator filters versus recipient UI; diagnostic data stays in the file.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output');
const records=html=>JSON.parse(html.match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
async function download(page,selector,file){const event=page.waitForEvent('download');await page.locator(selector).click();await(await event).saveAs(file);return fs.readFileSync(file,'utf8');}
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const context=await browser.newContext({viewport:{width:1280,height:950},acceptDownloads:true}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const u=new URL(route.request().url());return u.hostname==='127.0.0.1'||u.protocol==='file:'||u.protocol==='data:'?route.continue():route.abort();});
 await page.route('**/qa',async route=>{
  const response=await route.fetch(),html=await response.text(),cases=records(html),item=structuredClone(cases[0].revisions[0]);
  cases[0].revisions[0].importance='review';cases[0].revisions[0].reason='Synthetic uncertain classification retained for troubleshooting.';
  cases[1].revisions=[item];cases[1].status='partial';cases[1].status_message='Review analysis limitations';cases[1].analysis_warnings=['ADMIN_REVIEW_TEST_WARNING'];
  for(const side of ['resident','attending'])cases[1][side+'_report']=cases[0][side+'_report'];
  await route.fulfill({response,body:html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+JSON.stringify(cases).replaceAll('<','\\u003c')+b)});
 });
 await page.goto('http://127.0.0.1:8766/qa');assert.ok(await page.locator('#filter-review').isVisible());
 assert.equal(await page.locator('#filter-wording').isVisible(),false);assert.equal(await page.locator('#filter-wording').evaluate(n=>n.closest('details').id),'more-filters');
 await page.locator('#more-filters-label').click();await page.locator('#filter-wording').click();assert.equal(await page.locator('#more-filters-label').innerText(),'More (1)');await page.locator('#reset-filters').click();
 await page.locator('#case-0').click();assert.match(await page.locator('#row-0').innerText(),/Needs review/i);await page.locator('#case-1').click();assert.match(await page.locator('#row-1').innerText(),/ADMIN_REVIEW_TEST_WARNING/);
 const file=path.join(out,'recipient-filters.html'),html=await download(page,'#export-review',file),data=records(html);
 assert.equal(data.length,4);assert.equal(data[0].revisions[0].importance,'review');assert.match(data[0].revisions[0].reason,/troubleshooting/);
 assert.equal(data[0].admin_diagnostics.ungraded_change_count,1);assert.equal(data[1].admin_diagnostics.source_status,'partial');assert.equal(data[1].admin_diagnostics.had_analysis_warnings,true);assert.ok(!html.includes('ADMIN_REVIEW_TEST_WARNING'));
 const offline=await context.newPage();offline.on('pageerror',e=>errors.push(e.message));await offline.goto('file:///'+file.replaceAll('\\','/'));
 await offline.locator('#case-0').click();await offline.locator('#case-1').click();await offline.locator('#more-filters-label').click();
 assert.equal(await offline.locator('#filter-review').count(),0);assert.ok(await offline.locator('#filter-wording').isVisible());
 const visible=await offline.locator('body').innerText();assert.ok(!/needs? review|analysis incomplete|additional changes|ADMIN_REVIEW_TEST_WARNING/i.test(visible));
 assert.match(await offline.locator('#row-0').innerText(),/Report comparison/);assert.ok(!(await offline.locator('#row-0').innerText()).includes('No revisions'));
 assert.equal(await offline.locator('#row-0 .revision-review').count(),0);assert.equal(await offline.locator('#row-1 .revision-minor').count(),1);
 await offline.locator('#filter-none').click();assert.equal(await offline.locator('#row-0').count(),0);await offline.locator('#reset-filters').click();
 const updated=await download(offline,'#save-review',path.join(out,'recipient-filters-updated.html'));
 assert.equal(records(updated)[0].revisions[0].importance,'review');assert.equal(records(updated)[1].admin_diagnostics.source_status,'partial');
 await offline.screenshot({path:path.join(out,'recipient-filters.png'),fullPage:true});assert.deepEqual(errors,[]);
 console.log('Passed: wording under More, administrator Needs review retained, no recipient review UI/warnings, no false all-clear, clinical comparisons and embedded diagnostics survive download/re-save.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

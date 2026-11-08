// Filter modifiers on the actual website template and an offline export.
const {chromium}=require('playwright'),assert=require('assert/strict'),path=require('path');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const u=new URL(route.request().url());return u.hostname==='127.0.0.1'||u.protocol==='file:'||u.protocol==='data:'?route.continue():route.abort();});
 async function selected(p,expected){assert.deepEqual(await p.locator('.filter-chip[aria-pressed="true"]').evaluateAll(ns=>ns.map(n=>n.id).sort()),expected.map(k=>'filter-'+k).sort());}
 async function check(p){
  await p.locator('#filter-major').click();await selected(p,['major']);
  await p.locator('#filter-minor').click();await selected(p,['minor']);
  await p.locator('#filter-minor').click();await selected(p,['minor']);
  await p.locator('#filter-major').click({modifiers:['Control']});await selected(p,['minor','major']);
  await p.locator('#filter-favorite').click({modifiers:['Shift']});await selected(p,['minor','major','favorite']);
  await p.locator('#filter-minor').click({modifiers:['Control']});await selected(p,['major','favorite']);
  await p.locator('#filter-favorite').click({modifiers:['Shift']});await selected(p,['major']);
  await p.locator('#more-filters-label').click();await p.locator('#filter-wording').click({modifiers:['Control']});await selected(p,['major','wording']);
  await p.locator('#filter-none').click();await selected(p,['none']);
  await p.locator('#filter-minor').click({modifiers:['Shift']});await selected(p,['none','minor']);
  await p.locator('#filter-all').click({modifiers:['Control']});await selected(p,['all']);
  await p.locator('#filter-major').click();await p.locator('#filter-major').click({modifiers:['Shift']});await selected(p,['all']);
 }
 await page.goto('http://127.0.0.1:8766/qa');await check(page);
 const event=page.waitForEvent('download');await page.locator('#export-review').click();const file=path.join(__dirname,'qa-output/filter-selection.html');await(await event).saveAs(file);
 const offline=await context.newPage();offline.on('pageerror',e=>errors.push(e.message));await offline.goto('file:///'+file.replaceAll('\\','/'));await check(offline);
 assert.deepEqual(errors,[]);console.log('Passed: ordinary clicks replace selection, Ctrl/Shift toggle multiple filters, More filters share behavior, All clears, final modifier removal restores All, same behavior in actual HTML export.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

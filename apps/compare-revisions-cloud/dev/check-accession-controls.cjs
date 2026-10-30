// Synthetic offline reader: the compact header copy control and expanded list.
const {chromium}=require('playwright'),assert=require('assert/strict'),path=require('path');
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const page=await browser.newPage({viewport:{width:1280,height:1600}}),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>{if(new URL(r.request().url()).protocol==='file:')return r.continue();network.push(r.request().url());return r.abort();});
 await page.goto('file:///'+path.join(__dirname,'qa-output','clinical-review.html').replaceAll('\\','/'));
 await page.evaluate(()=>{window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>window.copied.push(value)}});});
 const icon=page.locator('#row-0 .case-copy-accession'),head=page.locator('#case-0');
 assert.equal(await icon.getAttribute('title'),'Copy accession');assert((await icon.getAttribute('aria-label')).includes('Copy accession'));
 const hit=await icon.boundingBox(),caret=await head.locator('.chevron').boundingBox();assert(hit.width>=44&&hit.height>=44);assert(hit.x+hit.width<=caret.x,'copy must be left of the caret');
 assert.equal(await head.locator('button').count(),0,'buttons must not be nested');assert.equal(await page.locator('#row-0 .accession-tools').count(),0);
 const height=(await page.locator('#row-0').boundingBox()).height;await icon.click();assert.equal(await head.getAttribute('aria-expanded'),'false');assert.equal(await icon.locator('svg').count(),1);assert.equal(await icon.locator('.accession-copy-feedback').isVisible(),true);assert(Math.abs((await page.locator('#row-0').boundingBox()).height-height)<1,'copy must not change card height');
 await page.waitForTimeout(1500);assert.equal(await icon.locator('.accession-copy-feedback').isVisible(),false);
 await icon.focus();await page.keyboard.press('Enter');assert.equal(await head.getAttribute('aria-expanded'),'false');
 await page.waitForTimeout(1500);await page.locator('#search').focus();await page.mouse.move(0,0);await page.locator('#row-0').screenshot({path:path.join(__dirname,'qa-output','accession-collapsed.png')});
 await head.click();assert.equal(await page.locator('#row-0 .accession-line').count(),2);assert(await page.locator('#row-0 .case-body').evaluate(body=>body.lastElementChild.classList.contains('accession-tools')),'full list belongs below review panes');
 await page.locator('#row-0 .accession-line').nth(1).getByRole('button',{name:'Copy accession',exact:true}).click();assert.equal(await page.evaluate(()=>window.copied.at(-1)),'CT901269345');
 await page.waitForTimeout(1500);await page.locator('#row-0').screenshot({path:path.join(__dirname,'qa-output','accession-expanded.png')});
 await page.locator('#theme-toggle').click();await page.setViewportSize({width:375,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 const mobile=await icon.boundingBox();assert(mobile.width>=44&&mobile.height>=44);await page.locator('#row-0').screenshot({path:path.join(__dirname,'qa-output','accession-mobile.png')});
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);console.log('Accession controls passed: compact 44px icon, keyboard/caret isolation, stable feedback, full expanded list, offline copy, themes and mobile layout.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1);});

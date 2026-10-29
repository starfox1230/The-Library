const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.join(__dirname,'qa-output');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1100,height:1500}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.setContent(fs.readFileSync(path.join(out,'preview.html'),'utf8'));
 const sampled=await page.evaluate(async()=>{
  const head=document.getElementById('case-5'),reveal=document.getElementById('body-5'),caret=head.querySelector('.chevron');
  head.click();
  const heights=[];for(let n=0;n<24;n++){await new Promise(requestAnimationFrame);heights.push(reveal.getBoundingClientRect().height);}
  return {heights,sameHead:head===document.getElementById('case-5'),sameCaret:caret===head.querySelector('.chevron'),caretText:caret.textContent};
 });
 assert(sampled.sameHead&&sampled.sameCaret);assert.equal(sampled.caretText,'');
 const last=sampled.heights.at(-1);assert(last>100);
 assert(sampled.heights.some(h=>h>0 && h<last-2),'expansion must interpolate, not jump');
 const layout=await page.evaluate(()=>{
  const row=document.getElementById('row-5'),next=document.getElementById('row-6'),body=row.querySelector('.case-body'),tab=row.querySelector('.tabs');
  return {gap:next.getBoundingClientRect().top-row.getBoundingClientRect().bottom,padding:tab.getBoundingClientRect().left-row.getBoundingClientRect().left,color:getComputedStyle(row).backgroundColor,nextColor:getComputedStyle(next).backgroundColor};
 });
 assert(layout.gap>=9);assert(layout.padding>=24);assert.notEqual(layout.color,layout.nextColor);
 await page.locator('#row-5').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(out,'polished-pending-desktop.png')});
 await page.evaluate(()=>{const h=document.getElementById('case-5');h.click();h.click();h.click();});
 await page.waitForFunction(()=>document.getElementById('body-5').getBoundingClientRect().height===0);
 assert.equal(await page.locator('#case-5').getAttribute('aria-expanded'),'false');
 assert(await page.locator('#body-5').evaluate(n=>n.inert));
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.locator('#case-5').click();
 assert.equal(await page.locator('#body-5').evaluate(n=>getComputedStyle(n).transitionDuration),'0s');
 await page.emulateMedia({reducedMotion:'no-preference'});
 // Validate inside the same sandbox wrapper used for inline visualization previews.
 await page.goto('http://127.0.0.1:8773/');
 await page.frameLocator('iframe').locator('#case-5').click();
 let frame=page.frames().find(f=>f!==page.mainFrame()&&f.url().includes('/frame'));
 if(!frame)frame=page.frames().find(f=>f!==page.mainFrame());
 await frame.waitForFunction(()=>document.getElementById('body-5').getBoundingClientRect().height>100);
 for(const width of [1024,736,375,320]){
  await page.setViewportSize({width,height:1500});
  const measurement=await frame.evaluate(()=>{
   const row=document.getElementById('row-5').getBoundingClientRect(),tabs=document.querySelector('#row-5 .tabs').getBoundingClientRect();
   return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,left:tabs.left-row.left,right:row.right-tabs.right};
  });
  assert(!measurement.overflow,JSON.stringify(measurement));
  assert(measurement.left>=17&&measurement.right>=17,'consistent inline padding '+JSON.stringify(measurement));
 }
 await page.setViewportSize({width:1100,height:1800});
 await page.screenshot({path:path.join(out,'polished-inline-light.png'),fullPage:true});
 await page.emulateMedia({colorScheme:'dark'});
 await page.reload();
 await page.frameLocator('iframe').locator('#case-5').click();
 await page.frameLocator('iframe').locator('#row-5').evaluate(async n=>{await Promise.all(n.getAnimations({subtree:true}).map(a=>a.finished));});
 await page.screenshot({path:path.join(out,'polished-inline-dark.png'),fullPage:true});
 await page.frameLocator('iframe').locator('#case-5').click();
 if(await page.frameLocator('iframe').locator('#case-0').getAttribute('aria-expanded')!=='true')await page.frameLocator('iframe').locator('#case-0').click();
 await page.frameLocator('iframe').locator('#row-0').evaluate(async n=>{await Promise.all(n.getAnimations({subtree:true}).map(a=>a.finished));});
 await page.screenshot({path:path.join(out,'polished-complex-dark.png')});
 await page.frameLocator('iframe').locator('#combined-view').check();
 await page.waitForTimeout(350);
 const columns=await page.frameLocator('iframe').locator('#row-0 .review-pane').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right};}));
 assert.equal(columns[0].top,columns[1].top);assert.equal(columns[0].bottom,columns[1].bottom);assert(columns[1].left>=columns[0].right);
 await page.frameLocator('iframe').locator('#revision-0-0').hover();await page.waitForTimeout(220);
 assert(await page.frameLocator('iframe').locator('#row-0 .is-linked').count()>0,'passage links work inside the actual conversation sandbox');
 await page.frameLocator('iframe').locator('#revision-0-0').click();await page.mouse.move(1090,10);await page.waitForTimeout(220);
 assert.equal(await page.frameLocator('iframe').locator('#revision-0-0').getAttribute('aria-pressed'),'true');
 await page.screenshot({path:path.join(out,'paired-inline-dark.png')});
 for(const width of [736,375,320]){
  await page.setViewportSize({width,height:1500});
  assert(await page.frameLocator('iframe').locator('html').evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'inline paired overflow '+width);
 }
 await page.frameLocator('iframe').locator('#input-disclosure > summary').click();
 await page.frameLocator('iframe').locator('.customize > summary').click();
 assert((await page.frameLocator('iframe').locator('#custom-prompt').inputValue()).includes('CALIBRATION'));
 await page.frameLocator('iframe').locator('#custom-prompt').fill('A different prompt.');
 await page.frameLocator('iframe').locator('#restore-prompt').click();
 assert((await page.frameLocator('iframe').locator('#custom-prompt').inputValue()).includes('CALIBRATION'));
 assert.deepEqual(errors,[]);
 console.log('Polish checks passed: animations, case boundaries, inline paired layout/mobile stacking, and full instruction editor/reset.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

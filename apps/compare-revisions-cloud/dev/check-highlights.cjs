// Synthetic browser verification: no provider calls or patient reports.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const dir=path.join(__dirname,'qa-output');
const html=fs.readFileSync(path.join(dir,'preview.html'),'utf8');
const fixtures=JSON.parse(fs.readFileSync(path.join(dir,'fixtures.json'),'utf8'));
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1600,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.abort());await page.setContent(html);
 await page.locator('#combined-view').check();await page.locator('#case-0').click();
 await page.waitForTimeout(350);
 await page.locator('#row-0').scrollIntoViewIfNeeded();
 const card=page.locator('#row-0 .revision').first();
 await card.hover();await page.waitForTimeout(200);
 assert(await card.evaluate(n=>n.classList.contains('is-highlighted')));
 assert(await page.locator('#row-0 .is-linked').count()>0);
 assert.equal(await page.locator('#row-0 .section-heading.is-linked').count(),0,'heading text never becomes evidence for a finding');
 assert.deepEqual(await page.locator('#row-0 .section-heading').allTextContents(),['FINDINGS:','IMPRESSION:'],'paired clinical report retains headers');
 assert.match(await page.locator('#link-status-0').innerText(),/Attending Impression/);
 await page.locator('#revision-0-0').click();await page.mouse.move(1590,10);await page.waitForTimeout(250);
 assert.equal(await page.locator('#revision-0-0').getAttribute('aria-pressed'),'true');
 assert(await page.locator('#row-0 .is-linked').count()>0,'pin survives leaving the card');
 const count=await page.locator('#link-count-0').innerText();assert.match(count,/1 of [234] passages/);
 await page.locator('#link-next-0').click();assert.match(await page.locator('#link-count-0').innerText(),/2 of/);
 await page.locator('#link-clear-0').click();await page.mouse.move(1590,10);await page.waitForTimeout(250);
 assert.equal(await page.locator('#row-0 .is-linked').count(),0);
 // Split view must retain every source character and map only that source's evidence.
 await page.locator('#diff-mode-0').selectOption('split');
 const diffs=page.locator('#row-0 .report-grid .diff');
 assert.equal(await diffs.first().textContent(),fixtures[0].clinical_diff.filter(t=>t.kind!=='insert').map(t=>t.text).join(''));
 assert.equal(await diffs.last().textContent(),fixtures[0].clinical_diff.filter(t=>t.kind!=='delete').map(t=>t.text).join(''));
 const addedIndex=fixtures[0].revisions.findIndex(r=>r.action==='added'&&r.resident_quote==='');
 assert(addedIndex>=0);
 await page.locator('#revision-0-'+addedIndex).focus();await page.waitForTimeout(120);
 assert.equal(await diffs.first().locator('.is-linked').count(),0,'attending-only evidence never marks resident column');
 assert(await diffs.last().locator('.is-linked').count()>0);
 await page.keyboard.press('Enter');await page.mouse.move(1590,10);await page.waitForTimeout(230);
 assert.equal(await page.locator('#revision-0-'+addedIndex).getAttribute('aria-pressed'),'true','keyboard pins the link');
 await page.locator('#evidence-0').click();assert.equal(await page.locator('#revision-0-'+addedIndex).getAttribute('aria-pressed'),'true');
 await page.locator('#evidence-0').click();
 await page.locator('#diff-mode-0').selectOption('inline');
 // With a long expanded summary, the report stays visible and has its own scroll.
 await page.evaluate(()=>{const row=document.getElementById('row-0');scrollTo(0,row.getBoundingClientRect().top+scrollY+600);});
 await page.waitForTimeout(400);
 const layout=await page.locator('#row-0').evaluate(row=>{
  const dock=row.querySelector('.report-dock'),viewer=row.querySelector('.diff-scroll'),panes=[...row.querySelectorAll('.review-pane')].map(n=>{const r=n.getBoundingClientRect();return {top:r.top,bottom:r.bottom};});
  return {dockTop:dock.getBoundingClientRect().top,dockBottom:dock.getBoundingClientRect().bottom,viewerHeight:viewer.clientHeight,viewerFull:viewer.scrollHeight,panes};
 });
 assert(layout.dockTop>=19&&layout.dockTop<=22,JSON.stringify(layout));
 assert(layout.dockBottom<=881,JSON.stringify(layout));
 assert(layout.viewerFull>layout.viewerHeight+200,JSON.stringify(layout));
 assert.equal(layout.panes[0].top,layout.panes[1].top);assert.equal(layout.panes[0].bottom,layout.panes[1].bottom);
 const lowerIndex=fixtures[0].revisions.findIndex(r=>r.summary.includes('degeneration'));
 assert(lowerIndex>=0);
 // Keep a stationary pointer from selecting another card while focus scrolls
 // its report. This check is for keyboard navigation, not concurrent hovering.
 await page.mouse.move(1590,10);await page.waitForTimeout(250);
 // At 900px this fixture's lower Findings passage can already be visible;
 // use a shorter desktop viewport so the navigation target is offscreen.
 await page.setViewportSize({width:1600,height:600});
 // Prior hover/pin checks can leave a smooth scroll in flight. Isolate the
 // location check from that animation and start at a known report position.
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.locator('#diff-scroll-0').evaluate(n=>n.scrollTo({top:0,behavior:'instant'}));
 const before=await page.evaluate(()=>scrollY);
 // Call the same native focus handler without Playwright's page-scroll helpers.
 await page.locator('#revision-0-'+lowerIndex).evaluate(n=>n.focus({preventScroll:true}));
 await page.waitForTimeout(600);
 assert.equal(await page.evaluate(()=>scrollY),before,'locating a passage must not move the page');
 assert(await page.locator('#diff-scroll-0').evaluate(n=>n.scrollTop)>0,'offscreen lower passage scrolls inside the report');
 const targetVisible=await page.locator('#diff-scroll-0').evaluate(viewer=>{
  const v=viewer.getBoundingClientRect();return [...viewer.querySelectorAll('.is-linked')].some(n=>{const r=n.getBoundingClientRect();return r.top>=Math.max(v.top,20)&&r.bottom<=Math.min(v.bottom,innerHeight-20);});
 });assert(targetVisible,'the linked passage is on screen');
 await page.screenshot({path:path.join(dir,'linked-sticky-light.png')});
 await page.emulateMedia({colorScheme:'dark'});await page.waitForTimeout(300);await page.screenshot({path:path.join(dir,'linked-sticky-dark.png')});
 // Pin remains marked on collapse/reopen, rather than losing the source context.
 await page.locator('#revision-0-'+lowerIndex).evaluate(n=>n.click());
 await page.locator('#case-0').evaluate(n=>n.click());await page.waitForTimeout(350);
 await page.locator('#case-0').evaluate(n=>n.click());await page.waitForTimeout(350);
 assert.equal(await page.locator('#revision-0-'+lowerIndex).getAttribute('aria-pressed'),'true');
 assert(await page.locator('#row-0 .is-linked').count()>0);
 for(const width of [1024,736,375,320]){
  await page.setViewportSize({width,height:900});await page.waitForTimeout(350);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no overflow at '+width);
  if(width<981){assert.equal(await page.locator('.report-dock').first().evaluate(n=>getComputedStyle(n).position),'static');assert.equal(await page.locator('.diff-scroll').first().evaluate(n=>getComputedStyle(n).overflowY),'visible');}
 }
 await page.locator('#row-0').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(dir,'linked-mobile.png')});
 // Exact repeated findings are all linked, but same words in Impression stay unmarked.
 const repeated=JSON.parse(fs.readFileSync(path.join(dir,'link-fixture.json'),'utf8'));
 const repeatHtml=html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_m,a,b)=>a+JSON.stringify(repeated)+b);
 await page.setViewportSize({width:1600,height:900});await page.emulateMedia({colorScheme:'light',reducedMotion:'reduce'});
 await page.setContent(repeatHtml);await page.locator('#combined-view').check();await page.locator('#case-0').click();
 await page.locator('#revision-0-0').click();await page.mouse.move(1590,10);await page.waitForTimeout(240);
 assert.equal(await page.locator('#link-count-0').innerText(),'1 of 4 passages','overlapping broader evidence must not add unrelated navigation targets');
 const matched=await page.locator('#row-0 .is-linked').allTextContents();
 assert.equal(matched.join(''),'SmallModerate effusion.SmallModerate effusion.');
 assert.match(await page.locator('#link-status-0').innerText(),/^Resident Findings · Attending Findings/);
 for(const count of [2,3,4,1]){await page.locator('#link-next-0').click();assert.equal(await page.locator('#link-count-0').innerText(),count+' of 4 passages');}
 await page.locator('#revision-0-2').click();await page.mouse.move(1590,10);await page.waitForTimeout(240);
 assert.equal(await page.locator('#row-0 .is-linked').allTextContents().then(x=>x.join('')),'SmallModerate effusion.');
 assert.match(await page.locator('#link-status-0').innerText(),/Resident Impression · Attending Impression/);
 await page.locator('#diff-mode-0').selectOption('split');
 assert.equal(await page.locator('#row-0 .report-grid .diff').first().textContent(),repeated[0].clinical_diff.filter(t=>t.kind!=='insert').map(t=>t.text).join(''));
 assert.equal(await page.locator('#row-0 .report-grid .diff').last().textContent(),repeated[0].clinical_diff.filter(t=>t.kind!=='delete').map(t=>t.text).join(''));
 assert.deepEqual(errors,[]);await browser.close();console.log('Passage linking, repeated/overlapping evidence, keyboard pinning, source fidelity, sticky scrolling and responsive checks passed.');
})().catch(e=>{console.error(e);process.exit(1);});

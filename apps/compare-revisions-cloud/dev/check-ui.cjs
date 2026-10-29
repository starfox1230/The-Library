// Offline browser checks against the real rendered template and mocked /analyze.
const {chromium}=require('playwright');
const fs=require('fs'), path=require('path'), assert=require('assert/strict');
const dir=path.join(__dirname,'qa-output');
const html=fs.readFileSync(path.join(dir,'preview.html'),'utf8');
const fixtures=JSON.parse(fs.readFileSync(path.join(dir,'fixtures.json'),'utf8'));
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1280,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let external=0;
 await page.route('**/*',route=>{external++;return route.abort();});
 await page.setContent(html);
 assert.equal(await page.locator('.case').count(),8);
 assert.equal(await page.locator('.case-head').first().getAttribute('aria-expanded'),'false');
 assert.match(await page.locator('.case-head').first().innerText(),/2 major/);
 assert.match(await page.locator('.case-head').first().innerText(),/4 minor/);
 assert.match(await page.locator('.case-head').first().innerText(),/5 wording/);
 assert.match(await page.locator('.case-head').first().innerText(),/\+9 more/);
 const totals=Object.fromEntries(['major','minor','wording','review'].map(group=>[group,fixtures.reduce((sum,c)=>sum+c.revisions.filter(r=>r.importance===group).length,0)]));
 for(const [group,total] of Object.entries(totals))if(group!=='review')assert.match(await page.locator('#revision-totals .'+group).innerText(),new RegExp('^'+total+' '),'totals count revisions across all numbered cases');
 assert.equal(await page.locator('#filter-review').innerText(),'Needs review (1)','review includes failed analyses without revision items');
 const initialTotals=await page.locator('#revision-totals').innerText();
 for(const group of ['major','wording']){
  const previews=page.locator('.preview-item.'+group);assert(await previews.count()>0);
  assert.equal(await previews.first().locator('.resident-summary').evaluate(n=>getComputedStyle(n).color),await page.locator('.case-title').first().evaluate(n=>getComputedStyle(n).color),'resident preview uses reading color regardless of '+group);
  assert.equal(await previews.first().locator('.attending-summary').evaluate(n=>getComputedStyle(n).color),await page.locator('#filter-minor').evaluate(n=>getComputedStyle(n).color),'attending preview always uses amber');
 }
 const minorPage=await browser.newPage({viewport:{width:1280,height:1000}});
 const minorFixture={...fixtures[0],revisions:fixtures[0].revisions.filter(r=>r.importance==='minor')};
 await minorPage.setContent(html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_m,a,b)=>a+JSON.stringify([minorFixture])+b));
 for(const colorScheme of ['light','dark']){
  await minorPage.emulateMedia({colorScheme});
  assert.equal(await minorPage.locator('.preview-item.minor .resident-summary').first().evaluate(n=>getComputedStyle(n).color),await minorPage.locator('.case-title').first().evaluate(n=>getComputedStyle(n).color),'resident uses reading color in '+colorScheme);
  assert.equal(await minorPage.locator('.preview-item.minor .attending-summary').first().evaluate(n=>getComputedStyle(n).color),await minorPage.locator('#filter-minor').evaluate(n=>getComputedStyle(n).color),'attending uses amber in '+colorScheme);
 }
 await minorPage.close();
 assert.match(await page.locator('#progress-count').innerText(),/7 of 7 report pairs · 100%/);
 assert.match(await page.locator('#progress-note').innerText(),/1 analysis needs attention/);
 assert.match(await page.locator('#progress-note').innerText(),/1 report pair was not submitted/);
 await page.locator('#case-0').click();
 assert(await page.locator('#combined-view').isChecked(),'paired view is the initial preference');
 assert.equal(await page.locator('#tab-0-paired').getAttribute('aria-selected'),'true');
 assert.equal(await page.locator('#row-0 .review-pane').count(),2,'opened cases initially show both panels');
 await page.locator('#combined-view').uncheck();
 assert.equal(await page.locator('#tab-0-summary').getAttribute('aria-selected'),'true');
 assert.equal(await page.locator('.group-major .revision').count(),2);
 assert.equal(await page.locator('.group-minor .revision').count(),4);
 const revisionColors=await page.evaluate(()=>({major:getComputedStyle(document.querySelector('.revision-major')).backgroundColor,minor:getComputedStyle(document.querySelector('.revision-minor')).backgroundColor}));
 assert.notEqual(revisionColors.major,revisionColors.minor);
 assert.equal(await page.getByRole('button',{name:/Show remaining|Show fewer/}).count(),0);
 assert.equal(await page.locator('.revision').count(),11);
 await page.locator('#tab-0-reports').click();
 assert.equal(await page.locator('.report-text').first().innerText(),fixtures[0].resident_report);
 await page.locator('#tab-0-diff').click();
 assert.deepEqual(await page.locator('#row-0 .section-heading').allTextContents(),['FINDINGS:','IMPRESSION:'],'inline clinical comparison retains section headings');
 assert.equal(await page.locator('#row-0 .section-heading').first().evaluate(n=>getComputedStyle(n).fontWeight),'650');
 await page.locator('#diff-mode-0').selectOption('split');
 for(const column of [page.locator('#row-0 .report-grid .diff').first(),page.locator('#row-0 .report-grid .diff').last()])assert.deepEqual(await column.locator('.section-heading').allTextContents(),['FINDINGS:','IMPRESSION:']);
 const r=await page.locator('.report-grid .diff').first().textContent();
 const a=await page.locator('.report-grid .diff').last().textContent();
 assert.equal(r,fixtures[0].clinical_diff.filter(t=>t.kind!=='insert').map(t=>t.text).join(''));
 assert.equal(a,fixtures[0].clinical_diff.filter(t=>t.kind!=='delete').map(t=>t.text).join(''));
 await page.locator('#tab-0-summary').click();
 await page.screenshot({path:path.join(dir,'desktop-expanded.png'),fullPage:true});
 // Full instructions, replacement editor, and global paired layout.
 const defaultPrompt=await page.locator('#default-prompt').textContent().then(JSON.parse);
 assert.equal(await page.locator('#custom-prompt').inputValue(),defaultPrompt);
 await page.setViewportSize({width:1600,height:1000});
 const narrowWidth=await page.locator('main').evaluate(n=>n.getBoundingClientRect().width);
 await page.locator('#case-1').click();
 await page.locator('#combined-view').check();
 await page.waitForTimeout(350);
 assert.equal(await page.locator('.paired-review').count(),2,'global preference applies to every open case');
 assert.equal(await page.locator('#combined-view-value').inputValue(),'1');
 assert(await page.locator('main').evaluate(n=>n.getBoundingClientRect().width)>narrowWidth,'paired view widens the page');
 for(const key of ['0','1']){
  const panes=await page.locator('#row-'+key+' .review-pane').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right};}));
  assert.equal(panes[0].top,panes[1].top);assert.equal(panes[0].bottom,panes[1].bottom);
  assert(panes[1].left>=panes[0].right,'summary is left; text changes is right');
  assert.equal(await page.locator('#row-'+key+' .review-pane').last().evaluate(n=>getComputedStyle(n).borderLeftWidth),'1px');
 }
 await page.locator('#diff-mode-0').selectOption('inline');
 await page.screenshot({path:path.join(dir,'paired-desktop.png')});
 await page.locator('#tab-1-reports').click();
 assert.equal(await page.locator('#row-1 .report-text').count(),2,'full reports still accessible');
 await page.locator('#tab-1-paired').click();
 await page.emulateMedia({colorScheme:'dark'});
 await page.waitForTimeout(300);
 await page.evaluate(()=>scrollTo(0,0));
 await page.screenshot({path:path.join(dir,'paired-dark.png')});
 await page.emulateMedia({colorScheme:'light'});
 await page.waitForTimeout(300);
 for(const width of [1024,736,375,320]){
  await page.setViewportSize({width,height:1000});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`paired overflow ${width}`);
  const panes=await page.locator('#row-1 .review-pane').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left};}));
  if(width<=980){assert.equal(panes[0].left,panes[1].left);assert(panes[1].top>=panes[0].bottom,'panes stack on small screens');}
  else assert.equal(panes[0].bottom,panes[1].bottom);
  if(width===375)await page.screenshot({path:path.join(dir,'paired-mobile.png')});
 }
 await page.setViewportSize({width:1280,height:1000});
 await page.locator('#combined-view').uncheck();
 await page.locator('#input-disclosure > summary').click();
 await page.locator('.customize > summary').click();
 await page.locator('#custom-prompt').fill('Replacement instructions for this experiment.');
 await page.locator('#restore-prompt').click();
 assert.equal(await page.locator('#custom-prompt').inputValue(),defaultPrompt);
 await page.locator('#input-disclosure > summary').click();
 await page.locator('#collapse').click();
 await page.locator('#order').selectOption('newest');
 assert.match(await page.locator('.case-number').first().innerText(),/21/);
 await page.locator('#order').selectOption('oldest');
 assert.match(await page.locator('.case-number').first().innerText(),/12/);
 await page.locator('#filter-major').click();
 assert.equal(await page.locator('.case').count(),2);
 assert.equal(await page.locator('#revision-totals').innerText(),initialTotals,'filters must not silently redefine the overall totals');
 await page.locator('#filter-all').click();
 await page.locator('#filter-none').click();
 assert.equal(await page.locator('.case').count(),2);
 await page.locator('#filter-all').click();
 await page.locator('#search').fill('16');
 assert.equal(await page.locator('.case').count(),1);
 assert.equal(await page.locator('#revision-totals').innerText(),initialTotals,'search leaves overall totals stable');
 assert.match(await page.locator('.case-number').innerText(),/16/);
 await page.locator('#search').fill('');
 for(const width of [1024,736,375,320]){
  await page.setViewportSize({width,height:1000});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width}`);
  await page.locator('#case-0').click();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`expanded overflow ${width}`);
  if(width===375)await page.screenshot({path:path.join(dir,'mobile-expanded.png'),fullPage:true});
  await page.locator('#case-0').click();
 }
 await page.emulateMedia({colorScheme:'dark'});
 await page.setViewportSize({width:1280,height:1000});
 await page.waitForTimeout(350);
 for(const group of ['major','wording'])assert.equal(await page.locator('.preview-item.'+group+' .resident-summary').first().evaluate(n=>getComputedStyle(n).color),await page.locator('.case-title').first().evaluate(n=>getComputedStyle(n).color),'dark resident text uses reading color for '+group);
 await page.screenshot({path:path.join(dir,'dark-collapsed.png'),fullPage:true});
 assert.equal(external,0,'synthetic preview must have no external requests');
 await page.locator('#input-disclosure > summary').click();
 await page.locator('#clear-button').click();
 assert.equal(await page.locator('.case').count(),0);
 assert.equal(await page.locator('#review-data').count(),0);
 assert(await page.locator('#analysis-progress').isHidden());
 assert.equal(await page.locator('#report-text').inputValue(),'');
 assert.equal(await page.locator('#custom-prompt').inputValue(),defaultPrompt,'clear restores defaults rather than leaving an empty required prompt');
 assert(!html.includes('localStorage') && !html.includes('sessionStorage'));
 assert.equal(await page.evaluate(()=>getComputedStyle(document.body).backgroundColor),await page.locator('#cr-app').evaluate(n=>getComputedStyle(n).backgroundColor),'empty page must keep the app background');

 // Live incremental request behavior is exercised in check-batching.cjs.
 assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(dir,'browser-results.json'),JSON.stringify({passed:true,checks:['compact counts','all 11 revisions reachable','summary default','full report fidelity','split diff losslessness','filters','both sort directions','source IDs','320-1600px layout','dark mode','zero preview requests','clear','full prompt editor/reset','equal-height paired panels','mobile stacking']},null,2));
 await browser.close();console.log('UI browser checks passed.');
})().catch(e=>{console.error(e);process.exit(1);});

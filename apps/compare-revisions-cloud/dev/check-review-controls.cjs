// Offline checks for directional summaries, complete groups, filters and text-change sorting.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.join(__dirname,'qa-output');
const html=fs.readFileSync(path.join(out,'preview.html'),'utf8');
const fixtures=JSON.parse(fs.readFileSync(path.join(out,'fixtures.json'),'utf8'));
const withCases=cases=>html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_m,a,b)=>a+JSON.stringify(cases).replace(/</g,'\\u003c')+b);
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try {
  const page=await browser.newPage({viewport:{width:1280,height:1000}});
  const errors=[];let requests=0;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>{requests++;return r.abort();});
  // Match the user's example without storing or using any real report.
  const sample=structuredClone(fixtures);
  sample[0].revisions[0].resident_summary='Pelvic mass with uncertain origin';
  sample[0].revisions[0].attending_summary='Uterine origin favored';
  sample[0].revisions[0].summary='Legacy text must never control the displayed endpoints';
  sample[0].revisions[1].resident_summary='<img src=x onerror="window.injected=1">';
  sample[0].revisions[1].attending_summary='Revised interpretation';
  await page.setContent(withCases(sample));
  assert.equal(await page.getByText('Filter cases',{exact:true}).count(),0);
  assert.equal(await page.locator('#filter-help').count(),0);
  assert.equal(await page.locator('#row-1 .preview-item').first().textContent(),'Small right pneumothorax → Added to Impression; finding unchanged','Impression inclusion states the edit explicitly');
  assert.equal(await page.locator('#filter-all').getAttribute('aria-pressed'),'true');
  assert.equal(await page.locator('#filter').count(),0,'filters are visible, not hidden in a dropdown');
  await page.locator('#search').fill('no matching search');
  await page.locator('#progress-issues').click();
  assert.equal(await page.locator('.case').count(),1,'analysis attention links to its exact affected subset');
  assert.equal(await page.locator('#case-7').getAttribute('aria-expanded'),'true');
  assert.match(await page.locator('#row-7 .case-next-step').textContent(),/Retry/);
  assert.equal(await page.locator('#search').inputValue(),'','status navigation clears an unrelated search');
  await page.locator('#progress-skipped').click();
  assert.equal(await page.locator('.case').count(),1);
  assert.equal(await page.locator('#case-5').getAttribute('aria-expanded'),'true');
  assert.match(await page.locator('#row-5 .case-next-step').textContent(),/Recapture/);
  await page.locator('#reset-filters').click();
  await page.locator('#collapse').click();
  for(const colorScheme of ['dark','light']){
   await page.emulateMedia({colorScheme});
   const resident=page.locator('#row-0 .change-preview .resident-summary').first();
   const attending=page.locator('#row-0 .change-preview .attending-summary').first();
   assert.equal(await resident.textContent(),'Pelvic mass with uncertain origin');
   assert.equal(await attending.textContent(),' → Uterine origin favored');
   assert.equal(await resident.evaluate(n=>getComputedStyle(n).color),await page.locator('.case-title').first().evaluate(n=>getComputedStyle(n).color));
   assert.equal(await attending.evaluate(n=>getComputedStyle(n).color),await page.locator('#filter-minor').evaluate(n=>getComputedStyle(n).color));
   assert.notEqual(await resident.evaluate(n=>getComputedStyle(n).color),await attending.evaluate(n=>getComputedStyle(n).color));
  }
  assert.equal(await page.locator('.change-preview img').count(),0);
  await page.locator('#case-0').click();
  await page.locator('#case-1').click();
  await page.locator('#evidence-0').click();
  assert.equal(await page.locator('#evidence-0').textContent(),'Show report wording');
  assert.equal(await page.locator('#row-0 .evidence:not([hidden])').count(),0);
  assert.equal(await page.locator('#evidence-1').textContent(),'Hide report wording','a local toggle leaves other cases unchanged');
  assert.equal(await page.locator('#report-wording-value').inputValue(),'1');
  await page.locator('#case-2').click();
  assert(await page.locator('#row-2 .evidence:not([hidden])').count()>0,'newly opened cases retain the default');
  await page.locator('#combined-view').uncheck();
  await page.locator('#order').selectOption('change-high');
  await page.locator('#filter-major').click();await page.locator('#filter-all').click();
  assert.equal(await page.locator('#row-0 .evidence:not([hidden])').count(),0,'local preference survives view, sorting and filtering');
  await page.locator('#evidence-0').click();
  assert.equal(await page.locator('#case-list .evidence[hidden]').count(),0);
  assert.equal(await page.locator('#report-wording-value').inputValue(),'1');
  await page.locator('#case-1').click();await page.locator('#case-2').click();
  await page.locator('#combined-view').check();await page.locator('#order').selectOption('oldest');
  assert.equal(await page.locator('#row-0 .group-minor .revision').count(),4);
  assert.equal(await page.locator('#row-0 .group-wording .revision').count(),5);
  for(const item of sample[0].revisions){
   const index=sample[0].revisions.indexOf(item),heading=page.locator('#revision-0-'+index);
   assert.equal(await heading.textContent(),item.resident_summary+' → '+item.attending_summary,'every action and importance uses fixed endpoints');
   assert.equal(await heading.locator('.resident-summary').count(),1);
   assert.equal(await heading.locator('.attending-summary').count(),1);
  }
  assert.equal(await page.getByRole('button',{name:/Show remaining|Show fewer/}).count(),0);
  assert.equal(await page.locator('#revision-0-0 .resident-summary').textContent(),'Pelvic mass with uncertain origin');
  assert.equal(await page.locator('#revision-0-0').textContent(),'Pelvic mass with uncertain origin → Uterine origin favored');
  await page.locator('#combined-view').uncheck();
  assert.equal(await page.locator('#row-0 h4 .attending-summary').first().textContent(),' → Uterine origin favored');
  await page.locator('#combined-view').check();
  const totals=await page.locator('#revision-totals').innerText();
  await page.locator('#filter-major').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('.case').count(),2);
  assert.equal(await page.evaluate(()=>document.activeElement.id),'filter-major');
  await page.locator('#filter-wording').click();
  assert.equal(await page.locator('.case').count(),4,'multiple categories include either, without duplicate cases');
  assert.equal(await page.locator('#filter-major').getAttribute('aria-pressed'),'true');
  assert.equal(await page.locator('#filter-wording').getAttribute('aria-pressed'),'true');
  await page.locator('#search').fill('13');
  assert.equal(await page.locator('.case').count(),1,'search narrows the category union');
  await page.locator('#reset-filters').click();
  assert.equal(await page.locator('#search').inputValue(),'');
  assert.equal(await page.locator('.case').count(),fixtures.length);
  assert.equal(await page.locator('#revision-totals').innerText(),totals,'counts stay stable under filtering');
  await page.locator('#filter-review').click();
  assert.equal(await page.locator('.case').count(),1,'analysis errors are discoverable even with zero review revisions');
  await page.locator('#filter-review').click();
  assert.equal(await page.locator('#filter-all').getAttribute('aria-pressed'),'true','deselecting last filter restores all');
  await page.locator('#filter-pending').click();assert.equal(await page.locator('.case').count(),2);
  await page.locator('#filter-all').click();
  await page.locator('#filter-none').click();assert.equal(await page.locator('.case').count(),2);
  await page.locator('#filter-all').click();
  for(const direction of ['high','low']){
   await page.locator('#order').selectOption('change-'+direction);
   const keys=await page.locator('.case').evaluateAll(nodes=>nodes.map(n=>Number(n.id.slice(4))));
   const valid=keys.filter(i=>sample[i].text_change_percent!==null);
   const unavailable=keys.filter(i=>sample[i].text_change_percent===null);
   const expected=sample.map((c,i)=>({c,i})).filter(({c})=>c.text_change_percent!==null).sort((a,b)=>(direction==='high'?b.c.text_change_percent-a.c.text_change_percent:a.c.text_change_percent-b.c.text_change_percent)||a.c.source_numbers[0]-b.c.source_numbers[0]).map(({i})=>i);
   assert.deepEqual(valid,expected);
   assert.deepEqual(keys,[...valid,...unavailable],'unavailable percentages sort last in either direction');
  }
  assert.equal(await page.locator('#row-4 .text-change').textContent(),'0.0% changed');
  assert.equal(await page.locator('#row-5 .text-change').textContent(),'Text change —');
  await page.locator('#order').selectOption('oldest');
  for(const width of [320,375,740,1024,1280]){
   await page.setViewportSize({width,height:1000});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'responsive controls at '+width);
   for(const selector of ['#filter-major','#filter-all','#order','#row-0 .text-change']){
    const bounds=await page.locator(selector).boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=width,selector+' fits at '+width);
   }
  }
  await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'review-controls-dark.png')});
  await page.setViewportSize({width:375,height:1000});await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:path.join(out,'review-controls-mobile.png')});
  await page.locator('#evidence-0').click();
  await page.locator('#clear-button').evaluate(n=>n.click());
  assert.equal(await page.locator('#report-wording-value').inputValue(),'1','a local toggle never changes the default for new batches');
  await page.setContent(withCases([sample[5]]));
  assert(await page.locator('#analysis-progress').isVisible(),'skipped-only batches retain their actionable notice');
  await page.locator('#progress-skipped').click();
  assert.equal(await page.locator('.case').count(),1);
  assert.match(await page.locator('.case-next-step').textContent(),/Recapture/);
  const uncertain={...sample[0],status:'complete',analysis_warnings:[],revisions:[{...sample[0].revisions[0],importance:'review'}]};
  await page.setContent(withCases([uncertain]));
  assert.equal(await page.locator('#progress-issues').count(),0,'clinical uncertainty is not an analysis failure');
  assert.equal(await page.locator('#filter-review').textContent(),'Needs review (1)');
  assert.equal(requests,0);assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'review-controls-results.json'),JSON.stringify({passed:true,checks:['resident/attending colors in both themes and views','all minor/wording visible','safe prose','multi-select union + search','keyboard and focus','stable totals','status filters','both percentage directions + missing values','320–1440px layout','no model requests']},null,2));
  console.log('Review controls browser checks passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

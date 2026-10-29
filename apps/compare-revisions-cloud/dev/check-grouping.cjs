// Production template + Python-imported synthetic groups. No provider calls.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.join(__dirname,'qa-output');
const results=JSON.parse(fs.readFileSync(path.join(out,'grouping-fixtures.json'),'utf8'));
const queued=results.map(c=>({...c,status:'queued',status_message:'Waiting to analyze',revisions:[],analysis_warnings:[]}));
const html=fs.readFileSync(path.join(out,'grouping-preview.html'),'utf8')
 .replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_m,a,b)=>a+JSON.stringify(queued)+b)
 .replace('const syntheticPreview=true;','const syntheticPreview=false;');
const labels=['Cases68–69','Case70','Cases71, 74','Case78'];
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try {
  const page=await browser.newPage({viewport:{width:1280,height:950}});
  const errors=[],batches=[],retries=[],unexpected=[];
  page.on('pageerror',e=>errors.push(e.message));
  // Deliberately wrong returned identity must never replace original membership.
  const responseFor=(id,retried=false)=>({...results.find(c=>c.id===id),source_numbers:[999],case_label:'999',resident_report:'Wrong source',attending_report:'Wrong source',
   ...(id===results[0].id&&!retried?{status:'partial',analysis_warnings:['Synthetic incomplete inventory.']}:{})});
  await page.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.origin!=='https://synthetic.invalid'){unexpected.push(url.href);return route.abort();}
   if(url.pathname==='/')return route.fulfill({contentType:'text/html',body:html});
   if(url.pathname==='/favicon.ico')return route.fulfill({status:204});
   const payload=route.request().postDataJSON();
   if(url.pathname==='/analyze-batch'){
    batches.push(payload);
    const events=[{type:'started',total:payload.cases.length},...payload.cases.map(c=>({type:'case',id:c.id,result:responseFor(c.id)})),{type:'done',total:payload.cases.length}];
    return route.fulfill({contentType:'application/x-ndjson',body:events.map(e=>JSON.stringify(e)).join('\n')+'\n'});
   }
   if(url.pathname==='/analyze'){retries.push(payload);return route.fulfill({contentType:'application/json',body:JSON.stringify(responseFor(payload.id,true))});}
   unexpected.push(url.href);return route.abort();
  });
  await page.goto('https://synthetic.invalid/');
  await page.waitForFunction(()=>document.getElementById('progress-track').getAttribute('aria-valuenow')==='100');
  assert.equal(batches.length,1);assert.equal(batches[0].cases.length,4,'six source rows must schedule four review pairs');
  assert.deepEqual(batches[0].cases.map(c=>c.id),results.map(c=>c.id));
  assert.equal(await page.locator('#totals').textContent(),'6 source cases · 4 review entries');
  assert.deepEqual(await page.locator('.case-number').allTextContents(),labels);
  assert.equal(await page.locator('#filter-minor').textContent(),'1 minor','one grouped revision must not be multiplied by its two source rows');
  await page.locator('#case-0').click();
  assert.match(await page.locator('#row-0 .member-note').textContent(),/Source cases 68, 69.*identical full report pairs.*one analysis/);
  assert.match(await page.locator('#row-0 .member-note').getAttribute('title'),/within 3 original case numbers/);
  await page.locator('#row-0').getByRole('tab',{name:'Full reports',exact:true}).click();
  assert.deepEqual(await page.locator('#row-0 pre.report-text').allTextContents(),[results[0].resident_report,results[0].attending_report]);
  await page.locator('#search').fill('74');
  assert.equal(await page.locator('.case').count(),1);
  assert.equal(await page.locator('.case-number').textContent(),'Cases71, 74');
  assert.equal(await page.locator('#totals').textContent(),'6 source cases · 4 review entries');
  await page.locator('#search').fill('');
  await page.locator('#order').selectOption('newest');
  assert.deepEqual(await page.locator('.case-number').allTextContents(),[...labels].reverse());
  await page.locator('#order').selectOption('oldest');
  await page.locator('#filter-minor').click();
  assert.equal(await page.locator('.case-number').textContent(),'Cases68–69');
  await page.locator('#filter-all').click();
  if(await page.locator('#case-0').getAttribute('aria-expanded')==='false')await page.locator('#case-0').click();
  await page.locator('#row-0').getByRole('tab',{name:'Summary + text changes',exact:true}).click();
  const retryResponse=page.waitForResponse(response=>response.url().endsWith('/analyze'));
  await page.locator('#row-0').getByRole('button',{name:'Retry analysis',exact:true}).click();
  await retryResponse;
  await page.waitForFunction(()=>document.querySelector('#row-0 .change-preview')?.textContent.includes('Small effusion')&&!document.querySelector('#row-0').textContent.includes('Synthetic incomplete inventory.'));
  assert.equal(retries.length,1);assert.equal(retries[0].id,results[0].id);
  assert.equal(retries[0].resident_report,results[0].resident_report);
  assert.deepEqual(await page.locator('.case-number').allTextContents(),labels);
  for(const width of [320,375,1280]){
   await page.setViewportSize({width,height:950});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Grouped labels overflow at '+width);
  }
  await page.emulateMedia({colorScheme:'dark'});
  await page.waitForTimeout(350); // Let the existing theme transitions finish before visual QA.
  await page.screenshot({path:path.join(out,'grouping-dark.png'),fullPage:true});
  assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);
  console.log('Grouping browser checks passed: labels, one request per group, source/review totals, revision counts, full reports, member search, sort, filter, retry and mobile layout.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

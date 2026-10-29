// Real template and native form submission, synthetic responses only.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.join(__dirname,'qa-output');
const empty=fs.readFileSync(path.join(out,'mode-empty.html'),'utf8');
const queued=fs.readFileSync(path.join(out,'mode-queued.html'),'utf8');
const fixtures=JSON.parse(fs.readFileSync(path.join(out,'mode-fixtures.json'),'utf8'));
const prompts=JSON.parse(empty.match(/<script id="review-prompts" type="application\/json">([\s\S]*?)<\/script>/)[1]);
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try{
  const page=await browser.newPage({viewport:{width:1100,height:900}});
  const errors=[],posts=[],batches=[],retries=[],unexpected=[];let held;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
   const request=route.request(),url=new URL(request.url());
   if(url.origin!=='https://synthetic.invalid'){unexpected.push(url.href);return route.abort();}
   if(url.pathname==='/favicon.ico')return route.fulfill({status:204});
   if(url.pathname==='/'){
    if(request.method()==='POST'){posts.push(Object.fromEntries(new URLSearchParams(request.postData())));return route.fulfill({contentType:'text/html',body:queued});}
    return route.fulfill({contentType:'text/html',body:empty});
   }
   const payload=request.postDataJSON();
   if(url.pathname==='/analyze-batch'){batches.push(payload);held=route;return;}
   if(url.pathname==='/analyze'){
    retries.push(payload);if(retries.length===1)return route.abort('failed');
    return route.fulfill({contentType:'application/json',body:JSON.stringify({...fixtures.resident,review_mode:'attending'})});
   }
   unexpected.push(url.href);return route.abort();
  });
  await page.goto('https://synthetic.invalid/');
  const resident=page.getByRole('radio',{name:'Resident',exact:true}),attending=page.getByRole('radio',{name:'Attending',exact:true});
  assert(await resident.isChecked());
  assert((await attending.boundingBox()).y<(await page.locator('#report-text').boundingBox()).y);
  assert.equal(await page.locator('#custom-prompt').inputValue(),prompts.resident);
  await page.locator('.customize > summary').click();
  // Native radio keys, associated form values, and independent custom drafts.
  await resident.focus();await page.keyboard.press('ArrowRight');assert(await attending.isChecked());
  assert.notEqual(await attending.locator('+ .mode-label').evaluate(node=>getComputedStyle(node).outlineStyle),'none','Keyboard mode selection needs a visible focus indicator');
  assert.equal(await page.locator('#custom-prompt').inputValue(),prompts.attending);
  assert.equal(await page.evaluate(()=>new FormData(document.getElementById('report-form')).get('review_mode')),'attending');
  await page.locator('#custom-prompt').fill('Attending custom draft');
  await resident.check();assert.equal(await page.locator('#custom-prompt').inputValue(),prompts.resident);
  await page.locator('#custom-prompt').fill('Resident custom draft');
  await attending.check();assert.equal(await page.locator('#custom-prompt').inputValue(),'Attending custom draft');
  await page.locator('#restore-prompt').click();
  assert.equal(await page.locator('#custom-prompt').inputValue(),prompts.attending);
  await resident.check();assert.equal(await page.locator('#custom-prompt').inputValue(),'Resident custom draft');
  await attending.check();
  await page.locator('.customize > summary').click();
  assert.equal(batches.length+retries.length,0,'Switching modes must not analyze');
  for(const width of [320,375,1100]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mode toggle overflows '+width);}
  await page.screenshot({path:path.join(out,'mode-toggle-light.png'),clip:{x:0,y:0,width:1100,height:600}});
  await page.emulateMedia({colorScheme:'dark'});await page.waitForTimeout(350);
  await page.screenshot({path:path.join(out,'mode-toggle-dark.png'),clip:{x:0,y:0,width:1100,height:600}});
  await page.locator('#report-text').fill(fixtures.reports_text);
  await page.locator('#analyze-button').click();
  await page.waitForFunction(()=>document.querySelector('#progress-track')?.getAttribute('aria-valuenow')==='0'&&document.querySelector('.case .badge')?.textContent==='Analyzing…');
  assert.equal(posts.length,1);assert.equal(posts[0].review_mode,'attending');assert.equal(posts[0].custom_prompt.replace(/\r\n/g,'\n'),prompts.attending);
  assert(await attending.isChecked());
  assert.equal(batches.length,1);assert.equal(batches[0].review_mode,'attending');assert.equal(batches[0].custom_prompt,prompts.attending);assert.equal(batches[0].cases.length,1);
  await resident.check();
  assert.equal(batches.length,1,'In-flight mode switch must not restart analysis');
  const result={...fixtures.attending,status:'partial',analysis_warnings:['Synthetic partial result.'],review_mode:'resident'};
  await held.fulfill({contentType:'application/x-ndjson',body:[{type:'started',total:1},{type:'case',id:result.id,result},{type:'done',total:1}].map(e=>JSON.stringify(e)).join('\n')+'\n'});
  await page.waitForFunction(()=>document.getElementById('progress-track').getAttribute('aria-valuenow')==='100');
  assert.equal(await page.locator('.case-title').textContent(),'Moderate effusion');
  assert.equal(await page.locator('.case-title').getAttribute('title'),'Review mode: Attending');
  assert.match(await page.locator('#mode-help').textContent(),/Existing results stay unchanged/);
  await attending.check();await resident.check();
  assert.equal(await page.locator('.case-title').textContent(),'Moderate effusion');assert.equal(batches.length,1);
  await page.locator('#case-0').click();
  await page.locator('#input-disclosure > summary').click();
  await page.locator('.customize > summary').click();
  await page.locator('#custom-prompt').fill('Edited resident retry prompt');
  await page.locator('#row-0').getByRole('button',{name:'Retry analysis',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#row-0').textContent.includes('Analysis could not be completed.'));
  assert.equal(await page.locator('.case-title').textContent(),'Moderate effusion');
  assert.equal(await page.locator('.case-title').getAttribute('title'),'Review mode: Attending','Failed retry must not relabel the retained title');
  const retried=page.waitForResponse(response=>response.url().endsWith('/analyze'));
  await page.locator('#row-0').getByRole('button',{name:'Retry analysis',exact:true}).click();await retried;
  await page.waitForFunction(()=>document.querySelector('.case-title')?.textContent==='Small effusion');
  assert.equal(retries.length,2);assert(retries.every(record=>record.review_mode==='resident'&&record.custom_prompt==='Edited resident retry prompt'));
  assert.equal(await page.locator('.case-title').getAttribute('title'),'Review mode: Resident');
  assert.equal(await page.locator('.case-number').textContent(),'Cases68–69');
  assert.equal(await page.locator('#filter-minor').textContent(),'1 minor');
  await attending.check();
  if(!await page.locator('#input-disclosure').evaluate(node=>node.open))await page.locator('#input-disclosure > summary').click();
  await page.locator('#clear-button').click();
  assert(await attending.isChecked());assert.equal(await page.locator('#custom-prompt').inputValue(),prompts.attending);
  await resident.check();assert.equal(await page.locator('#custom-prompt').inputValue(),prompts.resident,'Clear must discard both private custom drafts');
  await attending.check();await page.goto('https://synthetic.invalid/');assert(await resident.isChecked(),'A fresh visit defaults to Resident');
  assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);
  console.log('Mode browser checks passed: Resident default, native keyboard toggle, drafts/reset, form submission, attending request/title, in-flight snapshot, no implicit calls, explicit resident retry, source membership, Clear and mobile layout.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});

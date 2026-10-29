// Synthetic browser regression: local wording choices, opt-in bulk action and stable reading position.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.join(__dirname,'qa-output'),html=fs.readFileSync(path.join(out,'preview.html'),'utf8');
const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixtures.json'),'utf8'))[0];
const cases=Array.from({length:6},(_,i)=>({...fixture,id:'g'+(i+1),source_numbers:[i+1],case_label:String(i+1)}));
const content=html.replace(/(<script id="review-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_m,a,b)=>a+JSON.stringify(cases)+b);
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try {
  const page=await browser.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>r.abort());
  await page.emulateMedia({reducedMotion:'reduce'});
  for(const [width,paired] of [[1440,true],[1280,false],[375,true],[320,false]]){
   await page.setViewportSize({width,height:850});await page.setContent(content);
   if(!paired)await page.locator('#combined-view').uncheck();
   for(const key of [0,1,2])await page.locator('#case-'+key).evaluate(n=>n.click());
   if(paired)await page.locator('#revision-2-0').evaluate(n=>n.click());
   await page.evaluate(()=>{const n=document.getElementById('evidence-2');scrollTo(0,scrollY+n.getBoundingClientRect().top-220);window.wordingControl=n;window.otherRow=document.getElementById('row-0');});
   const top=()=>page.locator('#evidence-2').evaluate(n=>n.getBoundingClientRect().top);
   let before=await top();await page.locator('#evidence-2').click();
   assert(Math.abs(await top()-before)<2,'local toggle preserves viewport position at '+width);
   assert(await page.locator('#row-0 .evidence:not([hidden])').count()>0,'other open cases stay unchanged');
   assert.equal(await page.locator('#row-2 .evidence:not([hidden])').count(),0);
   assert.equal(await page.locator('#wording-all-2').textContent(),'Hide in all cases');
   assert.equal(await page.locator('.wording-dismiss').count(),0);
   await page.locator('#wording-all-2').focus();
   assert(await page.evaluate(()=>window.wordingControl===document.getElementById('evidence-2')&&window.otherRow===document.getElementById('row-0')),'keep case DOM and focus targets mounted');
   if(paired)assert.equal(await page.locator('#revision-2-0').getAttribute('aria-pressed'),'true');
   const bounds=await page.locator('.wording-offer').boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=width,'offer fits at '+width);
   if(width===1440||width===375)await page.screenshot({path:path.join(out,width===1440?'wording-offer-desktop.png':'wording-offer-mobile.png')});
   before=await top();await page.locator('#wording-all-2').click();
   assert(Math.abs(await top()-before)<2,'bulk hide preserves the current control despite shrinking earlier cases at '+width);
   assert.equal(await page.locator('#case-list .evidence:not([hidden])').count(),0);
   assert.equal(await page.evaluate(()=>document.activeElement.id),'evidence-2');
   await page.locator('#case-4').evaluate(n=>n.click());
   assert.equal(await page.locator('#row-4 .evidence:not([hidden])').count(),0,'explicit bulk choice becomes the default for unopened cases');
   before=await top();await page.locator('#evidence-2').click();
   assert(Math.abs(await top()-before)<2);
   assert.equal(await page.locator('#row-0 .evidence:not([hidden])').count(),0,'a later local override stays local');
   before=await top();await page.locator('#wording-all-2').click();
   assert(Math.abs(await top()-before)<2,'bulk show preserves position while earlier cases expand at '+width);
   assert.equal(await page.locator('#case-list .evidence[hidden]').count(),0);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  }
  // A short page tail must not clamp the reader upward after bulk collapse.
  await page.setViewportSize({width:1280,height:850});await page.setContent(content);
  for(const key of [0,1,2,3,4,5])await page.locator('#case-'+key).evaluate(n=>n.click());
  await page.evaluate(()=>{const n=document.getElementById('evidence-5');scrollTo(0,scrollY+n.getBoundingClientRect().top-220);});
  const before=await page.locator('#evidence-5').evaluate(n=>n.getBoundingClientRect().top);
  await page.locator('#evidence-5').click();await page.locator('#wording-all-5').click();
  assert(Math.abs(await page.locator('#evidence-5').evaluate(n=>n.getBoundingClientRect().top)-before)<2,'near-end bulk collapse retains the current case');
  // A fixed two-second deadline applies even while hovered; keyboard focus is retained.
  await page.clock.install();
  await page.locator('#evidence-5').click();await page.locator('#wording-all-5').hover();await page.clock.fastForward(2100);
  assert.equal(await page.locator('.wording-offer').count(),0);
  await page.locator('#evidence-5').click();await page.locator('#wording-all-5').focus();await page.clock.fastForward(2100);
  assert.equal(await page.locator('.wording-offer').count(),1);
  await page.locator('#evidence-5').focus();await page.clock.runFor(1);
  assert.equal(await page.locator('.wording-offer').count(),0,'an expired focused action disappears as soon as focus leaves');
  await page.locator('#evidence-5').click();await page.locator('#wording-all-5').focus();
  await page.keyboard.press('Escape');assert.equal(await page.locator('.wording-offer').count(),0);
  assert.equal(await page.evaluate(()=>document.activeElement.id),'evidence-5');
  await page.evaluate(()=>{const n=document.getElementById('evidence-5');n.click();n.click();});
  await page.clock.runFor(40);
  assert.equal(await page.evaluate(()=>document.documentElement.style.overflowAnchor),'','rapid toggles restore browser scroll anchoring');
  assert.deepEqual(errors,[]);
  console.log('Wording checks passed: local changes, explicit all, stationary controls, mobile, near-end collapse and accessible expiry.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

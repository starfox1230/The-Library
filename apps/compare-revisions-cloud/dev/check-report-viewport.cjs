// Exported reader geometry: no external services or patient data.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output'),file=path.join(out,'viewport-reader.html');
const records=JSON.parse(fs.readFileSync(file,'utf8').match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const lower=records[0].revisions.findIndex(r=>JSON.stringify(r).includes('degeneration'));assert.ok(lower>=0);
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const page=await browser.newPage({viewport:{width:1600,height:900}}),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
 async function locate(index,bottom){
  await page.mouse.move(1,1);await page.waitForTimeout(200);
  await page.locator('#revision-0-'+index).evaluate(n=>scrollTo(0,scrollY+n.getBoundingClientRect().top-180));
  await page.locator('#diff-scroll-0').evaluate((n,bottom)=>n.scrollTop=bottom?n.scrollHeight:0,bottom);
  const before=await page.evaluate(()=>scrollY);await page.locator('#revision-0-'+index).evaluate(n=>n.focus({preventScroll:true}));await page.waitForTimeout(330);
  assert.equal(await page.evaluate(()=>scrollY),before,'finding navigation moved the whole page');
  const visible=await page.locator('#diff-scroll-0').evaluate((viewer,index)=>{
   const v=viewer.getBoundingClientRect(),b=document.querySelector('.phi-banner').getBoundingClientRect(),h=viewer.closest('.report-dock').querySelector('.text-change-header').getBoundingClientRect();
   const top=Math.max(v.top,b.bottom,h.bottom,0),bottom=Math.min(v.bottom,innerHeight);
   const nodes=[...viewer.querySelectorAll('.is-linked')],locations=[...new Set(nodes.flatMap(n=>(n.dataset.locations||'').split(' ')).filter(x=>x.startsWith(index+':')))];
   const ranges=locations.map(l=>nodes.filter(n=>(n.dataset.locations||'').split(' ').includes(l)).flatMap(n=>[...n.getClientRects()]));
   return {top,bottom,groups:ranges.map(rs=>({top:Math.min(...rs.map(r=>r.top)),bottom:Math.max(...rs.map(r=>r.bottom))})),fits:ranges.some(rs=>rs.length&&rs.every(r=>r.top>=top&&r.bottom<=bottom))};
  },index);
  assert.ok(visible.fits,JSON.stringify(visible));
 }
 for(const [width,height,zoom,dense] of [[1600,900,1,false],[1280,600,1,true],[1280,420,1,false],[1600,700,1.25,true],[1600,700,1.5,false]]){
  await page.setViewportSize({width,height});await page.goto('file:///'+file.replaceAll('\\','/'));
  await page.evaluate(zoom=>{document.documentElement.style.zoom=zoom;dispatchEvent(new Event('resize'));},zoom);
  await page.locator('#case-0').click();await page.waitForTimeout(260);
  assert.equal(await page.locator('.link-tools,.diff-key,.diff-panel > .notice').count(),0);
  assert.equal(await page.locator('.text-change-header .pane-heading').first().innerText(),'Text changes');
  if(dense){await page.locator('#explanation-0').click();await page.locator('#evidence-0').click();}
  await locate(lower,false);await locate(0,true);
  await page.locator('#diff-mode-0').selectOption('split');await locate(lower,false);
  await page.locator('#diff-mode-0').selectOption('inline');
 }
 await page.screenshot({path:path.join(out,'report-visible-zoom.png')});
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);console.log('Passed: stripped text-change header, no page movement, complete highlighted quote visible with PHI banner, short viewports, compact/dense summaries, inline/split layouts and 125%/150% scaling.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

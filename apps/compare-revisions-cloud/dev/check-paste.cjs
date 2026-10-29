// Offline clipboard tests with synthetic text: no system clipboard or Azure.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.join(__dirname,'qa-output');
const html=fs.readFileSync(path.join(out,'preview.html'),'utf8');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try {
  const page=await browser.newPage({viewport:{width:1280,height:950}});
  const errors=[];let requests=0;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>{requests++;return route.abort();});
  await page.setContent(html);
  await page.locator('#input-disclosure').evaluate(n=>n.open=true);
  const input=page.locator('#report-text'),button=page.locator('#paste-button');
  assert.equal(await input.getAttribute('placeholder'),null);
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{readText:async()=> 'Case 1\nAttending Report:\nFINDINGS: café → normal\nResident Report:\nFINDINGS: normal'}}));
  await button.click();
  await page.waitForFunction(()=>document.getElementById('paste-status').textContent.includes('Reports pasted'));
  assert.match(await input.inputValue(),/café → normal/);
  assert.equal(await input.evaluate(n=>n===document.activeElement),true);
  assert.equal(requests,0,'Paste must not analyze or transmit text');
  await page.evaluate(()=>navigator.clipboard.readText=async()=>{throw new Error('Denied');});
  const previous=await input.inputValue();
  await button.click();
  await page.waitForFunction(()=>document.getElementById('paste-status').textContent.includes('Ctrl+V'));
  assert.equal(await input.inputValue(),previous,'Denied paste must preserve typed input');
  await page.evaluate(()=>navigator.clipboard.readText=async()=> '   ');
  await button.click();
  await page.waitForFunction(()=>document.getElementById('paste-status').textContent.includes('empty'));
  assert.equal(await input.inputValue(),previous);
  await page.evaluate(()=>navigator.clipboard.readText=()=>new Promise(resolve=>window.completePaste=resolve));
  await button.click();
  assert(await button.isDisabled());
  await page.locator('#clear-button').click();
  await page.evaluate(()=>window.completePaste('Case 999\nlate report'));
  await page.waitForFunction(()=>!document.getElementById('paste-button').disabled);
  assert.equal(await input.inputValue(),'','Clear must discard a late clipboard response');
  await button.click();await input.fill('New manual input');
  await page.evaluate(()=>window.completePaste('Late overwrite'));
  await page.waitForFunction(()=>!document.getElementById('paste-button').disabled);
  assert.equal(await input.inputValue(),'New manual input','Edits must win over a delayed paste');
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:undefined}));
  await button.focus();await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.getElementById('paste-status').textContent.includes('Ctrl+V'));
  for(const width of [320,375,1280]){
   await page.setViewportSize({width,height:950});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert(await button.isVisible());
  }
  await page.setViewportSize({width:1280,height:950});
  await page.screenshot({path:path.join(out,'paste-input.png'),fullPage:true});
  assert.deepEqual(errors,[]);assert.equal(requests,0);
  console.log('Paste passed: Unicode, blocked/absent/empty clipboard, keyboard, Clear/edit races, responsive layout; no requests.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

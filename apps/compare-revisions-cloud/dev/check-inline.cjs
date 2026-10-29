// Verify the service-free conversation preview and its selection-state bridge.
const {chromium}=require('playwright');
const fs=require('fs'),assert=require('assert/strict');
(async()=>{
 const html=fs.readFileSync(process.argv[2],'utf8');
 assert(!/<!doctype|<html|<head>|<body>|fetch\(/i.test(html));
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try {
  const page=await browser.newPage({viewport:{width:1024,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.evaluate(()=>{window.saved=[];window.openai={widgetState:{privateContent:{filters:['minor'],order:'change-high',combinedView:true,showReportWording:false}},setWidgetState:async state=>window.saved.push(state)};});
  await page.setContent(html);
  assert.equal(await page.locator('.case').count(),1);
  assert.equal(await page.locator('#filter-minor').getAttribute('aria-pressed'),'true');
  assert.equal(await page.locator('#order').inputValue(),'change-high');
  assert.equal(await page.locator('.evidence:not([hidden])').count(),0);
  await page.locator('#evidence-0').click();
  assert.equal(await page.evaluate(()=>window.saved.at(-1).privateContent.showReportWording),true);
  await page.locator('#filter-all').click();
  assert.equal(await page.locator('.case').count(),8);
  await page.locator('#filter-major').click();
  assert.deepEqual(await page.evaluate(()=>window.saved.at(-1).privateContent.filters),['major']);
  await page.locator('#order').selectOption('change-low');
  assert.equal(await page.evaluate(()=>window.saved.at(-1).privateContent.order),'change-low');
  assert.deepEqual(errors,[]);
  console.log('Inline preview state, filtering and percentage ordering checks passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

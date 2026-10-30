const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const path=require('path');const assert=require('assert');
(async()=>{
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='warning'||m.type()==='error')console.log(m.text());});
await page.goto('file:///'+path.resolve(__dirname,'../index.html').replaceAll('\\','/'));
await page.waitForTimeout(300);
assert.equal(await page.evaluate(()=>Afterglow.metrics().visual),'particles');
assert.equal(await page.evaluate(()=>Afterglow.renderer),'webgl','GPU test unexpectedly fell back');
await page.click('#beat');await page.click('#reveal');await page.selectOption('#palette','ember');
await page.waitForTimeout(1500);
await page.screenshot({path:path.resolve(__dirname,'../preview.png')});
const metrics=await page.evaluate(()=>Afterglow.metrics());assert(metrics.fps>10,'Renderer did not continue drawing');
await page.evaluate(()=>{clearInterval(previewLoop);window.fixed={config:{...cfg,motion:55,visual:'particles'},flow_time:3,flow_rate:0,particle_phases:Array(8).fill(3),particle_rates:Array(8).fill(0),camera_phase:.1,camera_rate:0,music_level:0,music_bass:0,music_push:0};Afterglow.update(fixed);});
await page.waitForTimeout(150);
const fixed=await page.locator('canvas').evaluate(c=>c.toDataURL());
await page.mouse.move(100,100);await page.mouse.move(900,600);await page.waitForTimeout(150);
assert(fixed===await page.locator('canvas').evaluate(c=>c.toDataURL()),'Pointer or frozen clock moved cloud');
await page.evaluate(()=>Afterglow.update({...fixed,energy:.04,bass:.035,music_level:0,music_bass:1,music_push:1}));
await page.waitForTimeout(100);
assert(fixed===await page.locator('canvas').evaluate(c=>c.toDataURL()),'Raw bass must not yank particle positions');
await page.evaluate(()=>Afterglow.update({...fixed,particle_phases:Array(8).fill(3.2)}));await page.waitForTimeout(100);
assert(fixed!==await page.locator('canvas').evaluate(c=>c.toDataURL()),'Integrated clocks must move particles');
for(const visual of ['liquid','particles','liquid','particles']){await page.evaluate(visual=>Afterglow.update({...fixed,config:{...fixed.config,visual}}),visual);await page.waitForTimeout(100);assert.equal(await page.evaluate(()=>Afterglow.metrics().visual),visual);}
assert.deepEqual(errors,[]);console.log(JSON.stringify({result:'PASS: cloud, no pointer control, no bass position jumps, integrated motion and visual switching',metrics}));
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

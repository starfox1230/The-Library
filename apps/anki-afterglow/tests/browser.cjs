// Run with node; point PLAYWRIGHT_MODULE at an installed playwright package.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const {pathToFileURL}=require('url');
const path=require('path');
const assert=require('assert');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.resolve(__dirname,'../index.html')).href);
 await page.waitForTimeout(250);
 assert(await page.locator('html').evaluate(e=>e.classList.contains('ag-on')));
 await page.click('#reveal');
 await page.waitForTimeout(100);
 assert(await page.locator('.cloze').getAttribute('data-ag-tone'));
 await page.evaluate(()=>{const p=document.createElement('p');p.id='dark-text';p.style.color='#111';p.textContent='Dark letters';document.querySelector('#qa').append(p);});
 await page.waitForTimeout(100);
 assert.equal(await page.locator('#dark-text').getAttribute('data-ag-tone'),'dark');
 await page.locator('#dark-text').evaluate(e=>e.remove());
 await page.click('#beat');
 await page.waitForTimeout(300);
 await page.screenshot({path:path.resolve(__dirname,'../preview.png')});
 await page.click('#motion');
 await page.waitForTimeout(100);
 const a=await page.locator('canvas').evaluate(e=>e.toDataURL());
 await page.waitForTimeout(250);
 const b=await page.locator('canvas').evaluate(e=>e.toDataURL());
 assert.equal(a,b,'motion zero must freeze canvas');
 await page.evaluate(()=>{cfg.enabled=false;});
 await page.waitForTimeout(100);
 assert(!await page.locator('html').evaluate(e=>e.classList.contains('ag-on')));
 assert(await page.locator('canvas').evaluate(e=>e.hidden));
 await page.evaluate(()=>{cfg.enabled=true;cfg.motion=55;});
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.waitForTimeout(150);
 const c=await page.locator('canvas').evaluate(e=>e.toDataURL());
 await page.waitForTimeout(250);
 assert.equal(c,await page.locator('canvas').evaluate(e=>e.toDataURL()),'reduced motion must freeze canvas');
 assert.deepEqual(errors,[]);
 // Compare the exact same scene with music absent and a detected attack.
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.evaluate(()=>{clearInterval(previewLoop);Afterglow.update({config:{...cfg,motion:1,impact:100},energy:0,bass:0,scene_time:0});});
 await page.waitForTimeout(700);
 const light=()=>page.locator('canvas').evaluate(e=>{const p=e.getContext('2d').getImageData(0,0,e.width,e.height).data;let n=0;for(let i=0;i<p.length;i+=4)n+=p[i]+p[i+1]+p[i+2];return n/(p.length/4);});
 const quiet=await light();
 await page.evaluate(()=>Afterglow.update({config:{...cfg,motion:1,impact:100},energy:.05,bass:.04,hit_id:99,scene_time:0}));
 await page.waitForTimeout(65);
 const loud=await light();
 assert(loud>quiet*1.15,`Music should visibly change the scene: ${quiet} -> ${loud}`);
 await page.evaluate(()=>{window.radialCalls=0;const original=CanvasRenderingContext2D.prototype.createRadialGradient;CanvasRenderingContext2D.prototype.createRadialGradient=function(...args){radialCalls++;return original.apply(this,args);};});
 await page.waitForTimeout(250);
 assert.equal(await page.evaluate(()=>radialCalls),0,'Steady-state animation should composite cached glows, not rebuild radial gradients');
 assert(await page.locator('#afterglow-meter').isVisible());
 // Top/card/bottom views render slices of one shared world, rather than restarting
 // the horizon at the top of the answer bar.
 const slices=[];
 for(const size of [1000,100]) {
   const p=await browser.newPage({viewport:{width:1440,height:size}});
   await p.setContent('<html><body><center id="outer"><button id="ansbut">Show answer</button></center></body></html>');
   await p.addStyleTag({path:path.resolve(__dirname,'../web/afterglow.css')});
   await p.addScriptTag({path:path.resolve(__dirname,'../web/afterglow.js')});
   await p.evaluate(size=>Afterglow.update({config:{enabled:true,motion:0,immersive:true,intensity:65},primary:false,surface:{x:0,y:1000-size,width:1440,height:1000},scene_time:0}),size);
   await p.waitForTimeout(100);
   slices.push(await p.locator('canvas').evaluate((e,size)=>Array.from(e.getContext('2d').getImageData(0,e.height-100,e.width,100).data),size));
   assert.equal(await p.locator('#outer').evaluate(e=>getComputedStyle(e).backgroundColor),'rgba(0, 0, 0, 0)');
   await p.close();
 }
 let diff=0;for(let i=0;i<slices[0].length;i++)diff+=Math.abs(slices[0][i]-slices[1][i]);
 assert(diff/slices[0].length<1,'Shared scene must align across card and answer bar');
 console.log(`Audio visual response: ${quiet.toFixed(1)} -> ${loud.toFixed(1)} RGB sum; aligned toolbar slices and cached gradients verified`);
 console.log('PASS: browser rendering, card replacement, adaptive halos, demo rhythm, still mode, disable, reduced motion; no JS errors');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});

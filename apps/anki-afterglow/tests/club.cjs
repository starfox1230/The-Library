const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const path=require('path');const assert=require('assert');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 if(process.env.FORCE_CANVAS)await context.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'?null:original.call(this,type,...args);};});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file:///'+path.resolve(__dirname,'../index.html').replaceAll('\\','/'));
 await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>Afterglow.metrics().visual),'club');
 assert.equal(await page.evaluate(()=>Afterglow.renderer),process.env.FORCE_CANVAS?'canvas':'webgl');
 await page.click('#beat');await page.click('#reveal');await page.waitForTimeout(1500);
 const metrics=await page.evaluate(()=>Afterglow.metrics());assert(metrics.fps>10);
 if(!process.env.FORCE_CANVAS)await page.screenshot({path:path.resolve(__dirname,'../preview.png')});
 await page.evaluate(()=>{clearInterval(previewLoop);Afterglow.update({config:{...cfg,motion:0}});});
 await page.waitForTimeout(100);
 const frozen=await page.locator('canvas').evaluate(c=>{Afterglow.paint();return c.toDataURL();});
 await page.waitForTimeout(150);
 assert.equal(frozen,await page.locator('canvas').evaluate(c=>{Afterglow.paint();return c.toDataURL();}));
 await page.evaluate(()=>Afterglow.update({config:{...cfg,motion:55}}));
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(100);
 const reduced=await page.locator('canvas').evaluate(c=>{Afterglow.paint();return c.toDataURL();});
 await page.waitForTimeout(150);assert.equal(reduced,await page.locator('canvas').evaluate(c=>{Afterglow.paint();return c.toDataURL();}));
 await page.evaluate(()=>Afterglow.update({config:{enabled:false}}));assert(await page.locator('canvas').evaluate(c=>c.hidden));
 // Hold time and light constant. Compare occupied pixels to establish a real
 // positional beat response, rather than counting brighter pixels as movement.
 const probe=await context.newPage();await probe.setContent('<html><body><canvas width="900" height="600"></canvas></body></html>');
 await probe.addScriptTag({path:path.resolve(__dirname,'../web/club.js')});
 const movement=await probe.evaluate(()=>{
   const canvas=document.querySelector('canvas'),renderer=AfterglowClub(canvas);
   const scene={w:900,h:600,vw:900,vh:600,x:0,y:0,time:2,clubTime:2,intensity:.7,quality:1,particleCount:1800,palette:'neon',level:.5};
   const pixels=beat=>{renderer.draw({...scene,clubBeat:beat});const copy=document.createElement('canvas');copy.width=900;copy.height=600;const ctx=copy.getContext('2d');ctx.drawImage(renderer.canvas,0,0);return ctx.getImageData(0,0,900,600).data;};
   const quiet=pixels(0),kick=pixels(1);let lit=0,overlap=0,shift=0;
   for(let i=0;i<quiet.length;i+=4){const q=quiet[i]+quiet[i+1]+quiet[i+2]>35,k=kick[i]+kick[i+1]+kick[i+2]>35;if(q)lit++;if(q&&k)overlap++;if(q!==k)shift++;}
   return {lit,retained:overlap/Math.max(1,lit),changed:shift,particles:renderer.particles};
 });
 assert(movement.lit>500,'Neon ribbons should be visible');
 assert(movement.retained<.6,`Beat must relocate particles, not merely brighten them: ${JSON.stringify(movement)}`);
 assert(movement.changed>movement.lit,'Large spatial response expected');
 assert.deepEqual(errors,[]);console.log(JSON.stringify({result:'PASS: club motion, spatial beat response, pause, reduced motion and disable',movement,metrics}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

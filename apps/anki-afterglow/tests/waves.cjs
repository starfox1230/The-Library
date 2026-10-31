const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const path=require('path');const assert=require('assert');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 if(process.env.FORCE_CANVAS)await context.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'?null:original.call(this,type,...args);};});
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file:///'+path.resolve(__dirname,'../index.html').replaceAll('\\','/'));
 await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>Afterglow.metrics().visual),'waves');
 await page.click('#beat');await page.click('#reveal');await page.waitForTimeout(1500);
 const metrics=await page.evaluate(()=>Afterglow.metrics());assert(metrics.fps>10);
 assert.equal(metrics.renderer,process.env.FORCE_CANVAS?'canvas':'webgl');
 if(!process.env.FORCE_CANVAS)await page.screenshot({path:path.resolve(__dirname,'../preview.png')});
 await page.evaluate(()=>{clearInterval(previewLoop);Afterglow.update({config:{...cfg,motion:0}});});await page.waitForTimeout(100);
 const capture=()=>page.locator('canvas').evaluate(c=>{Afterglow.paint();return c.toDataURL();});
 const frozen=await capture();await page.waitForTimeout(150);assert.equal(frozen,await capture());
 await page.emulateMedia({reducedMotion:'reduce'});await page.evaluate(()=>Afterglow.update({config:{...cfg,motion:55}}));await page.waitForTimeout(100);
 const reduced=await capture();await page.waitForTimeout(150);assert.equal(reduced,await capture());
 await page.emulateMedia({reducedMotion:'no-preference'});
 for(const visual of ['club','particles','liquid','waves']){await page.selectOption('#visual',visual);await page.evaluate(()=>Afterglow.update({config:cfg}));await page.waitForTimeout(80);assert.equal(await page.evaluate(()=>Afterglow.metrics().visual),visual);}
 await page.evaluate(()=>Afterglow.update({config:{enabled:false}}));assert(await page.locator('canvas').evaluate(c=>c.hidden));
 const probe=await context.newPage();await probe.setContent('<html><body><canvas width="900" height="600"></canvas></body></html>');
 await probe.addScriptTag({path:path.resolve(__dirname,'../web/waves.js')});
 const movement=await probe.evaluate(()=>{
  const canvas=document.querySelector('canvas'),renderer=AfterglowWaves(canvas);
  const scene={w:900,h:600,vw:900,vh:600,x:0,y:0,time:2,clubTime:2,intensity:.7,quality:1,particleCount:1800,palette:'neon',level:.5,waveImpact:1,clubBeat:0};
  // Read bright contour cores; broad stationary glow is intentionally excluded.
  const mask=(bands,kick=0)=>{renderer.draw({...scene,waveBands:bands,clubBeat:kick});const c=document.createElement('canvas');c.width=900;c.height=600;const ctx=c.getContext('2d');ctx.drawImage(renderer.canvas,0,0);const p=ctx.getImageData(0,0,900,600).data;return Uint8Array.from({length:900*600},(_,i)=>p[i*4]+p[i*4+1]+p[i*4+2]>200?1:0);};
  const quiet=mask(Array(8).fill(0)),low=mask([1,1,0,0,0,0,0,0]),mid=mask([0,0,1,1,1,0,0,0]),high=mask([0,0,0,0,0,1,1,1]),kick=mask(Array(8).fill(0),1);
  const retained=(a,b)=>{let n=0,m=0;for(let i=0;i<a.length;i++){n+=a[i];m+=a[i]&&b[i]?1:0;}return m/Math.max(1,n);};
  return {lit:quiet.reduce((a,b)=>a+b,0),low:retained(quiet,low),mid:retained(quiet,mid),high:retained(quiet,high),midToHigh:retained(mid,high),kick:retained(quiet,kick),particles:renderer.particles};
 });
 assert(movement.lit>500,'Circular contours should be visible');
 for(const band of ['low','mid','high','midToHigh','kick'])assert(movement[band]<.65,`Expected independent spatial ${band} response: ${JSON.stringify(movement)}`);
 // Verify native numeric bands reach the renderer independently of volume.
 const bridge=await context.newPage();await bridge.setContent('<html><body></body></html>');
 await bridge.evaluate(()=>{window.Last=null;window.AfterglowWaves=canvas=>({canvas,kind:'probe',draw:s=>window.Last=s});});
 await bridge.addScriptTag({path:path.resolve(__dirname,'../web/afterglow.js')});
 await bridge.evaluate(()=>Afterglow.update({config:{enabled:true,motion:55,visual:'waves'},energy:.02,bands:[.012,0,0,0,0,0,0,0]}));await bridge.waitForTimeout(300);
 assert(await bridge.evaluate(()=>Last.waveBands[0]>.5&&Last.waveBands[7]<.01));
 await bridge.evaluate(()=>Afterglow.update({config:{enabled:true,motion:55,visual:'waves'},energy:.02,bands:[0,0,0,0,0,0,0,.012]}));await bridge.waitForTimeout(350);
 assert(await bridge.evaluate(()=>Last.waveBands[7]>.5&&Last.waveBands[0]<.1));
 assert.deepEqual(errors,[]);console.log(JSON.stringify({result:'PASS: wave contours, independent bands, kick displacement, native band bridge, preset switching and still modes',movement,metrics}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

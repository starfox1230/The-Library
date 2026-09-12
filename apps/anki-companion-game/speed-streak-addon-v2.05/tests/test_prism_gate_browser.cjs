/* Run with NODE_PATH pointing to a Playwright installation. No dependency ships in the add-on. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  const browser = await chromium.launch({headless: true, channel: process.env.PRISM_BROWSER || 'msedge'});
  try {
    const context = await browser.newContext({viewport:{width:390,height:820},deviceScaleFactor:2});
    const page = await context.newPage();
    const errors=[]; page.on('pageerror', e => errors.push(String(e)));
    await page.addInitScript(() => {
      window.prismDraws = 0; window.prismStrokes = 0; window.hypernovaTimes = [];
      window.hypernovaRingGroups = new Map();window.hypernovaRingSamples = [[],[]];window.hypernovaRingPaths=0;
      const arc = CanvasRenderingContext2D.prototype.arc;
      CanvasRenderingContext2D.prototype.arc = function(x,y,r,...args) {
        if (!this.canvas.id && x===0 && y===0 && r>=.319 && r<=.942) {
          const ring=Math.round((r-.32)/.069);
          const group=hypernovaRingGroups.get(this.canvas)||new Set();group.add(ring);
          hypernovaRingGroups.set(this.canvas,group);hypernovaRingPaths++;
        }
        return arc.call(this,x,y,r,...args);
      };
      const drawImage=CanvasRenderingContext2D.prototype.drawImage;
      CanvasRenderingContext2D.prototype.drawImage=function(source,...args) {
        const group=hypernovaRingGroups.get(source);
        if(this.canvas.id==='acgPrismCanvas' && group) {
          const parity=group.has(0)?0:1, matrix=this.getTransform();
          const samples=hypernovaRingSamples[parity];samples.push(Math.atan2(matrix.b,matrix.a));
          if(samples.length>60)samples.shift();
        }
        return drawImage.call(this,source,...args);
      };
      const fill = CanvasRenderingContext2D.prototype.fillRect;
      CanvasRenderingContext2D.prototype.fillRect = function(x,y,w,h) {
        if (this.canvas.id === 'acgPrismCanvas' && x===0 && y===0) { window.prismDraws++; window.hypernovaTimes.push(performance.now()); }
        return fill.call(this,x,y,w,h);
      };
      const stroke = CanvasRenderingContext2D.prototype.stroke;
      CanvasRenderingContext2D.prototype.stroke = function(...args) {
        if (this.canvas.id === 'acgPrismCanvas') window.prismStrokes++;
        return stroke.apply(this,args);
      };
    });
    await page.goto(pathToFileURL(path.join(__dirname,'prism_gate_harness.html')).href);
    await page.waitForTimeout(600);
    const patch = async p => page.evaluate(p=>updateDemoState(p),p);
    const draws = async()=>page.evaluate(()=>window.prismDraws);
    const still = async(label) => {
      await page.waitForTimeout(120); const a=await draws(); await page.waitForTimeout(300);
      assert.equal(await draws(),a,label);
    };
    assert.equal(await page.locator('#acgPrismStreak').textContent(),'0');
    await still('Quiet seed does not redraw at idle');
    await page.evaluate(()=>demoEvent('good'));
    await page.waitForTimeout(2100);
    const firstAnswerDraws=await draws();await page.waitForTimeout(300);
    assert(await draws()>firstAnswerDraws+10,'First earned piece keeps rotating after the answer pulse');
    await patch({streak:17,satelliteColors:Array(17).fill('green')});await page.waitForTimeout(200);
    const pathsBefore=await page.evaluate(()=>hypernovaRingPaths);
    await page.waitForTimeout(1100);
    const turns=await page.evaluate(()=>hypernovaRingSamples.map(samples=>samples.at(-1)-samples[0]));
    assert(turns[0]>.15 && turns[1]<-.15,`At 17, neighboring rings must counter-rotate: ${turns}`);
    assert.equal(await page.evaluate(()=>hypernovaRingPaths),pathsBefore,'Ring paths stay cached during rotation');
    await patch({streak:27});await page.waitForTimeout(150);
    assert(await page.evaluate(()=>Array.from(hypernovaRingGroups.values()).some(group=>group.has(0)&&group.has(2)&&!group.has(1))), 'Third ring shares the first ring direction, opposite the second');
    await patch({streak:126,satelliteColors:Array(126).fill('green')});
    await page.waitForTimeout(500);
    assert.equal(await page.locator('#acgPrismPhase').count(),0);
    const a=await draws(); await page.waitForTimeout(1100); const fps=(await draws()-a)/1.1;
    assert(fps>=48 && fps<=62,`Smooth must sustain at least 48 FPS on this 60 Hz test host: ${fps}`);
    const cadence = await page.evaluate(() => {
      const times=hypernovaTimes.slice(-60);const intervals=times.slice(1).map((t,i)=>t-times[i]).sort((a,b)=>a-b);
      return {fps:1000/(intervals.reduce((a,b)=>a+b,0)/intervals.length),p95IntervalMs:intervals[Math.floor(intervals.length*.95)]};
    });
    console.log('Smooth cadence:',JSON.stringify(cadence));
    assert(cadence.p95IntervalMs<35,'Smooth frame cadence must not keep skipping refreshes');
    for (const p of [{paused:true},{renderMode:'ultra_low_resource',paused:false},{orbitAnimationEnabled:false,renderMode:'webgl'},{reducedMotion:true,orbitAnimationEnabled:true}]) {
      await patch(p); await still(JSON.stringify(p));
    }
    await patch({reducedMotion:false});
    await page.emulateMedia({reducedMotion:'reduce'}); await still('OS reduced motion');
    await page.emulateMedia({reducedMotion:'no-preference'});
    await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))});
    await still('hidden document');
    await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))});
    await patch({enabled:false}); await still('disabled');
    await patch({enabled:true,visualsEnabled:false});await still('visuals off');
    await patch({visualsEnabled:true,displayMode:'inline',sidebarCollapsed:true});await still('collapsed');
    await patch({displayMode:'compatibility',sidebarCollapsed:false,renderMode:'webgl'});
    // Streak magnitude must not increase the renderer's fixed drawing budget.
    const drawCost=async streak=>{
      await patch({streak}); await page.waitForTimeout(150);
      const before=await page.evaluate(()=>[prismDraws,prismStrokes]);await page.waitForTimeout(500);
      const after=await page.evaluate(()=>[prismDraws,prismStrokes]);return (after[1]-before[1])/(after[0]-before[0]);
    };
    assert.equal(await drawCost(100),await drawCost(1000000));
    for(const size of [{width:290,height:520},{width:1000,height:1800},{width:390,height:820}]) {
      await page.setViewportSize(size);await page.waitForTimeout(150);
      const dimensions=await page.locator('#acgPrismCanvas').evaluate(c=>[c.width,c.height]);
      assert(dimensions.every(n=>n>0 && n<=960),'Canvas resolution hard cap');
    }
    for(const mode of ['sphere','crystal_reactor','singularity','lightweight_rows','number_only','prism_gate']) {
      await patch({visualMode:mode,streak:126,satelliteColors:Array(126).fill('green')});await page.waitForTimeout(100);
      if(mode!=='prism_gate') {await still(`switched to ${mode}`);assert.equal(await page.locator('#acgPrismCanvas').evaluate(c=>c.width),1);}
    }
    // Event bursts replace one bounded event slot even when answers arrive rapidly.
    for(const kind of ['good','easy','hard','time-boost','again','timeout','reset']) {
      await page.evaluate(kind=>demoEvent(kind),kind);await page.waitForTimeout(50);
    }
    assert.equal(await page.locator('#acgPrismStreak').textContent(),'0');
    await patch({streak:49});await page.evaluate(()=>demoEvent('good'));assert.equal(await page.locator('#acgPrismPhase').count(),0);
    await patch({streak:99});await page.evaluate(()=>demoEvent('easy'));assert.equal(await page.locator('#acgPrismPhase').count(),0);
    await patch({streak:126,renderMode:'low_resource',lastEventType:'',customColors:{core:'#3289db'}});
    await page.waitForTimeout(1700);
    await page.screenshot({path:path.join(__dirname,'hypernova-preview.png')});
    // The live selector must send a real saveSettings command with this exact mode.
    await page.locator('#acgVisualSelector').evaluate(el=>el.classList.add('open'));
    await page.locator('[data-visual-choice="prism_gate"]').click();
    assert(await page.evaluate(()=>demoCommands.some(x=>x.includes('prism_gate'))));
    await page.locator('#acgVisualSelector').evaluate(el=>el.classList.remove('open'));
    assert.deepEqual(errors,[]);
    console.log('Hypernova lifecycle, events, selector, resolution, long-streak budget, and reduced-motion checks passed.');
    if (process.env.HYPERNOVA_SKIP_BENCHMARK === '1') return;
    // Compare actual Chromium CPU seconds, JS heap, and Windows browser-process working sets.
    const system = await browser.newBrowserCDPSession();
    const session = await context.newCDPSession(page);await session.send('Performance.enable');
    const cpu=async()=>{const {processInfo}=await system.send('SystemInfo.getProcessInfo');return {seconds:processInfo.reduce((sum,p)=>sum+p.cpuTime,0),ids:processInfo.map(p=>p.id)}};
    const memory=ids=>process.platform==='win32'?Number(execFileSync('powershell.exe',['-NoProfile','-Command',`(Get-Process -Id ${ids.join(',')} -ErrorAction SilentlyContinue | Measure-Object -Property WorkingSet64 -Sum).Sum`],{encoding:'utf8',windowsHide:true}).trim())/1048576:null;
    const results=[];
    for(let repeat=0;repeat<2;repeat++)for(const [mode,quality] of [['prism_gate','low_resource'],['prism_gate','webgl'],['singularity','low_resource'],['sphere','webgl'],['crystal_reactor','webgl'],['number_only','ultra_low_resource']]) {
      await patch({visualMode:mode,renderMode:quality,streak:126,satelliteColors:Array(126).fill('green'),customColors:{},phase:'idle',paused:false});
      await page.waitForTimeout(700);
      const before=await cpu(); const start=performance.now();await delay(2200);const after=await cpu();const elapsed=(performance.now()-start)/1000;
      const {metrics}=await session.send('Performance.getMetrics');const heap=metrics.find(m=>m.name==='JSHeapUsedSize').value/1048576;
      results.push({repeat,mode,quality,cpuPercentOneCore:+((after.seconds-before.seconds)/elapsed*100).toFixed(2),jsHeapMiB:+heap.toFixed(2),browserWorkingSetMiB:memory(after.ids)});
    }
    fs.writeFileSync(path.join(__dirname,'hypernova-benchmark.json'),JSON.stringify({cadence,environment:'Windows, headless Microsoft Edge Chromium; 390×820, DPR 2; idle timer; 126-card streak. CPU summed over browser processes, percentage of one core. Shared process working set includes retained renderer resources; no battery wattage measurement.',results},null,2)+'\n');
    console.log(JSON.stringify(results,null,2));
    assert.deepEqual(errors,[]);
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

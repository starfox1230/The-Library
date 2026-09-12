// Persistent progression must be visible in canvas pixels, without the DOM count
// or a transient answer effect. This also generates the reviewable contact sheet.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
(async()=>{
  const browser=await chromium.launch({headless:true,channel:process.env.PRISM_BROWSER||'msedge',args:['--disable-webgl']});
  try {
    const page=await browser.newPage({viewport:{width:390,height:820},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(pathToFileURL(path.join(__dirname,'prism_gate_harness.html')).href);
    const sample=async(streak,index)=>{
      await page.evaluate(streak=>updateDemoState({streak,renderMode:'ultra_low_resource',lastEventType:'',satelliteColors:Array(Math.min(100,streak)).fill('green')}),streak);
      await page.waitForTimeout(60);
      return page.locator('#acgPrismCanvas').evaluate((c,index)=>{
        const ctx=c.getContext('2d'),r=Math.min(c.clientWidth*.47,c.clientHeight*.39)*(.32+Math.floor(index/10)*.069);
        const ring=Math.floor(index/10), slot=ring%2 ? 9-(index%10) : index%10;
        const a=-Math.PI/2+(slot+.5)*Math.PI/5;
        const x=Math.round((c.clientWidth/2+Math.cos(a)*r)*c.width/c.clientWidth);
        const y=Math.round((c.clientHeight/2+Math.sin(a)*r)*c.height/c.clientHeight);
        const px=ctx.getImageData(x-1,y-1,3,3).data;
        return Array.from(px).filter((_,i)=>i%4!==3).reduce((sum,n)=>sum+n,0)/27;
      },index);
    };
    for(const [before,after,index] of [[0,1,0],[1,2,1],[12,13,12],[99,100,99],[101,102,1],[212,213,12]]) {
      const empty=await sample(before,index),earned=await sample(after,index);
      assert(Math.abs(earned-empty)>25,`${before} → ${after} must visibly change its permanent piece: ${empty} / ${earned}`);
    }
    const first=await sample(1,0);const retained=await sample(2,0);
    assert(Math.abs(first-retained)<2,'An earlier earned piece remains after the next answer');
    const colored=await sample(13,12);
    await page.evaluate(()=>updateDemoState({satelliteColors:Array(13).fill('blue')}));
    await page.waitForTimeout(60);
    const beforeReset=await page.locator('#acgPrismCanvas').evaluate(c=>c.toDataURL());
    await sample(13,12);
    assert.notEqual(await page.locator('#acgPrismCanvas').evaluate(c=>c.toDataURL()),beforeReset,'Still mode refreshes rating colors without changing the streak');
    assert(colored>40);
    const captures=[];
    for(const streak of [0,1,2,9,10,12,13,20,30,50,70,100]) {
      await sample(streak,0);
      captures.push({streak,image:(await page.locator('.acg-prism-scene').screenshot()).toString('base64')});
    }
    const sheet=await browser.newPage({viewport:{width:1120,height:1130},deviceScaleFactor:1});
    await sheet.setContent(`<html><body style="margin:0;background:#060b14;color:#e0f8ff;font:16px system-ui;padding:24px"><h1 style="margin:0 0 8px">Hypernova · build it one answer at a time</h1><p style="color:#93adbd;margin:0 0 20px">Each lit segment is earned. Every ten cards completes a ring and unlocks another layer.</p><main style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">${captures.map(c=>`<div><div style="margin-bottom:6px">${c.streak} cards</div><img style="width:100%;height:270px;object-fit:contain;background:#020611;border:1px solid #1d3549;border-radius:12px" src="data:image/png;base64,${c.image}"></div>`).join('')}</main></body></html>`);
    await sheet.screenshot({path:path.join(__dirname,'hypernova-progression.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(__dirname,'hypernova-progression-results.json'),JSON.stringify({checks:'Persistent canvas-only changes at 0→1, 1→2, 12→13, 99→100, 101→102, 212→213; earlier piece retained; same-streak palette correction; WebGL disabled',passed:true},null,2)+'\n');
    console.log('Persistent per-answer progression, retention, long-streak reforging, and Still color updates passed.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

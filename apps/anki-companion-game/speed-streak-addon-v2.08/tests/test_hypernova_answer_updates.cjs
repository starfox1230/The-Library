// NODE_PATH must expose Playwright. Uses an isolated browser, never an Anki profile.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');const path=require('node:path');const {pathToFileURL}=require('node:url');
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.PRISM_BROWSER||'msedge'});try{
const page=await browser.newPage({viewport:{width:390,height:820},deviceScaleFactor:2});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto(pathToFileURL(path.join(__dirname,'prism_gate_harness.html')).href);
await page.evaluate(()=>{
 const now=new Date();now.setHours(12,0,0,0);
 const runs=Array.from({length:5},(_,i)=>({id:i+1,streak:500-i*10,endedAt:now.toISOString()}));
 updateDemoState({streak:126,satelliteColors:Array(126).fill('green'),scoreboardLayout:'best_only',runHistory:{bestStreak:500,savedBestStreak:500,active:{streak:126},runs}});
 window.originalRow=document.querySelector('.acg-scoreboard-row');
 window.originalIcon=document.querySelector('#acgVisualSelectorCurrentIcon svg');
 window.originalTick=document.querySelector('#acgVisualResourceTicks span');
 window.rowMutations=0;new MutationObserver(list=>rowMutations+=list.length).observe(document.getElementById('acgScoreboardRows'),{childList:true,subtree:true});
});
for(const kind of ['hard','good','easy','hard','good','easy']){
 await page.evaluate(kind=>{demoEvent(kind);const now=Date.now();updateDemoState({phase:'question',phaseStartEpochMs:now,phaseLimitMs:12000,phaseBaseLimitMs:12000,timerDisplayRemainingMs:12000,timerDisplayNowEpochMs:now});},kind);
 await page.waitForTimeout(80);
}
assert(await page.evaluate(()=>originalRow===document.querySelector('.acg-scoreboard-row')),'Existing record node survives answer updates');
assert(await page.evaluate(()=>originalIcon===document.querySelector('#acgVisualSelectorCurrentIcon svg')),'Selector SVG survives answer updates');
assert(await page.evaluate(()=>originalTick===document.querySelector('#acgVisualResourceTicks span')),'Selector ticks survive answer updates');
assert.equal(await page.evaluate(()=>rowMutations),0,'No completed-row DOM churn during live answers');
assert.equal(await page.locator('#acgPrismStreak').textContent(),'132');
await page.evaluate(()=>updateDemoState({runHistory:{...demoState.runHistory,bestStreak:501,active:{streak:501}}}));
assert.equal(await page.locator('#acgScoreboardBest').textContent(),'501');
assert.equal(await page.locator('#acgScoreboardTarget small').first().textContent(),'NEW RECORD');
assert(await page.evaluate(()=>originalRow===document.querySelector('.acg-scoreboard-row')));
await page.evaluate(()=>{const runs=demoState.runHistory.runs.slice(1);updateDemoState({scoreboardLayout:'ladder',scoreboardOrder:'chronological',runHistory:{...demoState.runHistory,runs}})});
assert.equal(await page.locator('.acg-scoreboard-row').count(),4);
assert.equal(await page.locator('.acg-scoreboard-row').first().getAttribute('data-scoreboard-run-id'),'2');
await page.evaluate(()=>{const runs=demoState.runHistory.runs.map(r=>({...r,pauseCount:r.id===2?1:0}));updateDemoState({scoreboardPurity:'pure',runHistory:{...demoState.runHistory,runs}})});
assert.equal(await page.locator('.acg-scoreboard-row').count(),3);
assert.equal(await page.locator('.acg-scoreboard-row').first().getAttribute('data-scoreboard-run-id'),'3');
await page.evaluate(()=>{const NativeDate=Date;window.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[NativeDate.now()+86400000]))}static now(){return NativeDate.now()+86400000}};updateDemoState({});});
assert((await page.locator('.acg-scoreboard-row-copy strong').first().textContent()).startsWith('Yesterday'));
assert.deepEqual(errors,[]);console.log('Answer updates preserve record and selector nodes; live record, deletion, ordering, purity, and date rollover still update correctly.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});

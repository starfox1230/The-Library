const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const page=await browser.newPage({viewport:{width:900,height:850}});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.setContent('<html><body>Timer display test</body></html>');
 await page.evaluate(()=>window.pycmd=()=>{});
 for(const file of ['overlay.css','card_timer.css'])await page.addStyleTag({path:path.join(__dirname,'../web',file)});
 for(const file of ['overlay.js','card_timer.js'])await page.addScriptTag({path:path.join(__dirname,'../web',file)});
 const data={enabled:true,visualsEnabled:true,showCardTimer:true,sidePanelEnabled:true,displayMode:'compatibility',visualMode:'number_only',renderMode:'ultra_low_resource',phase:'question',phaseStartEpochMs:Date.now(),phaseLimitMs:12000,phaseBaseLimitMs:12000,timerDisplayRemainingMs:8100,timerDisplayNowEpochMs:Date.now(),paused:true,pausedRemainingMs:8100,streak:3,audioEnabled:false,hapticsEnabled:false};
 const send=async patch=>{Object.assign(data,patch);await page.evaluate(d=>{SpeedStreak.receiveState(d);SpeedStreakCardTimer.receiveState(d)},data)};
 await send({timerNumberMode:'decimal'});
 assert.equal(await page.locator('#sstValue').textContent(),'8.1s');
 assert.equal(await page.locator('#sstLab').isVisible(), false);
 await send({labTouch:true,labQuiet:true,labSavedMs:1500,labRaceBestMs:5000,currentCardId:'123',timeDrainFlag:2,reviewLaterFlag:4});
 await page.evaluate(() => { window.commands = []; window.pycmd = command => commands.push(command); });
 await page.locator('[data-sst-touch="later"]').click();
 assert.deepEqual(await page.evaluate(() => commands), ['speed-streak:lab-touch:later:123']);
 assert.equal(await page.locator('#sstLabSaved').textContent(), '1.5 s saved · Best 5.0 s');
 assert.equal(await page.locator('#sstLabRace i').first().evaluate(el => el.style.width), '30%');
 assert.equal(await page.locator('.acg-trial-hourglass').isVisible(), true);
 await send({labTouch:false,labQuiet:false,labSavedMs:null,labRaceBestMs:null});
 assert.equal(await page.locator('#sstLab').isVisible(), false);
 assert.equal(await page.locator('#acgTimerValue').textContent(),'8.1');
 await send({timerNumberMode:'seconds'});
 assert.equal(await page.locator('#sstValue').textContent(),'9s');
 assert.equal(await page.locator('#acgTimerValue').textContent(),'9');
 await send({timerDisplayRemainingMs:100,pausedRemainingMs:100});
 assert.equal(await page.locator('#sstValue').textContent(),'1s');
 await send({timerNumberMode:'hidden'});
 assert.equal(await page.locator('#sstValue').evaluate(e=>getComputedStyle(e).display),'none');
 assert.equal(await page.locator('#acgTimerValue').evaluate(e=>getComputedStyle(e).visibility),'hidden');
 assert.equal(await page.locator('#speed-streak-card-timer').evaluate(e=>e.classList.contains('hidden')),false);
 await send({timerNumberMode:'decimal',phase:'answer',paused:false,answerTimerPaused:true,phaseLimitMs:0,phaseBaseLimitMs:0});
 assert.equal(await page.locator('#sstValue').textContent(),'ANSWER\nUNTIMED');
 assert.equal(await page.locator('#acgTimerValue').textContent(),'UNTIMED');
 assert.equal(await page.locator('#acgPhaseLabel').textContent(),'Answer');
 await page.waitForTimeout(250);
 assert.equal(await page.locator('#sstValue').textContent(),'ANSWER\nUNTIMED');
 assert.equal(await page.locator('#speed-streak-card-timer').evaluate(e=>e.classList.contains('danger')),false);
 await send({phase:'question',answerTimerPaused:false,paused:true,phaseLimitMs:12000,phaseBaseLimitMs:12000,timerDisplayRemainingMs:12000,pausedRemainingMs:12000});
 assert.equal(await page.locator('#sstValue').textContent(),'12.0s');
 // Independent formats: exercise all combinations on the real timer surfaces.
 for (const circle of ['decimal','seconds','hidden']) for (const card of ['decimal','seconds','hidden']) {
   await send({timerNumberMode:circle,cardTimerNumberMode:card,timerDisplayRemainingMs:8100,pausedRemainingMs:8100});
   assert.equal(await page.locator('#sstValue').evaluate(e=>getComputedStyle(e).display),card==='hidden'?'none':'block');
   assert.equal(await page.locator('#acgTimerValue').evaluate(e=>getComputedStyle(e).visibility),circle==='hidden'?'hidden':'visible');
   if(card!=='hidden') assert.equal(await page.locator('#sstValue').textContent(),card==='seconds'?'9s':'8.1s');
   if(circle!=='hidden') assert.equal(await page.locator('#acgTimerValue').textContent(),circle==='seconds'?'9':'8.1');
 }
 // Hidden circle numbers leave the phase label centered in every review state.
 for (const [phase,paused] of [['question',false],['answer',false],['question',true]]) {
   await send({timerNumberMode:'hidden',phase,paused,phaseStartEpochMs:Date.now()});
   const centers=await page.evaluate(()=>{
     const ring=document.querySelector('#acgTimerHero').getBoundingClientRect();
     const label=document.querySelector('#acgPhaseLabel').getBoundingClientRect();
     return {dx:label.x+label.width/2-ring.x-ring.width/2,dy:label.y+label.height/2-ring.y-ring.height/2};
   });
   assert(Math.abs(centers.dx)<2 && Math.abs(centers.dy)<2,JSON.stringify(centers));
 }
 await send({timerNumberMode:'decimal'});
 assert.notEqual(await page.locator('#acgTimerValue').evaluate(e=>getComputedStyle(e).display),'none');
 // Hiding numbers must not hide explanations for free/untimed cards.
 for (const phase of ['question','answer']) {
   await send({timerNumberMode:'hidden',cardTimerNumberMode:'hidden',firstCardFree:true,phase,paused:false,phaseLimitMs:0});
   assert.equal(await page.locator('#sstValue').textContent(),'FREE');
   assert.equal(await page.locator('#sstValue').isVisible(),true);
   assert.equal(await page.locator('#acgTimerValue').textContent(),'FREE');
   assert.equal(await page.locator('#acgTimerValue').isVisible(),true);
 }
 await send({firstCardFree:false,phase:'answer',answerTimerPaused:true,phaseLimitMs:0,paused:false});
 assert.equal(await page.locator('#sstValue').isVisible(),true);
 assert.equal(await page.locator('#acgPauseOverlay').evaluate(e=>e.classList.contains('visible')),false);
 assert.equal(await page.locator('#acgTimerValue').isVisible(),true);
 // Wide fonts and narrow review windows must never split either word.
 await page.setViewportSize({width:280,height:850});
 for(const font of ['Arial','Georgia','monospace']) {
   await page.locator('#sstValue').evaluate((e,font)=>{e.style.fontFamily=font;e.style.letterSpacing='2px'},font);
   const lines=await page.locator('#sstValue').evaluate(e=>{
     const node=e.firstChild;
     return [0,5,7,13].map(i=>{const r=document.createRange();r.setStart(node,i);r.setEnd(node,i+1);return r.getBoundingClientRect().y});
   });
   assert.equal(lines[0],lines[1]);
   assert.equal(lines[2],lines[3]);
   assert(lines[2]>lines[0]);
 }
 const timerSpaceBefore=await page.locator("#acgTimerContextZone").boundingBox();
 await send({showSidePanelTimer:false});
 assert.deepEqual(await page.locator("#acgTimerContextZone").boundingBox(),timerSpaceBefore);
 assert.equal(await page.locator('#acgTimerContextZone').isVisible(),false);
 assert.equal(await page.locator('#speed-streak-sidebar').isVisible(),true);
 assert.equal(await page.locator('#speed-streak-card-timer').isVisible(),true);
 await send({showSidePanelTimer:true});
 assert.equal(await page.locator('#acgTimerContextZone').isVisible(),true);
 assert.deepEqual(errors,[]);
 console.log('Both timer surfaces: decimals, rounded seconds, hidden numbers, answer pause, next question passed.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});

import test from 'node:test';import assert from 'node:assert/strict';
import {createGame,validateCheckpoints} from '../game.mjs';
const target=(id,x,plane='axial')=>({id,label:id,side:x?'left':'right',windows:[{width:[60,120],level:[25,55]}],regions:[{plane,normal:[9,11],polygon:[[x,0],[x+10,0],[x+10,10],[x,10]],toleranceMm:0}],representative:{plane,patient:[x+5,5,10],width:80,level:40}});
const phases=[{id:'first',targets:[target('right',0),target('left',20)]},{id:'second',targets:[target('last',40)]}];
function setup(mode='timed',p=phases){let time=0;const game=createGame({phases:p,mode,now:()=>time});return {game,tick:t=>time=t};}
const click=(g,x=5,options={})=>g.click({patient:[x,5,10],plane:'axial',width:80,level:40,...options});
test('loading and idle cannot score',()=>{const {game:g}=setup();assert.equal(g.start(false),false);assert.equal(click(g).kind,'ignored');assert.equal(g.start(true),true);assert.equal(click(g).kind,'hit');});
test('both sides required and repeats ignored',()=>{const {game:g}=setup();g.start(true);click(g);assert.equal(click(g).kind,'ignored');assert.equal(g.snapshot().completed.length,1);assert.equal(g.snapshot().phaseId,'first');click(g,25);assert.equal(g.snapshot().phaseId,'second');});
test('wrong plane and outside slice miss',()=>{const {game:g}=setup();g.start(true);assert.equal(click(g,5,{plane:'coronal'}).kind,'miss');assert.equal(click(g,5,{patient:[5,5,12]}).kind,'miss');assert.equal(click(g,11).kind,'miss');});
test('window mismatch provides hint without credit',()=>{const {game:g}=setup();g.start(true);assert.equal(click(g,5,{width:2500,level:500}).kind,'window');assert.deepEqual(g.snapshot().completed,[]);});
test('future-phase target does not score',()=>{const {game:g}=setup();g.start(true);assert.equal(click(g,45).kind,'miss');});
test('overlap chooses smallest region then ID',()=>{const a=target('large',0),b=target('small',0);b.regions[0].polygon=[[4,4],[6,4],[6,6],[4,6]];const {game:g}=setup('practice',[{id:'p',targets:[a,b]}]);g.start(true);assert.equal(click(g).targetId,'small');});
test('pause freezes time demotes and blocks clicks',()=>{const {game:g,tick}=setup();g.start(true);tick(2000);g.pause();tick(9000);assert.equal(click(g).kind,'ignored');g.resume();tick(9500);assert.equal(g.snapshot().elapsedMs,2500);assert.equal(g.snapshot().eligible,false);assert.equal(g.snapshot().mode,'practice');});
test('completion freezes clock and repeated completion is ignored',()=>{const {game:g,tick}=setup();g.start(true);click(g);click(g,25);tick(3100);click(g,45);tick(9999);assert.equal(g.snapshot().status,'complete');assert.equal(g.snapshot().elapsedMs,3100);assert.equal(g.snapshot().eligible,true);assert.equal(click(g,45).kind,'ignored');});
test('restart clears state and requires Start',()=>{const {game:g}=setup();g.start(true);click(g);g.restart('timed');assert.equal(g.snapshot().status,'idle');assert.deepEqual(g.snapshot().completed,[]);assert.equal(click(g).kind,'ignored');});
test('practice never eligible and repeated start cannot reset timer',()=>{const {game:g,tick}=setup('practice');g.start(true);tick(1000);assert.equal(g.start(true),false);tick(2000);assert.equal(g.snapshot().elapsedMs,2000);assert.equal(g.snapshot().eligible,false);});
test('invalid click coordinates ignored safely',()=>{const {game:g}=setup();g.start(true);assert.equal(click(g,5,{patient:[NaN,0,0]}).kind,'ignored');});
test('manifest mismatch and malformed annotation rejected',()=>{
 const m={id:'case',version:'1',checkpointVersion:'1'},c={caseId:'case',caseVersion:'1',version:'1',phases};
 assert.equal(validateCheckpoints(m,c),c);
 assert.throws(()=>validateCheckpoints(m,{...c,caseVersion:'2'}),/version/i);
 const bad=structuredClone(c);bad.phases[0].targets[0].regions[0].polygon=[[0,0]];assert.throws(()=>validateCheckpoints(m,bad),/polygon/i);
 const miss=structuredClone(c);miss.phases[0].targets[0].representative.patient=[99,99,99];assert.throws(()=>validateCheckpoints(m,miss),/representative/i);
});

const {test}=require('node:test');const assert=require('node:assert/strict');const {JSDOM}=require('jsdom');const {readFileSync}=require('node:fs');const {resolve}=require('node:path');const tick=()=>new Promise(done=>setImmediate(done));
async function audio(prefs={}){
 const dom=new JSDOM('<iframe src="https://player.vimeo.com/video/123"></iframe>',{url:'https://medality.com/course/demo/unit/test/',runScripts:'outside-only'}),w=dom.window;let change;const intervals=[],players=[];
 w.setInterval=fn=>{intervals.push(fn);return 1;};
 const observers=[],Original=w.MutationObserver;w.MutationObserver=class extends Original{constructor(fn){super(fn);observers.push(this);}};
 w.chrome={storage:{local:{get:async defaults=>({...defaults,...prefs}),set:async()=>{}},onChanged:{addListener:fn=>{change=fn;}}},runtime:{onMessage:{addListener(){}}}};
 w.Vimeo={Player:class{constructor(){this.muted=true;this.volume=0;this.handlers={};this.sets=[];players.push(this);}on(e,fn){this.handlers[e]=fn;}off(e){delete this.handlers[e];}async getMuted(){return this.muted;}async setMuted(v){this.muted=v;this.sets.push(v);}async getVolume(){return this.volume;}async setVolume(v){this.volume=v;}}};
 w.eval(readFileSync(resolve(__dirname,'../extension/audio.js'),'utf8'));await tick();
 return{w,players,intervals,change:(obj)=>change(obj,'local'),close(){observers.forEach(o=>o.disconnect());w.close();}};
}
test('autoplay audio restores muted player and zero volume without calling play',async()=>{const e=await audio();assert.equal(e.players[0].muted,false);assert.equal(e.players[0].volume,1);e.players[0].muted=true;e.players[0].handlers.loaded();await tick();assert.equal(e.players[0].muted,false);e.close();});
test('deliberate mute preference survives subsequent autoplay',async()=>{const e=await audio({audioMuted:true});assert.equal(e.players[0].muted,true);assert.equal(e.players[0].volume,0);e.players[0].handlers.play();await tick();assert.equal(e.players[0].muted,true);e.close();});
test('audio option can be disabled and explicit Restore sound works',async()=>{const e=await audio({rememberAudio:false});assert.deepEqual(e.players[0].sets,[]);assert.equal(await e.w.MedalityRestoreAudio(),true);assert.equal(e.players[0].muted,false);e.close();});
test('iframe reuse gets another audio check even without SDK loaded event',async()=>{const e=await audio();e.intervals.forEach(fn=>fn());await tick();e.players[0].muted=true;e.w.document.querySelector('iframe').src='https://player.vimeo.com/video/456';await tick();e.intervals.forEach(fn=>fn());await tick();assert.equal(e.players[0].muted,false);e.close();});

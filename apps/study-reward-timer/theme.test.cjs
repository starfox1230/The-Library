const test=require('node:test');
const assert=require('node:assert/strict');
const T=require('./theme');
const sample=(elapsedMs,extra={})=>T.resolve({active:true,targetMs:1080000,elapsedMs,...extra});
const composite=(back,front,alpha)=>back.map((value,i)=>value*(1-alpha)+front[i]*alpha);
function luminance(color) {
  const channels=(Array.isArray(color)?color:T.rgb(color)).map(n=>{const c=n/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4;});
  return channels[0]*.2126+channels[1]*.7152+channels[2]*.0722;
}
function contrast(a,b) {const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}

test('countdown moves continuously from night through wine to ruby for every duration',()=>{
  assert.equal(T.resolve().phase,'idle');assert.equal(T.resolve().palette.bg,'#080b15');
  let previous=T.rgb(sample(0).palette.bg);
  for(let i=1;i<=1000;i++) {
    const normal=sample(1080000*i/1000),short=sample(6000*i/1000,{targetMs:6000});
    assert.deepEqual(short.palette,normal.palette);
    const current=T.rgb(normal.palette.bg);
    assert.ok(current[0]>=previous[0],`red channel at ${i}`);
    assert.ok(current.every((n,k)=>Math.abs(n-previous[k])<=3),`no band/jump at ${i}`);
    previous=current;
  }
  assert.equal(sample(1080000).palette.bg,'#b51c31');
});

test('last-two-minute pulse boundaries stop at overtime and never change payout timing',()=>{
  assert.equal(sample(959999).warning,false);assert.equal(sample(959999).pulse,'off');
  assert.equal(sample(960000).warning,true);assert.equal(sample(960000).pulse,'slow');
  assert.equal(sample(1049999).pulse,'slow');assert.equal(sample(1050000).pulse,'fast');
  assert.equal(sample(1080000).phase,'running');assert.equal(sample(1080000).pulse,'fast');
  const over=sample(1080001);assert.equal(over.phase,'overtime');assert.equal(over.pulse,'off');
  assert.notEqual(over.palette.bg,sample(1080000).palette.bg);
  assert.equal(sample(1080000*10).palette.bg,over.palette.bg);
});

test('real pause always uses gold; holding preserves its current colors and silences pulsing',()=>{
  const late=sample(1060000),held=sample(1060000,{holding:true});
  assert.equal(held.phase,'running');assert.deepEqual(held.palette,late.palette);assert.equal(held.pulse,'off');
  const paused=sample(1060000,{paused:true});assert.equal(paused.phase,'paused');assert.equal(paused.palette.bg,'#f4c75f');assert.equal(paused.pulse,'off');
  assert.deepEqual(sample(1100000,{paused:true}).palette,paused.palette);
  assert.equal(sample(1100000,{holding:true}).phase,'overtime');
  assert.equal(T.resolve({active:false,paused:true,holding:true}).phase,'idle');
});

test('motion-off leaves a static final-minutes warning with the same readable palette',()=>{
  const normal=sample(1060000),quiet=sample(1060000,{motion:false});
  assert.equal(quiet.warning,true);assert.equal(quiet.pulse,'off');assert.deepEqual(quiet.palette,normal.palette);
});

test('text and buttons retain contrast across the gradient and the brightest pulse',()=>{
  const looks=Array.from({length:1001},(_,i)=>sample(1080000*i/1000));
  looks.push(sample(1200000),sample(500000,{paused:true}));
  for(const look of looks) {
    const p=look.palette;
    let peak=T.rgb(p.bg);
    peak=composite(peak,T.rgb(p.accent),.055);
    peak=composite(peak,T.rgb(p.buttonA),.035);
    if(look.warning)peak=composite(peak,[255,225,211],.04);
    for(const color of [p.text,p.muted,p.accent,look.vars['--timer-secondary']]) {
      for(const back of [p.bg,peak,look.vars['--timer-panel-a'],look.vars['--timer-panel-b']]) {
        assert.ok(contrast(color,back)>=4.5,`${look.phase} ${look.progress.toFixed(3)}: ${color} on ${JSON.stringify(back)} = ${contrast(color,back).toFixed(2)}`);
      }
    }
    for(const fill of [p.buttonA,p.buttonB,look.vars['--timer-hold-a'],look.vars['--timer-hold-b']])assert.ok(contrast(p.ink,fill)>=4.5,`${p.ink} on ${fill}`);
  }
});

test('renderer updates browser chrome, stops pulse states, and avoids unchanged color writes',()=>{
  const values={},body={dataset:{}},attributes={content:'#000000'};let writes=0;
  const renderer=T.createRenderer({root:{style:{setProperty(key,value){values[key]=value;writes++;}}},body,themeColor:{getAttribute:key=>attributes[key],setAttribute(key,value){attributes[key]=value;}}});
  renderer.update({active:true,targetMs:1080000,elapsedMs:1060000});
  assert.equal(body.dataset.theme,'running');assert.equal(body.dataset.pulse,'fast');assert.equal(attributes.content,values['--timer-bg']);
  const original=writes;renderer.update({active:true,targetMs:1080000,elapsedMs:1060000});assert.equal(writes,original);
  renderer.update({active:true,targetMs:1080000,elapsedMs:1060000,paused:true});assert.equal(body.dataset.pulse,'off');assert.equal(attributes.content,'#f4c75f');
  renderer.update({});assert.equal(body.dataset.theme,'idle');assert.equal(values['--timer-bg'],'#080b15');
});

import test from 'node:test';import assert from 'node:assert/strict';
import {normalizeWheel,isGameShortcut,isClick} from '../input.mjs';
import {readBest,saveBest,recordKey} from '../records.mjs';
test('drag and editable targets cannot trigger scoring shortcuts',()=>{
 assert.equal(isClick([0,0],[12,0]),false);assert.equal(isClick([0,0],[2,2]),true);
 for(const tagName of ['INPUT','SELECT','TEXTAREA'])assert.equal(isGameShortcut({target:{tagName}}),false);
 assert.equal(isGameShortcut({target:{tagName:'CANVAS'},ctrlKey:true}),false);
 assert.equal(isGameShortcut({target:{tagName:'CANVAS'}}),true);
});
test('touchpad carries small deltas and bounds big bursts',()=>{
 assert.deepEqual(normalizeWheel({deltaY:10,deltaMode:0},0),{steps:0,carry:10});
 assert.deepEqual(normalizeWheel({deltaY:30,deltaMode:0},10),{steps:1,carry:0});
 assert.equal(normalizeWheel({deltaY:3,deltaMode:1},0).steps,1);
 assert.equal(normalizeWheel({deltaY:10000,deltaMode:0},0).steps,4);
});
test('broken storage is harmless',()=>{
 const bad={getItem(){throw Error('blocked')},setItem(){throw Error('blocked')}};
 assert.equal(readBest(bad,'k'),null);assert.equal(saveBest(bad,'k',{status:'complete',eligible:true,mode:'timed',elapsedMs:1200}),null);
});
test('only valid eligible completed times can replace best',()=>{
 let value=null;const s={getItem:()=>value,setItem:(k,v)=>value=v};const ok={status:'complete',eligible:true,mode:'timed',elapsedMs:2000};
 assert.equal(saveBest(s,'k',ok),2000);assert.equal(saveBest(s,'k',{...ok,elapsedMs:3000}),2000);
 assert.equal(saveBest(s,'k',{...ok,eligible:false,elapsedMs:10}),2000);
 value='-1';assert.equal(readBest(s,'k'),null);value='broken';assert.equal(readBest(s,'k'),null);
 assert.notEqual(recordKey({caseId:'a',caseVersion:'1',checkpointVersion:'1',mode:'timed'}),recordKey({caseId:'a',caseVersion:'1',checkpointVersion:'2',mode:'timed'}));
});

const {test}=require('node:test');
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('focused text fields keep their caret even when WebKit reports a body selection',()=>{
 const listeners={},ui={nodeType:1,closest:()=>null},input={nodeType:1,closest:()=>({})};let clears=0;
 const selection={rangeCount:1,anchorNode:ui,focusNode:ui,removeAllRanges(){clears++;}};
 const document={activeElement:input,addEventListener:(name,fn)=>(listeners[name]??=[]).push(fn)};
 vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'interaction.js'),'utf8'),{document,window:{getSelection:()=>selection}});
 for(let i=0;i<30;i++){listeners.selectionchange.forEach(fn=>fn());let blocked=false;listeners.selectstart.forEach(fn=>fn({target:ui,cancelable:true,preventDefault(){blocked=true;}}));assert.equal(blocked,false);}
 assert.equal(clears,0,'typing must never clear the focused field caret');
 document.activeElement=ui;listeners.selectionchange.forEach(fn=>fn());assert.equal(clears,1,'UI selection is still cleared outside fields');
 let blocked=false;listeners.selectstart.forEach(fn=>fn({target:ui,cancelable:true,preventDefault(){blocked=true;}}));assert.equal(blocked,true);
 selection.anchorNode=input;selection.focusNode=input;listeners.selectionchange.forEach(fn=>fn());assert.equal(clears,1,'editable selection is preserved even without focus');
});

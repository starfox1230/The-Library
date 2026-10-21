const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');
const {runtime,record}=require('./fixtures.cjs');
test('worker accepts only own-extension RadPrimer messages and opens only its local library',async()=>{
  let listener,icon,created=[],saved=0;
  const context={importScripts:()=>{},RadCore:require('../extension/core.js'),RadDB:{saveCapture:async c=>{saved++;return c;}},chrome:{runtime:{id:'ours',getURL:p=>'chrome-extension://ours/'+p,onMessage:{addListener:f=>{listener=f;}}},action:{onClicked:{addListener:f=>{icon=f;}}},tabs:{create:args=>created.push(args)}}};
  vm.runInNewContext(fs.readFileSync(path.join(runtime,'background.js'),'utf8'),context);
  const c=await record();let response;
  assert.equal(listener({type:'rp:save',capture:c},{id:'other',tab:{url:'https://app.radprimer.com/assessment/a'}},r=>{response=r;}),undefined);assert.equal(saved,0);
  assert.equal(listener({type:'rp:save',capture:c},{id:'ours',tab:{url:'https://app.radprimer.com.evil.test/'}},r=>{response=r;}),undefined);assert.equal(saved,0);
  const pending=new Promise(resolve=>listener({type:'rp:save',capture:c},{id:'ours',tab:{url:'https://app.radprimer.com/assessment/a'}},resolve));
  assert.equal((await pending).ok,true);assert.equal(saved,1);icon();assert.equal(created[0].url,'chrome-extension://ours/library.html');
});
test('manifest limits access and packages runtime without external code or network access in library',()=>{
  const m=JSON.parse(fs.readFileSync(path.join(runtime,'manifest.json'),'utf8'));assert.equal(m.manifest_version,3);
  assert.deepEqual(m.permissions,['unlimitedStorage']);assert.deepEqual(m.content_scripts[0].matches,['https://app.radprimer.com/*']);assert.equal(m.host_permissions,undefined);assert.equal(m.externally_connectable,undefined);assert.equal(m.web_accessible_resources,undefined);
  assert.match(m.content_security_policy.extension_pages,/connect-src 'none'/);assert.match(m.content_security_policy.extension_pages,/img-src 'self' data:/);
});

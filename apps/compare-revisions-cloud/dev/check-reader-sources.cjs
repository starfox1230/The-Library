// Actual pinned OCR plus editable, offline source evidence; all identifiers fictional.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const out=path.join(__dirname,'qa-output');
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const context=await browser.newContext({permissions:['clipboard-read','clipboard-write'],viewport:{width:1280,height:1000}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/qa',async route=>{
  const response=await route.fetch(),html=await response.text(),match=html.match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/),cases=JSON.parse(match[1]);
  cases[0].title_resident='Initial pelvic mass';cases[0].title_attending='Favored uterine fibroid';
  await route.fulfill({response,body:html.replace(match[1],JSON.stringify(cases).replaceAll('<','\\u003c'))});
 });
 await page.goto('http://127.0.0.1:8766/qa');
 assert((await page.locator('#row-0 .case-title').innerText()).includes('Initial pelvic mass'));
 await page.locator('#mode-attending').check();assert((await page.locator('#row-0 .case-title').innerText()).includes('Favored uterine fibroid'));
 await page.locator('#input-disclosure > summary').click();
 await page.evaluate(()=>{
  window.makeShot=(first,count)=>{const c=document.createElement('canvas');c.width=900;c.height=30+count*36;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,c.width,c.height);x.fillStyle='black';x.font='24px Arial';
   for(let i=0;i<count;i++){const n=first+i,y=30+i*36;x.fillText(String(n),10,y);x.fillText('9876543',150,y);x.fillText('OT900001'+String(n).padStart(3,'0'),400,y);x.fillText('IGNORE',730,y);}
   return new Promise(resolve=>c.toBlob(blob=>resolve(new File([blob],'synthetic.png',{type:'image/png'}))));};
  window.pasteShot=async(first,count)=>{const dt=new DataTransfer();dt.items.add(await window.makeShot(first,count));document.querySelector('#lookup-paste-zone').dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));};
 });
 await page.evaluate(()=>window.pasteShot(68,6));await page.evaluate(()=>window.pasteShot(71,6));
 assert.equal(await page.locator('.lookup-screenshot').count(),2);assert((await page.locator('#lookup-paste').innerText()).includes('(3)'));
 await page.waitForFunction(()=>document.querySelectorAll('.lookup-screenshot').length===2&&[...document.querySelectorAll('.lookup-screenshot summary')].every(n=>/\d+ rows/.test(n.textContent)),{},{timeout:180000});
 assert.equal(await page.locator('.lookup-screenshot[open]').count(),0,'OCR details should stay optional');
 assert.equal(await page.locator('#lookup-rows tr').count(),9,'overlap should deduplicate 71-73');
 const mappings=await page.locator('#lookup-value').inputValue().then(JSON.parse);assert.equal(mappings.length,9,await page.locator('#lookup-rows').innerText());assert(mappings.every(r=>r.accession==='OT900001'+String(r.case_number).padStart(3,'0')));assert(mappings.every(r=>r.source_row?.startsWith('data:image/png;base64,')));
 await page.locator('.lookup-screenshot summary').nth(0).click();await page.waitForFunction(()=>document.querySelector('#lookup-editor').parentElement===document.querySelectorAll('.lookup-screenshot')[0]&&document.querySelectorAll('#lookup-rows tr').length===6);
 await page.locator('.lookup-screenshot > summary').nth(1).click();await page.waitForFunction(()=>document.querySelector('#lookup-editor').parentElement===document.querySelectorAll('.lookup-screenshot')[1]&&document.querySelectorAll('#lookup-rows tr').length===6);assert.equal(await page.locator('#lookup-rows tr').count(),6,'each screenshot should show its own rows, including shared overlaps');
 await page.locator('.lookup-screenshot > summary').nth(1).click();
 const download=page.waitForEvent('download');await page.locator('#export-review').click();const file=await download,exportPath=path.join(out,'source-review.html');await file.saveAs(exportPath);
 const html=fs.readFileSync(exportPath,'utf8');assert(html.includes('source_row'));assert(html.includes('Initial pelvic mass'));assert(html.includes('Favored uterine fibroid'));assert(!html.includes('9876543'));
 const readerContext=await browser.newContext(),reader=await readerContext.newPage(),network=[];reader.on('pageerror',e=>errors.push(e.message));
 await reader.route('**/*',route=>{if(route.request().url().startsWith('file:'))return route.continue();network.push(route.request().url());return route.abort();});
 await reader.goto('file:///'+exportPath.replaceAll('\\','/'));
 await reader.evaluate(()=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>window.copied=value}});});
 assert((await reader.locator('#row-0 .case-title').innerText()).includes('Favored uterine fibroid'));
 await reader.locator('#mode-resident').check();assert((await reader.locator('#row-0 .case-title').innerText()).includes('Initial pelvic mass'));
 await reader.locator('#row-0 .case-copy-accession').click();assert.equal(await reader.evaluate(()=>window.copied),'OT900001068');
 const image=reader.locator('.accession-peek img');await image.waitFor();assert(await image.evaluate(i=>i.complete&&i.naturalWidth>0));
 await reader.getByRole('textbox',{name:'Correct accession for case 68'}).fill('OT900001099');await reader.getByRole('button',{name:'Copy corrected accession',exact:true}).click();assert.equal(await reader.evaluate(()=>window.copied),'OT900001099');
 const corrected=reader.waitForEvent('download');await reader.locator('#save-review').click();const saved=await corrected,correctedPath=path.join(out,'source-review-corrected.html');await saved.saveAs(correctedPath);
 await reader.goto('file:///'+correctedPath.replaceAll('\\','/'));assert((await reader.locator('#row-0 .case-title').innerText()).includes('Initial pelvic mass'));
 const finalLookup=JSON.parse(await reader.locator('#lookup-data').textContent());assert.equal(finalLookup.find(r=>r.case_number===68).accession,'OT900001099');assert(finalLookup.find(r=>r.case_number===68).source_row);
 await reader.evaluate(()=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>window.copied=value}});});await reader.setViewportSize({width:375,height:900});await reader.locator('#row-0 .case-copy-accession').click();assert(await reader.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await reader.screenshot({path:path.join(out,'source-peek-mobile.png')});await reader.locator('.accession-peek').screenshot({path:path.join(out,'source-peek.png')});
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);console.log('Queued headerless screenshots, optional per-image editing, overlap joins, cropped PNG export, dual title switching and offline correction/save/reopen passed.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1);});

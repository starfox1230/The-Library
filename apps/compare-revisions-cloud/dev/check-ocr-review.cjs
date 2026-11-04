// Real production UI with synthetic OCR tokens/pixels; no OCR/model/network calls.
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const context=await browser.newContext({viewport:{width:1280,height:1000}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const u=new URL(route.request().url());return ['127.0.0.1','localhost'].includes(u.hostname)?route.continue():route.abort();});
 await page.route('http://127.0.0.1:8766/qa',async route=>{const response=await route.fetch(),html=await response.text();
  const hook="window.ocrQA={get rows(){return lookupRows},set rows(v){lookupRows=v},images:lookupImages,read:readImageRows,show:showLookupImage,table:lookupTable,available:availableLookup};";
  await route.fulfill({response,body:html.replace('})();',hook+'})();')});
 });
 await page.goto('http://127.0.0.1:8766/qa');await page.locator('#input-disclosure > summary').click();
 await page.evaluate(async()=>{
  ocrQA.rows=[];
  for(const [id,start,end] of [['a',1,59],['b',57,65],['c',63,70]]){
   const canvas=document.createElement('canvas');canvas.width=400;canvas.height=(end-start+1)*24+24;const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='black';ctx.font='16px Arial';
   const img={id,label:'Screenshot '+id,words:[],caseColumn:[0,60],accessionColumn:[80,350],headerY:0};
   for(let n=start;n<=end;n++){
    const y=24+(n-start)*24,actual='CT9900'+String(n).padStart(5,'0');ctx.fillText(n,8,y);ctx.fillText(actual,90,y);
    const readNumber=(id==='a'&&n===11)?'1':(id==='b'&&n===61)?'6':String(n);
    const accession=id==='a'&&n===33?'ZZ'+actual.slice(2):((id==='a'&&n===40)||(id==='b'&&n===58)||(id==='c'&&n===65))?actual+'9':actual;
    img.words.push({text:readNumber,confidence:70,bbox:{x0:8,x1:40,y0:y-15,y1:y+2}},{text:accession,confidence:75,bbox:{x0:90,x1:300,y0:y-15,y1:y+2}});
   }
   img.bitmap=await createImageBitmap(canvas);img.details=document.createElement('details');img.details.className='lookup-screenshot';img.summary=document.createElement('summary');img.details.append(img.summary);document.querySelector('#lookup-images').append(img.details);ocrQA.images.push(img);ocrQA.read(img);
  }
 });
 assert.equal(await page.evaluate(()=>ocrQA.rows.length),70);assert.equal(await page.evaluate(()=>ocrQA.available().length),68);
 assert.deepEqual(await page.evaluate(()=>ocrQA.rows.map(r=>r.case_number)),Array.from({length:70},(_,i)=>i+1));
 assert.equal(await page.evaluate(()=>ocrQA.rows.find(r=>r.case_number===57).imageId),'a');
 assert.equal(await page.evaluate(()=>ocrQA.rows.find(r=>r.case_number===58).accession),'CT990000058');
 assert.deepEqual(await page.evaluate(()=>ocrQA.images.map(i=>i.duplicateCount)),[0,3,3]);
 await page.evaluate(()=>ocrQA.show(ocrQA.images[1],true));
 assert.deepEqual(await page.evaluate(()=>[...document.querySelector('#lookup-canvas').getContext('2d').getImageData(2,15,1,1).data]),[0,0,0,255],'repeated image row is blacked out');
 await page.locator('#lookup-review').click();assert(await page.locator('#ocr-review-dialog').evaluate(d=>d.open));
 assert.equal(await page.locator('#ocr-review-case').inputValue(),'33');assert(await page.locator('#ocr-review-crop').isVisible());
 assert.equal(await page.locator('#ocr-review-accession').evaluate(e=>document.activeElement===e),true);
 await page.locator('#ocr-review-accession').fill('CT990000033');await page.keyboard.press('Tab');
 assert.equal(await page.locator('#ocr-review-case').inputValue(),'40');
 fs.mkdirSync(path.join(__dirname,'qa-output'),{recursive:true});await page.screenshot({path:path.join(__dirname,'qa-output/ocr-review-overlay.png')});
 await page.setViewportSize({width:390,height:844});const box=await page.locator('#ocr-review-dialog').boundingBox();assert(box.x>=0&&box.x+box.width<=390,'review overlay overflows mobile');await page.screenshot({path:path.join(__dirname,'qa-output/ocr-review-mobile.png')});
 await page.locator('#ocr-review-accession').fill('CT990000040');await page.keyboard.press('Enter');
 assert.equal(await page.locator('#ocr-review-dialog').evaluate(d=>d.open),false);assert(await page.locator('#lookup-review').isDisabled());assert.equal(await page.evaluate(()=>ocrQA.available().length),70);
 // Choosing the second conflicting source must not skip the following item.
 await page.evaluate(()=>{ocrQA.images.length=0;ocrQA.rows=[{case_number:81,accession:'CT990000081',source:'First'},{case_number:81,accession:'MR990000081',source:'Second'},{case_number:82,accession:'CT9900000829',accessionIssue:'Check length'}];ocrQA.table();});
 await page.locator('#lookup-review').click();await page.locator('#ocr-review-alternatives button').click();assert.equal(await page.locator('#ocr-review-accession').inputValue(),'MR990000081');
 await page.locator('#ocr-review-keep').click();assert.equal(await page.locator('#ocr-review-case').inputValue(),'82','removing an earlier conflicting source must not skip the next row');
 await page.locator('#ocr-review-accession').fill('CT990000082');await page.keyboard.press('Tab');assert.equal(await page.locator('#ocr-review-dialog').evaluate(d=>d.open),false);
 assert.deepEqual(await page.evaluate(()=>ocrQA.available().map(r=>r.accession)),['MR990000081','CT990000082']);
 // One absolute start repairs an otherwise unread whole image and skips the
 // now-resolved case-only checks rather than requiring three confirmations.
 await page.evaluate(()=>{const img={id:'unknown',rowsReady:true,details:document.createElement('details'),summary:document.createElement('summary'),rows:[91,92,93].map(n=>({imageId:'unknown',case_number:null,caseIssue:'Case number not read',accession:'CT9900'+String(n).padStart(5,'0')}))};ocrQA.images.push(img);ocrQA.rows.push(...img.rows);ocrQA.table();});
 await page.locator('#lookup-review').click();await page.locator('#ocr-review-case').fill('91');await page.locator('#ocr-review-accession').press('Enter');
 assert.equal(await page.locator('#ocr-review-dialog').evaluate(d=>d.open),false);assert.equal(await page.evaluate(()=>ocrQA.available().length),5);assert.deepEqual(errors,[]);
 console.log('OCR review UI passed: sequence autocorrection, three-image overlaps, source blackouts, first reading, cropped evidence, keyboard navigation and conflict selection.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

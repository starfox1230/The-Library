// Only explicitly confirmed, batch-local mappings reach the reader or AI input form.
let lookupRows=JSON.parse($('lookup-data').textContent||'[]');
const lookupSourceText=$('report-text')?.value;
const lookupMatchesReview=()=>exportedReview||!cases.length||$('report-text').value===lookupSourceText;
const validLookup=r=>Number.isInteger(r.case_number)&&r.case_number>0&&r.case_number<=1000000&&typeof r.accession==='string'&&/^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/.test(r.accession);
function lookupConflicts(){
 const seen=new Map(),conflicts=new Set();
 for(const r of lookupRows){if(!validLookup(r))continue;if(seen.has(r.case_number)&&seen.get(r.case_number)!==r.accession)conflicts.add(r.case_number);seen.set(r.case_number,r.accession);}
 return conflicts;
}
function caseAccessions(c){if(!lookupMatchesReview())return [];const conflicts=lookupConflicts();return [...new Map(lookupRows.filter(r=>r.confirmed&&validLookup(r)&&!conflicts.has(r.case_number)&&members(c).includes(r.case_number)).sort((a,b)=>a.case_number-b.case_number).map(r=>[r.accession,r])).values()];}
async function copyAccession(target,value){
 const original=target.textContent;
 try{
  try{if(!navigator.clipboard?.writeText)throw Error();await navigator.clipboard.writeText(value);}
  catch{const box=el('textarea');box.value=value;box.setAttribute('aria-label','Accession to copy');box.style.cssText='position:fixed;left:-9999px;top:0';document.body.append(box);box.select();let ok=false;try{ok=document.execCommand('copy');}finally{box.remove();target.focus({preventScroll:true});}if(!ok)throw Error();}
  target.textContent='Accession copied';$('announcement').textContent='Accession copied';
 }catch{target.textContent='Copy unavailable';$('announcement').textContent='Copy unavailable. Select the displayed accession and press Ctrl+C.';}
 setTimeout(()=>{target.textContent=original;},1400);
}
function appendAccessionTools(row,c){
 const entries=caseAccessions(c);if(!entries.length){if(lookupRows.length){const missing=el('div','accession-tools');missing.append(el('span','muted','Accession not attached'));row.append(missing);}return;}
 const tools=el('div','accession-tools'),copy=button('Copy accession','copy-accession',()=>copyAccession(copy,entries[0].accession));
 copy.title='Copy '+entries[0].accession+' (source case '+entries[0].case_number+')';tools.append(copy);
 if(entries.length===1)tools.append(el('span','muted',entries[0].accession));
 else{const detail=el('details'),summary=el('summary','muted',entries.length+' accessions');detail.append(summary);for(const entry of entries){const line=el('div','lookup-tools');const one=button('Copy','plain',()=>copyAccession(one,entry.accession));line.append(el('span','','Case '+entry.case_number+' · '+entry.accession),one);detail.append(line);}tools.append(detail);}
 const mapped=new Set(lookupRows.filter(r=>r.confirmed&&validLookup(r)&&!lookupConflicts().has(r.case_number)).map(r=>r.case_number));
 const missing=members(c).filter(n=>!mapped.has(n));if(missing.length)tools.append(el('span','lookup-warning','Lookup missing: '+missing.join(', ')));
 row.append(tools);
}
function updateLookupCoverage(){
 {% if not exported_review | default(false) %}
 const matchesBatch=lookupMatchesReview(),conflicts=lookupConflicts(),source=new Set(matchesBatch?cases.flatMap(members):[]),valid=lookupRows.filter(r=>r.confirmed&&validLookup(r)&&!conflicts.has(r.case_number));
 $('lookup-count').textContent=valid.length?'· '+new Set(valid.map(r=>r.case_number)).size+' confirmed':'';
 const matched=new Set(valid.filter(r=>source.has(r.case_number)).map(r=>r.case_number));
 const missing=[...source].filter(n=>!matched.has(n));
 const extras=lookupRows.filter(r=>validLookup(r)&&source.size&&!source.has(r.case_number));
 $('lookup-coverage').textContent=(!matchesBatch?'Reports changed. Analyze the new batch before using its lookup or exporting. ':'')+(source.size?matched.size+' of '+source.size+' source cases matched. '+(missing.length?'Missing: '+missing.join(', ')+'. ':''):'')+(conflicts.size?'Conflicting cases: '+[...conflicts].join(', ')+'. ':'')+(extras.length?'Some lookup rows do not belong to this report batch. ':'')+(lookupRows.some(r=>!r.confirmed)?'Check each row against the screenshot, then confirm.':'');
 $('lookup-value').value=JSON.stringify(valid.map(r=>({case_number:r.case_number,accession:r.accession,confirmed:true})));
 $('export-review').disabled=ocrBusy||!matchesBatch||!cases.length||cases.some(c=>['queued','processing'].includes(c.status))||lookupRows.some(r=>!r.confirmed||!validLookup(r))||conflicts.size>0;
 {% endif %}
}
{% if not exported_review | default(false) %}
let lookupEpoch=0,ocrBusy=false,ocrWorker=null,ocrLoading=null,currentImage=null,marking=null,dragStart=null;
const lookupImages=[];
function paintLookup(){
 const canvas=$('lookup-canvas');if(!currentImage)return;const ctx=canvas.getContext('2d');canvas.width=currentImage.bitmap.width;canvas.height=currentImage.bitmap.height;ctx.drawImage(currentImage.bitmap,0,0);
 for(const [name,color] of [['caseColumn','#2689df'],['accessionColumn','#dba72a']]){const col=currentImage[name];if(!col)continue;ctx.fillStyle=color+'33';ctx.fillRect(col[0],0,col[1]-col[0],canvas.height);ctx.strokeStyle=color;ctx.lineWidth=2;ctx.strokeRect(col[0],1,col[1]-col[0],canvas.height-2);}
 if(Number.isFinite(currentImage.focusY)){ctx.strokeStyle='#e14c79';ctx.lineWidth=2;ctx.strokeRect(1,currentImage.focusY-9,canvas.width-2,18);}
}
function showLookupImage(img){currentImage=img;$('lookup-image').hidden=false;$('lookup-column-tools').hidden=false;const zoom=$('lookup-zoom').value;$('lookup-canvas').style.width=(zoom==='fit'?Math.min(img.bitmap.width*3,$('lookup-image').clientWidth):img.bitmap.width*Number(zoom))+'px';paintLookup();}
function lookupTable(){
 const conflicts=lookupConflicts();$('lookup-rows').replaceChildren();
 lookupRows.forEach((r,index)=>{
  const tr=el('tr'),n=el('input'),a=el('input'),check=el('input');n.type='text';n.inputMode='numeric';n.value=r.case_number||'';n.setAttribute('aria-label','Case number row '+(index+1));a.type='text';a.value=r.accession;a.autocomplete='off';a.spellcheck=false;a.setAttribute('aria-label','Accession row '+(index+1));check.type='checkbox';check.checked=!!r.confirmed;check.setAttribute('aria-label','Confirm row '+(index+1));check.disabled=!validLookup(r)||conflicts.has(r.case_number);
  const status=el('span',(!validLookup(r)||conflicts.has(r.case_number))?'lookup-warning':'muted',conflicts.has(r.case_number)?'Conflicting accession':!validLookup(r)?'Check case / accession':(r.source||'Manual')+(r.confidence!==undefined?' · OCR '+Math.round(r.confidence)+'%':''));
  const source=el('div');source.append(status);if(r.imageId){const reveal=()=>{const img=lookupImages.find(i=>i.id===r.imageId);if(!img)return;img.focusY=r.rowY;showLookupImage(img);const canvas=$('lookup-canvas'),scale=canvas.getBoundingClientRect().width/canvas.width;$('lookup-image').scrollTop=Math.max(0,r.rowY*scale-100);};source.append(button('View row','plain',reveal));n.addEventListener('focus',reveal);a.addEventListener('focus',reveal);}
  const changed=()=>{r.case_number=/^\d+$/.test(n.value.trim())?Number(n.value.trim()):null;r.accession=a.value.trim();r.confirmed=false;check.checked=false;const conflicts=lookupConflicts();for(const [i,row] of [...$('lookup-rows').children].entries()){const item=lookupRows[i],box=row.querySelector('[type=checkbox]');box.disabled=!validLookup(item)||conflicts.has(item.case_number);row.children[2].querySelector('span').textContent=conflicts.has(item.case_number)?'Conflicting accession':!validLookup(item)?'Check case / accession':item.confirmed?'Confirmed':'Check against screenshot';}updateReview();};
  n.addEventListener('input',changed);a.addEventListener('input',changed);
  check.addEventListener('change',()=>{r.confirmed=check.checked;updateReview();});
  for(const child of [n,a,source,check,button('Remove','plain',()=>{lookupRows.splice(index,1);lookupTable();updateReview();})]){const td=el('td');td.append(child);tr.append(td);}$('lookup-rows').append(tr);
 });updateLookupCoverage();
}
function clearLookup(){
 lookupEpoch++;lookupRows=[];for(const img of lookupImages)img.bitmap.close();lookupImages.length=0;currentImage=null;marking=null;
 if(ocrWorker){ocrWorker.terminate().catch(()=>{});ocrWorker=null;}
 ocrLoading=null;ocrBusy=false;$('lookup-files').value='';$('lookup-images').replaceChildren();$('lookup-canvas').width=1;$('lookup-canvas').height=1;$('lookup-image').hidden=true;$('lookup-column-tools').hidden=true;$('ocr-status').textContent='';lookupTable();
}
async function getOCR(epoch){
 if(ocrWorker)return ocrWorker;
 if(!ocrLoading)ocrLoading=(async()=>{
  if(!window.Tesseract)await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/ocr-assets/tesseract.min.js';script.onload=resolve;script.onerror=()=>{script.remove();reject(Error('runtime'));};document.head.append(script);});
  const base=new URL('/ocr-assets/',location.href).href;
  const worker=await window.Tesseract.createWorker('eng',1,{workerPath:base+'worker.min.js',corePath:base+'tesseract-core-lstm.wasm.js',langPath:base,workerBlobURL:false,cacheMethod:'none',logger:m=>{if(epoch===lookupEpoch&&m.status==='recognizing text')$('ocr-status').textContent='Reading screenshot… '+Math.round((m.progress||0)*100)+'%';}});
  if(epoch!==lookupEpoch){await worker.terminate();throw Error('cleared');}
  await worker.setParameters({tessedit_pageseg_mode:'6'});ocrWorker=worker;return worker;
 })().catch(error=>{ocrLoading=null;throw error;});
 return ocrLoading;
}
function imageLines(words){
 const lines=[];
 for(const w of [...words].sort((a,b)=>(a.bbox.y0+a.bbox.y1)-(b.bbox.y0+b.bbox.y1)||a.bbox.x0-b.bbox.x0)){
  const y=(w.bbox.y0+w.bbox.y1)/2,h=w.bbox.y1-w.bbox.y0;
  let line=lines.find(l=>Math.abs(l.y-y)<=Math.max(5,Math.min(l.height,h)*0.5));
  if(!line){line={y,height:h,words:[]};lines.push(line);}line.words.push(w);
 }
 for(const line of lines)line.words.sort((a,b)=>a.bbox.x0-b.bbox.x0);return lines;
}
function detectColumns(img){
 for(const line of imageLines(img.words)){
  const clean=w=>w.text.toLowerCase().replace(/[^a-z#]/g,'');const cw=line.words.find(w=>['case','case#','caseid'].includes(clean(w))),aw=line.words.find(w=>/^acc(?:ession)?(?:number|no|#)?$/.test(clean(w)));
  if(!aw)continue;
  if(!cw){
   if(line.words.length!==1)continue;
   // A two-column export often leaves the row-number header blank. Accept only
   // a clearly separated numeric column to the left of the named Accession.
   const numeric=img.words.filter(w=>/^\d{1,7}$/.test(w.text)&&w.bbox.y0>aw.bbox.y1&&w.bbox.x1<aw.bbox.x0);
   if(numeric.length>=3){const edge=Math.max(...numeric.map(w=>w.bbox.x1));if(edge<aw.bbox.x0){const boundary=(edge+aw.bbox.x0)/2;img.caseColumn=[0,boundary];img.accessionColumn=[boundary,img.bitmap.width];img.headerY=line.y+line.height/2;return true;}}
   continue;
  }
  if(cw===aw)continue;
  const bounds=word=>{const i=line.words.indexOf(word),center=w=>(w.bbox.x0+w.bbox.x1)/2;return [i? (center(line.words[i-1])+center(word))/2:0,i<line.words.length-1?(center(word)+center(line.words[i+1]))/2:img.bitmap.width];};
  img.caseColumn=bounds(cw);img.accessionColumn=bounds(aw);img.headerY=line.y+line.height/2;return true;
 }return false;
}
async function recognizeColumns(img,worker,epoch){
 const words=[];
 if(img.accessionColumn[1]-img.accessionColumn[0]<240){
  // Tiny table screenshots lose whole rows in page OCR. Segment by visible ink
  // in the accession column, then recognize each actual row and both columns.
  // Row positions are never substituted for unreadable case numbers.
  const probe=document.createElement('canvas'),left=Math.floor(img.accessionColumn[0]),width=Math.ceil(img.accessionColumn[1])-left;probe.width=width;probe.height=img.bitmap.height;const pc=probe.getContext('2d');pc.drawImage(img.bitmap,left,0,width,img.bitmap.height,0,0,width,img.bitmap.height);const data=pc.getImageData(0,0,width,img.bitmap.height).data,bands=[];let start=null,last=-1;
  for(let y=0;y<img.bitmap.height;y++){let ink=0;for(let x=0;x<width;x++){const i=(y*width+x)*4;if((data[i]+data[i+1]+data[i+2])/3<140)ink++;}if(ink>=2){if(start===null)start=y;last=y;}else if(start!==null&&y-last>2){if(last-start>=3)bands.push([start,last]);start=null;}}
  if(start!==null&&last-start>=3)bands.push([start,last]);probe.width=1;probe.height=1;
  if(bands.length>260)throw Error('rows');
  for(const [top,bottom] of bands){
   if(top<=(img.headerY||0))continue;
   if(epoch!==lookupEpoch)return;
   for(const [name,alphabet] of [['caseColumn','0123456789'],['accessionColumn','0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-']]){
    const [x0,x1]=img[name],y0=Math.max(0,top-2),h=Math.min(img.bitmap.height-y0,bottom-top+5),scale=4,canvas=document.createElement('canvas');canvas.width=Math.ceil((x1-x0)*scale)+16;canvas.height=h*scale+16;const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img.bitmap,x0,y0,x1-x0,h,8,8,(x1-x0)*scale,h*scale);
    await worker.setParameters({tessedit_char_whitelist:alphabet,tessedit_pageseg_mode:name==='caseColumn'?'13':'7'});const {data}=await worker.recognize(canvas,{}, {blocks:true,text:true});canvas.width=1;canvas.height=1;
    for(const w of (data.blocks||[]).flatMap(b=>(b.paragraphs||[]).flatMap(p=>(p.lines||[]).flatMap(l=>l.words||[]))))words.push({...w,bbox:{x0:(w.bbox.x0-8)/scale+x0,x1:(w.bbox.x1-8)/scale+x0,y0:(w.bbox.y0-8)/scale+y0,y1:(w.bbox.y1-8)/scale+y0}});
   }
  }
  if(epoch!==lookupEpoch)return;img.words=words;readImageRows(img);return;
 }
 for(const [name,alphabet] of [['caseColumn','0123456789'],['accessionColumn','0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-']]){
  const [left,right]=img[name],width=right-left;if(width<3)throw Error('column');
  const scale=Math.min(4,Math.sqrt(16000000/(width*img.bitmap.height))),canvas=document.createElement('canvas');canvas.width=Math.round(width*scale);canvas.height=Math.round(img.bitmap.height*scale);const ctx=canvas.getContext('2d');ctx.drawImage(img.bitmap,left,0,width,img.bitmap.height,0,0,canvas.width,canvas.height);
  const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);for(let i=0;i<pixels.data.length;i+=4){const v=(pixels.data[i]+pixels.data[i+1]+pixels.data[i+2])/3<140?0:255;pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=v;pixels.data[i+3]=255;}ctx.putImageData(pixels,0,0);
  await worker.setParameters({tessedit_char_whitelist:alphabet,tessedit_pageseg_mode:'6'});
  const {data}=await worker.recognize(canvas,{}, {blocks:true,text:true});canvas.width=1;canvas.height=1;
  if(epoch!==lookupEpoch)return;
  for(const w of (data.blocks||[]).flatMap(b=>(b.paragraphs||[]).flatMap(p=>(p.lines||[]).flatMap(l=>l.words||[]))))words.push({...w,bbox:{x0:w.bbox.x0/scale+left,x1:w.bbox.x1/scale+left,y0:w.bbox.y0/scale,y1:w.bbox.y1/scale}});
 }
 if(epoch!==lookupEpoch)return;img.words=words;readImageRows(img);
}
function readImageRows(img){
 if(!img.caseColumn||!img.accessionColumn){$('ocr-status').textContent='Mark the case-number and accession columns on the screenshot, then read marked columns.';return;}
 if(Math.max(img.caseColumn[0],img.accessionColumn[0])<Math.min(img.caseColumn[1],img.accessionColumn[1])){$('ocr-status').textContent='The marked columns overlap. Mark two separate columns.';return;}
 lookupRows=lookupRows.filter(r=>r.imageId!==img.id);let found=0;
 const within=(w,col)=>{const x=(w.bbox.x0+w.bbox.x1)/2;return x>=col[0]&&x<=col[1];};
 for(const line of imageLines(img.words)){
  if(line.y<=(img.headerY||0))continue;
  const ns=line.words.filter(w=>within(w,img.caseColumn)),as=line.words.filter(w=>within(w,img.accessionColumn));
  const n=ns.map(w=>w.text).join(' ').trim(),accession=as.map(w=>w.text).join(' ').trim();
  const number=/^\d{1,7}$/.test(n)&&Number(n)>0?Number(n):null;
  if(!number&&/^(?:acc(?:ession)?(?:number|no)?|case|number|no)$/i.test(accession.replace(/[ #._-]/g,'')))continue;
  if(!number&&!/^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/.test(accession))continue;
  const candidate={case_number:number,accession,confirmed:false,source:img.label,imageId:img.id,rowY:line.y,confidence:Math.min(...[...ns,...as].map(w=>w.confidence??0))};
  if(!number||!lookupRows.some(r=>r.case_number===candidate.case_number&&r.accession===candidate.accession))lookupRows.push(candidate);
  found++;
 }
 lookupTable();updateReview();$('ocr-status').textContent=found?'Read '+found+' rows. Check every case number and accession against the screenshot and confirm each match.'+(img.bitmap.width<500?' Small source image: a larger original capture can improve recognition.':''):'No numbered rows recognized. Adjust the marked columns or add rows manually.';
}
async function addLookupImages(files){
 if(ocrBusy){$('ocr-status').textContent='Wait for the current screenshots to finish.';return;}
 if(lookupImages.length+files.length>20){$('ocr-status').textContent='Use at most 20 screenshots per batch.';return;}
 const epoch=lookupEpoch;ocrBusy=true;marking=null;updateLookupCoverage();
 try{
  for(const file of files){
   if(epoch!==lookupEpoch)return;
   if(!/^image\/(png|jpeg|webp)$/.test(file.type)||file.size>15*1024*1024)throw Error('image');
   const bitmap=await createImageBitmap(file);if(bitmap.width*bitmap.height>16000000){bitmap.close();throw Error('image');}
   if(epoch!==lookupEpoch){bitmap.close();return;}
   const img={id:crypto.randomUUID(),bitmap,label:'Screenshot '+(lookupImages.length+1),words:[]};lookupImages.push(img);
   const choose=button(img.label,'',()=>showLookupImage(img));$('lookup-images').append(choose);showLookupImage(img);
   $('ocr-status').textContent='Loading local OCR…';const worker=await getOCR(epoch);if(epoch!==lookupEpoch)return;
   // A canvas supplies only image pixels to the browser worker. No screenshot request is made.
   const scale=Math.min(4,Math.max(1,1600/bitmap.width),Math.sqrt(16000000/(bitmap.width*bitmap.height)));
   const canvas=document.createElement('canvas');canvas.width=Math.round(bitmap.width*scale);canvas.height=Math.round(bitmap.height*scale);canvas.getContext('2d').drawImage(bitmap,0,0,canvas.width,canvas.height);
   const ctx=canvas.getContext('2d'),pixels=ctx.getImageData(0,0,canvas.width,canvas.height);for(let i=0;i<pixels.data.length;i+=4){const v=(pixels.data[i]+pixels.data[i+1]+pixels.data[i+2])/3<140?0:255;pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=v;pixels.data[i+3]=255;}ctx.putImageData(pixels,0,0);
   await worker.setParameters({tessedit_char_whitelist:'',tessedit_pageseg_mode:'6'});
   const {data}=await worker.recognize(canvas,{}, {blocks:true,text:true});canvas.width=1;canvas.height=1;
   if(epoch!==lookupEpoch)return;
   img.words=(data.blocks||[]).flatMap(b=>(b.paragraphs||[]).flatMap(p=>(p.lines||[]).flatMap(l=>l.words||[])));
   if(!img.words.length&&Array.isArray(data.words))img.words=data.words;
   if(scale!==1)img.words=img.words.map(w=>({...w,bbox:Object.fromEntries(Object.entries(w.bbox).map(([k,v])=>[k,v/scale]))}));
   if(detectColumns(img))await recognizeColumns(img,worker,epoch);else $('ocr-status').textContent='Screenshot read. Mark the case-number and accession columns, then read marked columns.';
   showLookupImage(img);
  }
 }catch{if(epoch===lookupEpoch)$('ocr-status').textContent='Could not read this screenshot. Check the image size/format or retry. You can add and confirm rows manually.';}
 finally{if(epoch===lookupEpoch){ocrBusy=false;$('lookup-files').value='';updateLookupCoverage();}}
}
$('lookup-files').addEventListener('change',()=>addLookupImages([...$('lookup-files').files]));
$('lookup-zoom').addEventListener('change',()=>{if(currentImage)showLookupImage(currentImage);});
$('report-text').addEventListener('input',updateReview);
$('lookup-panel').addEventListener('paste',event=>{const files=[...(event.clipboardData?.files||[])].filter(f=>f.type.startsWith('image/'));if(files.length){event.preventDefault();addLookupImages(files);}});
$('lookup-paste').addEventListener('click',async()=>{try{if(!navigator.clipboard?.read)throw Error();const items=await navigator.clipboard.read(),files=[];for(const item of items)for(const type of item.types)if(type.startsWith('image/')){files.push(await item.getType(type));break;}if(!files.length)throw Error();await addLookupImages(files);}catch{$('ocr-status').textContent='Click inside this lookup section and press Ctrl+V, or choose an image file.';}});
$('lookup-add').addEventListener('click',()=>{lookupRows.push({case_number:null,accession:'',confirmed:false,source:'Manual'});lookupTable();});
$('lookup-clear').addEventListener('click',()=>{clearLookup();updateReview();});
for(const [id,column] of [['mark-case','caseColumn'],['mark-accession','accessionColumn']])$(id).addEventListener('click',()=>{if(ocrBusy){$('ocr-status').textContent='Wait for screenshot recognition to finish before marking columns.';return;}marking=column;$('ocr-status').textContent='Drag across the full width of the '+(column==='caseColumn'?'case-number':'accession')+' column.';});
$('read-columns').addEventListener('click',async()=>{if(!currentImage||ocrBusy)return;if(!currentImage.caseColumn||!currentImage.accessionColumn){readImageRows(currentImage);return;}if(Math.max(currentImage.caseColumn[0],currentImage.accessionColumn[0])<Math.min(currentImage.caseColumn[1],currentImage.accessionColumn[1])){$('ocr-status').textContent='The marked columns overlap. Mark two separate columns.';return;}const epoch=lookupEpoch;ocrBusy=true;marking=null;updateLookupCoverage();try{await recognizeColumns(currentImage,await getOCR(epoch),epoch);}catch{if(epoch===lookupEpoch)$('ocr-status').textContent='Could not read these columns. Adjust the selection or add rows manually.';}finally{if(epoch===lookupEpoch){ocrBusy=false;updateLookupCoverage();}}});
$('lookup-canvas').addEventListener('pointerdown',event=>{if(!marking||!currentImage)return;const canvas=$('lookup-canvas'),rect=canvas.getBoundingClientRect();dragStart=(event.clientX-rect.left)*canvas.width/rect.width;canvas.setPointerCapture(event.pointerId);});
$('lookup-canvas').addEventListener('pointerup',event=>{if(dragStart===null||!marking||!currentImage)return;const canvas=$('lookup-canvas'),rect=canvas.getBoundingClientRect(),end=(event.clientX-rect.left)*canvas.width/rect.width;currentImage[marking]=[Math.max(0,Math.min(dragStart,end)),Math.min(canvas.width,Math.max(dragStart,end))];currentImage.headerY=0;dragStart=null;marking=null;paintLookup();});
$('export-review').addEventListener('click',async()=>{
 const target=$('export-review');target.disabled=true;$('export-status').textContent='Preparing clinical review…';
 try{
  if(ocrBusy||!lookupMatchesReview())throw Error('batch');
  const selected=$('export-filtered').checked?new Set([...document.querySelectorAll('#case-list .case')].map(r=>Number(r.id.slice(4)))):null;
  const records=cases.filter((c,i)=>!selected||selected.has(i)).map(c=>({source_numbers:members(c),resident_report:c.resident_report,attending_report:c.attending_report,review_mode:c.review_mode,exam_label:c.exam_label,title:c.title,status:c.status,revisions:revisions(c)}));
  const lookup=lookupRows.filter(r=>r.confirmed&&validLookup(r)).map(r=>({case_number:r.case_number,accession:r.accession,confirmed:true}));
  const response=await fetch('/export-review',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('[name=csrf_token]').value},body:JSON.stringify({cases:records,lookup,review_mode:reviewMode,theme:themeChoice,combined_view:combinedView,show_report_wording:showReportWording})});
  if(!response.ok||!response.headers.get('content-type')?.includes('text/html')||response.redirected)throw Error();
  const blob=await response.blob(),url=URL.createObjectURL(blob),link=el('a');link.href=url;link.download='clinical-review.html';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);$('export-status').textContent='Review downloaded. Contains PHI—keep it within approved systems.';
 }catch{$('export-status').textContent='Export could not be completed. Check that analysis and lookup confirmation are finished, or refresh your sign-in.';}
 finally{updateLookupCoverage();}
});
lookupTable();
{% endif %}

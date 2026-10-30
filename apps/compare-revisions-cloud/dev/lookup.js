// Valid, batch-local mappings are accepted by Analyze/Download; no per-row approval.
let lookupRows=JSON.parse($('lookup-data').textContent||'[]');
const lookupSourceText=$('report-text')?.value;
const lookupMatchesReview=()=>exportedReview||!cases.length||$('report-text').value===lookupSourceText;
const validLookup=r=>!r.caseIssue&&!r.accessionIssue&&Number.isInteger(r.case_number)&&r.case_number>0&&r.case_number<=1000000&&typeof r.accession==='string'&&/^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/.test(r.accession);
function lookupConflicts(){
 const seen=new Map(),conflicts=new Set();
 for(const r of lookupRows){if(!validLookup(r))continue;if(seen.has(r.case_number)&&seen.get(r.case_number)!==r.accession)conflicts.add(r.case_number);seen.set(r.case_number,r.accession);}
 return conflicts;
}
function caseAccessions(c){if(!lookupMatchesReview())return [];const conflicts=lookupConflicts();return [...new Map(lookupRows.filter(r=>validLookup(r)&&!conflicts.has(r.case_number)&&members(c).includes(r.case_number)).sort((a,b)=>a.case_number-b.case_number).map(r=>[r.accession,r])).values()];}
const accessionCopyTimers=new WeakMap();
async function copyAccession(target,value){
 const iconOnly=target.classList.contains('case-copy-accession'),original=iconOnly?'':(target.dataset.copyLabel||target.textContent);
 if(!iconOnly)target.dataset.copyLabel=original;
 clearTimeout(accessionCopyTimers.get(target));
 let message;
 try{
  try{if(!navigator.clipboard?.writeText)throw Error();await navigator.clipboard.writeText(value);}
  catch{const box=el('textarea');box.value=value;box.setAttribute('aria-label','Accession to copy');box.style.cssText='position:fixed;left:-9999px;top:0';document.body.append(box);box.select();let ok=false;try{ok=document.execCommand('copy');}finally{box.remove();target.focus({preventScroll:true});}if(!ok)throw Error();}
  message='Accession copied';
 }catch{message='Copy unavailable';}
 $('announcement').textContent=message==='Accession copied'?message:'Copy unavailable. Expand the case to select an accession and press Ctrl+C.';
 if(iconOnly){target.querySelector('.accession-copy-feedback').textContent=message;target.classList.add('show-copy-feedback');}
 else target.textContent=message;
 accessionCopyTimers.set(target,setTimeout(()=>{if(iconOnly)target.classList.remove('show-copy-feedback');else target.textContent=original;},1400));
}
function accessionIcon(c){
 const entries=caseAccessions(c);if(!entries.length)return null;
 const copy=button('','copy-accession case-copy-accession',()=>copyAccession(copy,entries[0].accession));
 copy.title='Copy accession';copy.setAttribute('aria-label','Copy accession for '+(members(c).length>1?'cases ':'case ')+caseLabel(c));
 copy.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3"/></svg><span class="accession-copy-feedback" aria-hidden="true"></span>';
 return copy;
}
function appendAccessionTools(body,c){
 const entries=caseAccessions(c);if(!entries.length){if(lookupRows.length){const missing=el('div','accession-tools');missing.append(el('span','muted','Accession not attached'));body.append(missing);}return;}
 const tools=el('div','accession-tools');
 for(const entry of entries){const line=el('div','accession-line'),copy=button('Copy accession','copy-accession',()=>copyAccession(copy,entry.accession));copy.title='Copy '+entry.accession+' (source case '+entry.case_number+')';line.append(copy,el('span','accession-value',(entries.length>1?'Case '+entry.case_number+' · ':'')+entry.accession));tools.append(line);}
 const mapped=new Set(lookupRows.filter(r=>validLookup(r)&&!lookupConflicts().has(r.case_number)).map(r=>r.case_number));
 const missing=members(c).filter(n=>!mapped.has(n));if(missing.length)tools.append(el('span','lookup-warning','Lookup missing: '+missing.join(', ')));
 body.append(tools);
}
function updateLookupCoverage(){
 {% if not exported_review | default(false) %}
 const matchesBatch=lookupMatchesReview(),conflicts=lookupConflicts(),source=new Set(matchesBatch?cases.flatMap(members):[]),valid=lookupRows.filter(r=>validLookup(r)&&!conflicts.has(r.case_number));
 $('lookup-count').textContent=valid.length?'· '+new Set(valid.map(r=>r.case_number)).size+' ready':'';
 const matched=new Set(valid.filter(r=>source.has(r.case_number)).map(r=>r.case_number));
 const missing=[...source].filter(n=>!matched.has(n));
 const extras=lookupRows.filter(r=>validLookup(r)&&source.size&&!source.has(r.case_number));
 $('lookup-coverage').textContent=(!matchesBatch?'Reports changed. Analyze the new batch before using its lookup or exporting. ':'')+(source.size?matched.size+' of '+source.size+' source cases matched. '+(missing.length?'Missing: '+missing.join(', ')+'. ':''):'')+(conflicts.size?'Duplicate case numbers with different accessions: '+[...conflicts].join(', ')+'. Check the case-number OCR. ':'')+(extras.length?'Some lookup rows do not belong to this report batch. ':'')+(lookupRows.some(r=>r.caseIssue)?'Some case numbers may be incomplete. Correct them or use a verified consecutive range. ':'');
 $('lookup-value').value=JSON.stringify(valid.map(r=>({case_number:r.case_number,accession:r.accession,confirmed:true})));
 $('export-review').disabled=ocrBusy||!matchesBatch||!cases.length||cases.some(c=>['queued','processing'].includes(c.status))||lookupRows.some(r=>!validLookup(r))||conflicts.size>0;
 {% endif %}
}
{% if not exported_review | default(false) %}
let lookupEpoch=0,ocrBusy=false,ocrWorker=null,ocrLoading=null,currentImage=null;
const lookupImages=[];
function paintLookup(){
 const canvas=$('lookup-canvas');if(!currentImage)return;const ctx=canvas.getContext('2d');canvas.width=currentImage.bitmap.width;canvas.height=currentImage.bitmap.height;ctx.drawImage(currentImage.bitmap,0,0);
 for(const [name,color] of [['caseColumn','#2689df'],['accessionColumn','#dba72a']]){const col=currentImage[name];if(!col)continue;ctx.fillStyle=color+'33';ctx.fillRect(col[0],0,col[1]-col[0],canvas.height);ctx.strokeStyle=color;ctx.lineWidth=2;ctx.strokeRect(col[0],1,col[1]-col[0],canvas.height-2);}
 if(Number.isFinite(currentImage.focusY)){ctx.strokeStyle='#e14c79';ctx.lineWidth=2;ctx.strokeRect(1,currentImage.focusY-9,canvas.width-2,18);}
}
function showLookupImage(img){if(currentImage!==img){$('lookup-range-first').value='';$('lookup-range-last').value='';$('lookup-range-checked').checked=false;$('lookup-range-status').textContent='';}currentImage=img;$('lookup-image').hidden=false;$('lookup-column-tools').hidden=false;$('lookup-range-tools').hidden=false;const zoom=$('lookup-zoom').value;$('lookup-canvas').style.width=(zoom==='fit'?Math.min(img.bitmap.width*3,$('lookup-image').clientWidth):img.bitmap.width*Number(zoom))+'px';paintLookup();}
function lookupRowMessage(r,conflicts){return r.caseIssue||r.accessionIssue|| (conflicts.has(r.case_number)?'Duplicate case '+r.case_number+' · check OCR':!validLookup(r)?'Check case / accession':(r.source||'Manual')+(r.originalAccession?' · OCR characters corrected':'')+(r.numberSource==='sequence'?' · case repaired from '+(r.originalCase??'unread'):r.numberSource==='range'?' · verified range':r.confidence!==undefined?' · read score '+Math.round(r.confidence):''));}
function lookupTable(){
 const conflicts=lookupConflicts();$('lookup-rows').replaceChildren();
 lookupRows.forEach((r,index)=>{
  const tr=el('tr'),n=el('input'),a=el('input');n.type='text';n.inputMode='numeric';n.value=r.case_number||'';n.setAttribute('aria-label','Case number row '+(index+1));a.type='text';a.value=r.accession;a.autocomplete='off';a.spellcheck=false;if(r.originalAccession){a.classList.add('lookup-repaired');a.title='OCR read '+r.originalAccession+'. Context-corrected to '+r.accession+' (two letters, then digits).';}a.setAttribute('aria-label','Accession row '+(index+1));
  if(r.numberSource==='sequence'){n.classList.add('lookup-repaired');n.title='OCR read '+(r.originalCase??'no case number')+'. Suggested '+r.case_number+' from consistent consecutive source numbers. Compare with the source if needed.';}
  const status=el('span',(!validLookup(r)||conflicts.has(r.case_number))?'lookup-warning':'muted',lookupRowMessage(r,conflicts));status.title='A duplicate case warning means the lookup assigns different accessions to one case number. OCR read scores are engine confidence, not measured accuracy.';
  const source=el('div');source.append(status);if(r.imageId){const reveal=()=>{const img=lookupImages.find(i=>i.id===r.imageId);if(!img)return;img.focusY=r.rowY;showLookupImage(img);const canvas=$('lookup-canvas'),scale=canvas.getBoundingClientRect().width/canvas.width;$('lookup-image').scrollTop=Math.max(0,r.rowY*scale-100);};source.append(button('View row','plain',reveal));n.addEventListener('focus',reveal);a.addEventListener('focus',reveal);}
  const changed=caseEdited=>{r.case_number=/^\d+$/.test(n.value.trim())?Number(n.value.trim()):null;r.accession=a.value.trim();if(!caseEdited){r.accessionIssue='';r.originalAccession=null;}if(caseEdited){r.caseIssue='';r.numberSource='manual';}r.confirmed=false;const conflicts=lookupConflicts();for(const [i,row] of [...$('lookup-rows').children].entries()){const item=lookupRows[i],status=row.children[2].querySelector('span');status.className=(!validLookup(item)||conflicts.has(item.case_number))?'lookup-warning':'muted';status.textContent=lookupRowMessage(item,conflicts);}updateReview();};
  n.addEventListener('input',()=>changed(true));a.addEventListener('input',()=>changed(false));
  for(const child of [n,a,source,button('Remove','plain',()=>{lookupRows.splice(index,1);lookupTable();updateReview();})]){const td=el('td');td.append(child);tr.append(td);}$('lookup-rows').append(tr);
 });updateLookupCoverage();
}
function clearLookup(){
 lookupEpoch++;lookupRows=[];for(const img of lookupImages)img.bitmap.close();lookupImages.length=0;currentImage=null;
 if(ocrWorker){ocrWorker.terminate().catch(()=>{});ocrWorker=null;}
 ocrLoading=null;ocrBusy=false;$('lookup-images').replaceChildren();$('lookup-canvas').width=1;$('lookup-canvas').height=1;$('lookup-image').hidden=true;$('lookup-column-tools').hidden=true;$('lookup-range-tools').hidden=true;$('lookup-range-status').textContent='';$('ocr-status').textContent='';lookupTable();
}
async function getOCR(epoch){
 if(ocrWorker)return ocrWorker;
 if(!ocrLoading)ocrLoading=(async()=>{
  if(!window.Tesseract)await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/ocr-assets/tesseract.min.js';script.onload=resolve;script.onerror=()=>{script.remove();reject(Error('runtime'));};document.head.append(script);});
  const base=new URL('/ocr-assets/',location.href).href;
  const worker=await window.Tesseract.createWorker('eng',1,{workerPath:base+'worker.min.js',corePath:base+'tesseract-core-lstm.wasm.js',langPath:base,workerBlobURL:false,cacheMethod:'none'});
  if(epoch!==lookupEpoch){await worker.terminate();throw Error('cleared');}
  await worker.setParameters({tessedit_pageseg_mode:'6'});ocrWorker=worker;return worker;
 })().catch(error=>{ocrLoading=null;throw error;});
 return ocrLoading;
}
function showOCRProgress(img,phase,completed,total,epoch){
 // Worker percentages restart for every recognize() call. Report completed
 // rows/columns instead, so the visible percentage never resets within a pass.
 if(epoch!==lookupEpoch||!ocrBusy)return;
 $('ocr-status').textContent=img.label+' · '+phase+'… '+completed+' of '+total+' ('+Math.floor(completed/total*100)+'%)';
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
function normalizeAccession(text){
 const value=text.trim().replace(/\s+/g,'').toUpperCase(),match=value.match(/^([A-Z07]{2})([0-9O]{6,14})$/);
 if(!match)return {value,issue:'Check accession: expected two letters followed by digits'};
 const prefix=['0T','07','O7'].includes(match[1])?'OT':match[1];
 if(!/^[A-Z]{2}$/.test(prefix))return {value,issue:'Check accession prefix'};
 const normalized=prefix+match[2].replace(/O/g,'0');
 return {value:normalized,issue:'',original:normalized!==value?value:null};
}
function detectColumns(img){
 const lines=imageLines(img.words),clean=w=>w.text.toLowerCase().replace(/[^a-z#]/g,'');
 let header=null;
 for(const line of lines){const aw=line.words.find(w=>/^acc(?:ession)?(?:number|no|#)?$/.test(clean(w)));if(aw){header={line,word:aw};break;}}
 const pairs=[];
 for(const line of lines){
  const words=line.words;
  for(let i=0;i<words.length;i++){
   let aw=words[i];
   if(/^[A-Za-z07]{2}$/.test(aw.text)&&/^[0-9O]{6,14}$/.test(words[i+1]?.text||'')){const next=words[i+1];aw={text:aw.text+next.text,bbox:{x0:aw.bbox.x0,x1:next.bbox.x1,y0:Math.min(aw.bbox.y0,next.bbox.y0),y1:Math.max(aw.bbox.y1,next.bbox.y1)}};}
   if(normalizeAccession(aw.text).issue)continue;
   const candidates=words.filter(w=>/^\d{1,4}$/.test(w.text)&&Number(w.text)>0&&w.bbox.x1<aw.bbox.x0);
   if(candidates.length!==1)continue;
   pairs.push({n:candidates[0],a:aw});
  }
 }
 // Require multiple stable rows and at least one visibly alphabetic prefix.
 // A numeric-only MRN column is not sufficient evidence for an accession.
 if(pairs.length>=3&&pairs.some(p=>/[A-Za-z]/.test(p.a.text.slice(0,2)))){
  const starts=pairs.map(p=>p.a.bbox.x0).sort((a,b)=>a-b),median=starts[Math.floor(starts.length/2)],tolerance=Math.max(5,img.bitmap.width*.05);
  const stable=pairs.filter(p=>Math.abs(p.a.bbox.x0-median)<=tolerance);
  if(stable.length>=3&&stable.length/pairs.length>=.8){
   const edge=Math.max(...stable.map(p=>p.n.bbox.x1)),left=Math.min(...stable.map(p=>p.a.bbox.x0));
   if(edge<left){const margin=Math.max(2,Math.min((left-edge)/3,Math.max(...stable.map(p=>p.n.bbox.y1-p.n.bbox.y0))/2));img.caseColumn=[Math.max(0,Math.floor(Math.min(...stable.map(p=>p.n.bbox.x0))-margin)),Math.ceil(edge+margin)];img.accessionColumn=[Math.max(0,Math.floor(left-margin)),img.bitmap.width];img.headerY=header?header.word.bbox.y1:0;return true;}
  }
 }
 // Preserve support for an explicitly labeled, simple two-column table even
 // when the page pass missed many rows. Other layouts are not guessed.
 if(header&&header.line.words.length<=2){
  const numbers=img.words.filter(w=>/^\d{1,4}$/.test(w.text)&&w.bbox.y0>header.word.bbox.y1&&w.bbox.x1<header.word.bbox.x0);
  if(numbers.length>=3){const edge=Math.max(...numbers.map(w=>w.bbox.x1));if(edge<header.word.bbox.x0){const boundary=(edge+header.word.bbox.x0)/2;img.caseColumn=[0,boundary];img.accessionColumn=[boundary,img.bitmap.width];img.headerY=header.word.bbox.y1;return true;}}
 }
 return false;
}
function markAccessionLengths(rows){
 const lengths=rows.filter(r=>!r.accessionIssue&&/^[A-Z]{2}\d+$/.test(r.accession)).map(r=>r.accession.length-2),counts=new Map();
 for(const n of lengths)counts.set(n,(counts.get(n)||0)+1);
 const [expected,count]=[...counts].sort((a,b)=>b[1]-a[1])[0]||[];
 if(lengths.length<6||count/lengths.length<.8)return;
 for(const r of rows)if(!r.accessionIssue&&r.accession.length-2!==expected)r.accessionIssue='Check accession length: most rows have '+expected+' digits';
}
async function recognizeColumns(img,worker,epoch){
 const words=[];
 img.caseChecks=[];
 if(img.accessionColumn[1]-img.accessionColumn[0]<240){
  // Tiny table screenshots lose whole rows in page OCR. Segment by visible ink
  // in the accession column, then recognize each actual row and both columns.
  // Keep actual row positions; sequence repair runs only after OCR validation.
  const probe=document.createElement('canvas'),left=Math.floor(img.accessionColumn[0]),width=Math.ceil(img.accessionColumn[1])-left;probe.width=width;probe.height=img.bitmap.height;const pc=probe.getContext('2d');pc.drawImage(img.bitmap,left,0,width,img.bitmap.height,0,0,width,img.bitmap.height);const data=pc.getImageData(0,0,width,img.bitmap.height).data,bands=[];let start=null,last=-1;
  for(let y=0;y<img.bitmap.height;y++){let ink=0;for(let x=0;x<width;x++){const i=(y*width+x)*4;if((data[i]+data[i+1]+data[i+2])/3<140)ink++;}if(ink>=2){if(start===null)start=y;last=y;}else if(start!==null&&y-last>2){if(last-start>=3)bands.push([start,last]);start=null;}}
  if(start!==null&&last-start>=3)bands.push([start,last]);probe.width=1;probe.height=1;
  if(bands.length>260)throw Error('rows');
  const digits=document.createElement('canvas'),digitLeft=Math.floor(img.caseColumn[0]),digitWidth=Math.ceil(img.caseColumn[1])-digitLeft;digits.width=digitWidth;digits.height=img.bitmap.height;const dc=digits.getContext('2d');dc.drawImage(img.bitmap,digitLeft,0,digitWidth,img.bitmap.height,0,0,digitWidth,img.bitmap.height);const digitPixels=dc.getImageData(0,0,digitWidth,img.bitmap.height).data;
  const rows=bands.filter(([top])=>top>(img.headerY||0));
  if(rows.length)showOCRProgress(img,'Reading rows',0,rows.length,epoch);
  for(const [rowIndex,[top,bottom]] of rows.entries()){
   if(epoch!==lookupEpoch)return;
   // A missing thin '1' can still produce a valid integer. Count separated ink
   // components to flag a shorter reading. This check never supplies a digit.
   const components=[];let begin=null,lastX=0;
   for(let x=0;x<digitWidth;x++){let ink=false;for(let y=Math.max(0,top-2);y<=Math.min(img.bitmap.height-1,bottom+2);y++){const i=(y*digitWidth+x)*4;if(Math.min(digitPixels[i],digitPixels[i+1],digitPixels[i+2])<140){ink=true;break;}}if(ink){if(begin===null)begin=x;lastX=x;}else if(begin!==null){components.push(lastX-begin+1);begin=null;}}
   if(begin!==null)components.push(lastX-begin+1);
   if(components.length&&components.length<=7&&components.every(w=>w<=bottom-top+5))img.caseChecks.push({y:(top+bottom)/2,digits:components.length});
   for(const [name,alphabet] of [['caseColumn','0123456789'],['accessionColumn','0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-']]){
    const [x0,x1]=img[name],y0=Math.max(0,top-2),h=Math.min(img.bitmap.height-y0,bottom-top+5),scale=4,canvas=document.createElement('canvas');canvas.width=Math.ceil((x1-x0)*scale)+16;canvas.height=h*scale+16;const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img.bitmap,x0,y0,x1-x0,h,8,8,(x1-x0)*scale,h*scale);
    await worker.setParameters({tessedit_char_whitelist:alphabet,tessedit_pageseg_mode:name==='caseColumn'?'13':'7'});const {data}=await worker.recognize(canvas,{}, {blocks:true,text:true});canvas.width=1;canvas.height=1;
    for(const w of (data.blocks||[]).flatMap(b=>(b.paragraphs||[]).flatMap(p=>(p.lines||[]).flatMap(l=>l.words||[]))))words.push({...w,bbox:{x0:(w.bbox.x0-8)/scale+x0,x1:(w.bbox.x1-8)/scale+x0,y0:(w.bbox.y0-8)/scale+y0,y1:(w.bbox.y1-8)/scale+y0}});
   }
   showOCRProgress(img,'Reading rows',rowIndex+1,rows.length,epoch);
  }
  digits.width=1;digits.height=1;
  if(epoch!==lookupEpoch)return;img.words=words;readImageRows(img);return;
 }
 let completedColumns=0;showOCRProgress(img,'Reading columns',0,2,epoch);
 for(const [name,alphabet] of [['caseColumn','0123456789'],['accessionColumn','0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-']]){
  const [left,right]=img[name],width=right-left;if(width<3)throw Error('column');
  const heights=img.words.map(w=>w.bbox.y1-w.bbox.y0).filter(h=>h>0).sort((a,b)=>a-b),typical=heights[Math.floor(heights.length/2)]||10;
  const scale=Math.min(4,Math.max(1,40/typical),Math.sqrt(16000000/(width*img.bitmap.height))),canvas=document.createElement('canvas');canvas.width=Math.round(width*scale);canvas.height=Math.round(img.bitmap.height*scale);const ctx=canvas.getContext('2d');ctx.drawImage(img.bitmap,left,0,width,img.bitmap.height,0,0,canvas.width,canvas.height);
  await worker.setParameters({tessedit_char_whitelist:alphabet,tessedit_pageseg_mode:'6'});
  const {data}=await worker.recognize(canvas,{}, {blocks:true,text:true});canvas.width=1;canvas.height=1;
  if(epoch!==lookupEpoch)return;
  for(const w of (data.blocks||[]).flatMap(b=>(b.paragraphs||[]).flatMap(p=>(p.lines||[]).flatMap(l=>l.words||[]))))words.push({...w,bbox:{x0:w.bbox.x0/scale+left,x1:w.bbox.x1/scale+left,y0:w.bbox.y0/scale,y1:w.bbox.y1/scale}});
  showOCRProgress(img,'Reading columns',++completedColumns,2,epoch);
 }
 if(epoch!==lookupEpoch)return;img.words=words;readImageRows(img);
}
function readImageRows(img){
 if(!img.caseColumn||!img.accessionColumn){$('ocr-status').textContent='Could not identify the columns. Paste a clearer screenshot cropped to case numbers and accessions, or add rows manually.';return;}
 if(Math.max(img.caseColumn[0],img.accessionColumn[0])<Math.min(img.caseColumn[1],img.accessionColumn[1])){$('ocr-status').textContent='The detected columns overlap. Paste a clearer crop with separate case-number and accession columns.';return;}
 lookupRows=lookupRows.filter(r=>r.imageId!==img.id);img.rows=[];let found=0;
 const within=(w,col)=>{const x=(w.bbox.x0+w.bbox.x1)/2;return x>=col[0]&&x<=col[1];};
 for(const line of imageLines(img.words)){
  if(line.y<=(img.headerY||0))continue;
  const ns=line.words.filter(w=>within(w,img.caseColumn)),as=line.words.filter(w=>within(w,img.accessionColumn));
  const n=ns.map(w=>w.text).join(' ').trim(),rawAccession=as.map(w=>w.text).join(' ').trim(),normalized=normalizeAccession(rawAccession),accession=normalized.value;
  const number=/^\d{1,7}$/.test(n)&&Number(n)>0?Number(n):null;
  if(!number&&/^(?:acc(?:ession)?(?:number|no)?|case|number|no)$/i.test(accession.replace(/[ #._-]/g,'')))continue;
  if(!number&&!/^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/.test(accession))continue;
  const check=(img.caseChecks||[]).find(c=>Math.abs(c.y-line.y)<=5);
  const caseIssue=!number?'Case number not read':check&&n.length<check.digits?'Case number may be incomplete':'';
  const candidate={case_number:number,accession,confirmed:false,source:img.label,imageId:img.id,rowY:line.y,caseIssue,accessionIssue:normalized.issue,originalAccession:normalized.original,confidence:Math.min(...[...ns,...as].map(w=>w.confidence??0))};
  img.rows.push(candidate);
  found++;
 }
 markAccessionLengths(img.rows);
 const repairs=repairCaseSequence(img.rows);
 for(const candidate of img.rows)if(!candidate.case_number||!lookupRows.some(r=>r.case_number===candidate.case_number&&r.accession===candidate.accession))lookupRows.push(candidate);
 lookupTable();updateReview();$('ocr-status').textContent=found?'Read '+found+' rows. '+(repairs?'Repaired '+repairs+' incomplete case numbers from a consistent sequence; suggested numbers are highlighted. ':'')+'Analyze reports accepts these mappings. You can correct any number against its source row.'+(img.bitmap.width<500?' Small source image: a larger original capture can improve recognition.':''):'No numbered rows recognized. Paste a clearer crop or add rows manually.';
}
function regularImageRows(rows){
 const gaps=rows.slice(1).map((r,i)=>r.rowY-rows[i].rowY),ordered=[...gaps].sort((a,b)=>a-b),median=ordered[Math.floor(ordered.length/2)];
 return gaps.every(g=>g>0&&g>=median*.55&&g<=median*1.6);
}
function repairCaseSequence(rows){
 if(rows.length<4||!regularImageRows(rows))return 0;
 const occurrences=new Map();for(const r of rows)if(Number.isInteger(r.case_number))occurrences.set(r.case_number,(occurrences.get(r.case_number)||0)+1);
 const anchors=rows.map((r,i)=>({r,i,start:r.case_number-i})).filter(a=>Number.isInteger(a.r.case_number)&&!a.r.caseIssue&&occurrences.get(a.r.case_number)===1);
 if(anchors.length<Math.max(4,Math.ceil(rows.length*.6)))return 0;
 const starts=new Set(anchors.map(a=>a.start));
 // Any contradictory readable number, gap or reordered source list blocks
 // repair. Do not choose a majority that could erase a legitimate source gap.
 // An early genuine 2/3 may also be excluded when 22/31 were truncated to
 // those digits. Allow an anchor in the first five rows, while retaining the
 // global consensus, spacing and far-end requirements.
 if(starts.size!==1||!anchors.some(a=>a.i<5)||!anchors.some(a=>a.i>=rows.length-3))return 0;
 const start=anchors[0].start;if(start<1||start+rows.length-1>1000000)return 0;
 let changed=0;
 for(const [i,r] of rows.entries())if(!Number.isInteger(r.case_number)||r.caseIssue||r.case_number!==start+i){r.originalCase=r.case_number;r.case_number=start+i;r.caseIssue='';r.numberSource='sequence';r.confirmed=false;changed++;}
 return changed;
}
async function addLookupImages(files){
 if(ocrBusy){$('ocr-status').textContent='Wait for the current screenshots to finish, then paste the next one.';return;}
 if(lookupImages.length+files.length>20){$('ocr-status').textContent='Use at most 20 screenshots per batch.';return;}
 const epoch=lookupEpoch;ocrBusy=true;updateLookupCoverage();
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
   $('ocr-status').textContent=img.label+' · Finding columns…';
   await worker.setParameters({tessedit_char_whitelist:'',tessedit_pageseg_mode:'6'});
   const {data}=await worker.recognize(canvas,{}, {blocks:true,text:true});canvas.width=1;canvas.height=1;
   if(epoch!==lookupEpoch)return;
   img.words=(data.blocks||[]).flatMap(b=>(b.paragraphs||[]).flatMap(p=>(p.lines||[]).flatMap(l=>l.words||[])));
   if(!img.words.length&&Array.isArray(data.words))img.words=data.words;
   if(scale!==1)img.words=img.words.map(w=>({...w,bbox:Object.fromEntries(Object.entries(w.bbox).map(([k,v])=>[k,v/scale]))}));
   if(detectColumns(img))await recognizeColumns(img,worker,epoch);else $('ocr-status').textContent='Could not identify the columns. Paste a clearer screenshot cropped to case numbers and accessions, or add rows manually.';
   showLookupImage(img);
  }
 }catch{if(epoch===lookupEpoch)$('ocr-status').textContent='Could not read this screenshot. Check the image size/format or retry. You can add rows manually.';}
 finally{if(epoch===lookupEpoch){ocrBusy=false;updateLookupCoverage();}}
}
$('lookup-zoom').addEventListener('change',()=>{if(currentImage)showLookupImage(currentImage);});
$('lookup-range-apply').addEventListener('click',()=>{
 const status=$('lookup-range-status'),first=$('lookup-range-first').value.trim(),last=$('lookup-range-last').value.trim(),img=currentImage;
 if(ocrBusy){status.textContent='Wait for OCR to finish first.';return;}
 if(!img?.rows?.length){status.textContent='Read the screenshot rows first.';return;}
 if(!/^\d+$/.test(first)||!/^\d+$/.test(last)||Number(first)<1||Number(last)>1000000||Number(last)<Number(first)){status.textContent='Enter the first and last case numbers visible in this screenshot.';return;}
 const count=Number(last)-Number(first)+1,rows=[...img.rows].sort((a,b)=>a.rowY-b.rowY);
 if(count!==rows.length){status.textContent='Range has '+count+' cases, but '+rows.length+' image rows were detected. Resolve missing or extra rows before assigning numbers.';return;}
 if(!regularImageRows(rows)){status.textContent='The detected row spacing is irregular. Check for a missing, duplicate or wrapped row; edit numbers individually instead.';return;}
 if(!$('lookup-range-checked').checked){status.textContent='Check that every case in this range is present and in order before applying it.';return;}
 lookupRows=lookupRows.filter(r=>r.imageId!==img.id);
 for(const [i,r] of rows.entries()){const next={...r,case_number:Number(first)+i,caseIssue:'',numberSource:'range',confirmed:false};if(!lookupRows.some(other=>other.case_number===next.case_number&&other.accession===next.accession))lookupRows.push(next);}
 lookupTable();updateReview();status.textContent='Assigned '+first+'–'+last+' to '+rows.length+' image rows. Accession strings are unchanged.';
});
$('report-text').addEventListener('input',updateReview);
$('lookup-panel').addEventListener('paste',event=>{const files=[...(event.clipboardData?.files||[])].filter(f=>f.type.startsWith('image/'));if(files.length){event.preventDefault();addLookupImages(files);}});
$('lookup-paste').addEventListener('click',async()=>{try{if(!navigator.clipboard?.read)throw Error();const items=await navigator.clipboard.read(),files=[];for(const item of items)for(const type of item.types)if(type.startsWith('image/')){files.push(await item.getType(type));break;}if(!files.length)throw Error();await addLookupImages(files);}catch{$('ocr-status').textContent='Copy a screenshot, then click Paste screenshot here and press Ctrl+V.';}});
$('lookup-add').addEventListener('click',()=>{lookupRows.push({case_number:null,accession:'',confirmed:false,source:'Manual'});lookupTable();});
$('lookup-clear').addEventListener('click',()=>{clearLookup();updateReview();});
$('export-review').addEventListener('click',async()=>{
 const target=$('export-review');target.disabled=true;$('export-status').textContent='Preparing clinical review…';
 try{
  if(ocrBusy||!lookupMatchesReview())throw Error('batch');
  const selected=$('export-filtered').checked?new Set([...document.querySelectorAll('#case-list .case')].map(r=>Number(r.id.slice(4)))):null;
  const records=cases.filter((c,i)=>!selected||selected.has(i)).map(c=>({source_numbers:members(c),resident_report:c.resident_report,attending_report:c.attending_report,review_mode:c.review_mode,exam_label:c.exam_label,title:c.title,status:c.status,revisions:revisions(c)}));
  const lookup=lookupRows.filter(r=>validLookup(r)).map(r=>({case_number:r.case_number,accession:r.accession,confirmed:true}));
  const response=await fetch('/export-review',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('[name=csrf_token]').value},body:JSON.stringify({cases:records,lookup,review_mode:reviewMode,theme:themeChoice,combined_view:combinedView,show_report_wording:showReportWording})});
  if(response.redirected||response.status===401||response.status===403)throw Error('session');
  if(!response.ok||!response.headers.get('content-type')?.includes('text/html'))throw Error('export');
  const html=await response.text(),reader=new DOMParser().parseFromString(html,'text/html');if(reader.head.querySelector('meta[name="compare-revisions-export"]')?.content!=='offline-v1')throw Error('session');
  const blob=new Blob([html],{type:'text/html;charset=utf-8'}),url=URL.createObjectURL(blob),link=el('a');link.href=url;link.download='clinical-review.html';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);$('export-status').textContent='Review downloaded. Contains PHI—keep it within approved systems.';
 }catch(error){$('export-status').textContent=error.message==='session'?'Your sign-in expired. Sign in to Compare Revisions, then download the review again.':'Export could not be completed. Check that analysis is finished and lookup issues are resolved.';}
 finally{updateLookupCoverage();}
});
lookupTable();
{% endif %}

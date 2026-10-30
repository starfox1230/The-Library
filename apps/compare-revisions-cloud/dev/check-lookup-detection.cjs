// Pure geometry/domain checks with invented identifiers; no OCR/model/network.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync(path.join(__dirname,'lookup.js'),'utf8'),context={};vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function imageLines('),source.indexOf('async function recognizeColumns(')),context);
for(const prefix of ['XR','RF','MR','CT','OT','US','NM'])assert.equal(context.normalizeAccession(prefix+'000001234').value,prefix+'000001234');
for(const prefix of ['0T','07','O7']){
 const r=context.normalizeAccession(prefix+'900001234');assert.equal(r.value,'OT900001234');assert.equal(r.original,prefix+'900001234');
}
assert.equal(context.normalizeAccession('CTO00001234').value,'CT000001234');
assert(context.normalizeAccession('CT1234S6789').issue,'uncertain digit-like letters must not be guessed');
assert(context.normalizeAccession('123456789').issue,'numeric-only identifier is not enough to infer an accession');
const word=(text,x0,x1,y)=>({text,bbox:{x0,x1,y0:y,y1:y+10}});
const image=(prefix='CT',middle=false)=>({bitmap:{width:400},words:Array.from({length:8},(_,i)=>[
 word(String(57+i),5,18,30+i*18),...(middle?[word('9876543',75,125,30+i*18)]:[]),word(prefix+'90000123'+i,180,270,30+i*18)]).flat()});
let img=image('CT',true);assert(context.detectColumns(img),'headerless accession/case positions should be inferred');assert(img.caseColumn[1]<75,'MRN column must not enter the case-number crop');assert(img.accessionColumn[0]>125,'MRN column must not enter the accession crop');
img=image('0T');assert(context.detectColumns(img),'ambiguous OT prefix with a visible letter remains detectable');
img=image('07');assert.equal(context.detectColumns(img),false,'all-numeric rows cannot bootstrap a headerless accession column');
img=image();img.words=img.words.slice(0,4);assert.equal(context.detectColumns(img),false,'insufficient rows are not guessed');
img=image();img.words.push(...image('MR').words.map(w=>({...w,bbox:{...w.bbox,x0:w.bbox.x0+110,x1:w.bbox.x1+110}})));assert.equal(context.detectColumns(img),false,'competing accession columns require a clearer crop');
let rows=Array.from({length:8},(_,i)=>({accession:'MR90000123'+i,accessionIssue:''}));rows[4].accession+='4';context.markAccessionLengths(rows);assert(rows[4].accessionIssue.includes('9 digits'));assert(rows.filter(r=>r.accessionIssue).length===1);assert(rows[4].accession.endsWith('4'),'extra digits must not be trimmed');
rows=[{accession:'MR123456',accessionIssue:''},{accession:'MR1234567',accessionIssue:''}];context.markAccessionLengths(rows);assert(rows.every(r=>!r.accessionIssue),'small samples cannot establish a modal digit length');
console.log('Header-free detection, extra-column exclusion, OT/O context corrections, leading zero digits, and non-destructive length warnings passed.');

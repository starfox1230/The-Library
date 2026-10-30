// Pure sequence safeguards: no OCR runtime, network, real identifiers or provider calls.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),vm=require('vm');
const source=fs.readFileSync(path.join(__dirname,'lookup.js'),'utf8');
const block=source.slice(source.indexOf('function regularImageRows('),source.indexOf('async function addLookupImages('));
const context={};vm.createContext(context);vm.runInContext(block,context);
const make=(count,start=1)=>Array.from({length:count},(_,i)=>({case_number:start+i,accession:'SYNTHETIC-'+i,rowY:30+i*18,caseIssue:'',confirmed:false}));
const copy=value=>JSON.parse(JSON.stringify(value));
const repair=context.repairCaseSequence;
let rows=make(47),accessions=rows.map(r=>r.accession);
for(const [i,n] of [[10,null],[16,7],[21,2],[30,3],[33,4],[35,3],[40,4]])rows[i].case_number=n;
rows[10].caseIssue='Case number not read';rows[16].caseIssue='Case number may be incomplete';
assert.equal(repair(rows),7);assert.deepEqual(rows.map(r=>r.case_number),make(47).map(r=>r.case_number));assert.deepEqual(rows.map(r=>r.accession),accessions);
assert.equal(rows.filter(r=>r.numberSource==='sequence').length,7);assert(rows.every(r=>!r.confirmed));assert.equal(rows[16].originalCase,7);
rows=make(12,68);rows[5].case_number=null;assert.equal(repair(rows),1);assert.equal(rows[5].case_number,73,'repair starts from actual source labels, not 1');
for(const mutate of [
 r=>{r[4].case_number=900;}, // Contradictory unique reading: never choose a majority.
 r=>{for(let i=5;i<r.length;i++)r[i].case_number++;}, // Genuine source-number gap.
 r=>{r.reverse();}, // Reordered list.
 r=>{for(let i=5;i<r.length;i++)r[i].rowY+=18;}, // Missing image row.
 r=>{r[5].rowY=r[4].rowY;}, // Duplicate image row.
 r=>{r.forEach((v,i)=>{if(i>1)v.case_number=null;});}, // Insufficient anchors.
 r=>{r.forEach(v=>v.case_number=2);}, // Repeated labels cannot be anchors.
 r=>{r[7].case_number=1;}, // Unique readable contradiction with invalid start.
]){rows=make(12,68);mutate(rows);const before=copy(rows);assert.equal(repair(rows),0);assert.deepEqual(rows,before);}
console.log('Sequence repair passed: seven truncated/unread labels, source offsets, unchanged accessions, confirmation retained, and refusal of contradictory/gapped/reordered/insufficient evidence.');

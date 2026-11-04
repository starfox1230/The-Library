// Each screenshot is contracted to be a consecutive, increasing source list.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),vm=require('vm');
const source=fs.readFileSync(path.join(__dirname,'lookup.js'),'utf8'),context={};vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function repairCaseSequence('),source.indexOf('function reconcileLookupImages(')),context);
const make=(count,start=1)=>Array.from({length:count},(_,i)=>({case_number:start+i,accession:'SYNTHETIC-'+i,rowY:30+i*18,caseIssue:'',confirmed:false}));
const repair=context.repairCaseSequence;
let rows=make(47),accessions=rows.map(r=>r.accession);
for(const [i,n] of [[10,null],[16,7],[21,2],[30,3],[33,4],[35,3],[40,4]])rows[i].case_number=n;
rows[10].caseIssue='Case number not read';rows[16].caseIssue='Case number may be incomplete';
assert.equal(repair(rows),7);assert.deepEqual(rows.map(r=>r.case_number),make(47).map(r=>r.case_number));assert.deepEqual(rows.map(r=>r.accession),accessions);assert(rows.every(r=>!r.caseIssue));
for(const middle of [null,1,77,111]){
 rows=[8,9,10,middle,12].map((n,i)=>({case_number:n,caseIssue:i===3?'Case number may be incomplete':'',accession:'SYNTHETIC-'+i}));
 assert.equal(repair(rows),1);assert.deepEqual(rows.map(r=>r.case_number),[8,9,10,11,12]);assert(rows.every(r=>!r.caseIssue));
}
rows=make(12,68);rows[0].case_number=null;rows[4].case_number=900;rows[8].case_number=7;
accessions=rows.map(r=>r.accession);assert.equal(repair(rows),3);assert.deepEqual(rows.map(r=>r.case_number),make(12,68).map(r=>r.case_number));assert.deepEqual(rows.map(r=>r.accession),accessions);
rows=make(20);for(let i=15;i<rows.length;i++)rows[i].case_number++;
assert.equal(repair(rows),5);assert.deepEqual(rows.map(r=>r.case_number),make(20).map(r=>r.case_number),'source gaps are OCR inconsistencies under the new contract');
rows=make(12,68);rows.forEach((r,i)=>{if(i<8)r.case_number=null;r.rowY+=i%2?8:0;});
assert.equal(repair(rows),8);assert.deepEqual(rows.map(r=>r.case_number),make(12,68).map(r=>r.case_number),'end anchors suffice; spacing is not a case-number warning');
rows=[{case_number:1},{case_number:12}];assert.equal(repair(rows),1);assert.deepEqual(rows.map(r=>r.case_number),[11,12]);
rows=make(5,68);rows.forEach(r=>{r.case_number=null;r.caseIssue='Case number not read';});
assert.equal(repair(rows),0,'do not invent an absolute start without any anchor');
assert.equal(repair(rows,68),5);assert.deepEqual(rows.map(r=>r.case_number),[68,69,70,71,72]);assert(rows.every(r=>!r.caseIssue));assert.equal(repair(rows),0);
console.log('Consecutive screenshot numbering passed: missing/truncated/substituted digits, source offsets, end anchors, spacing, explicit starts and unchanged accessions.');

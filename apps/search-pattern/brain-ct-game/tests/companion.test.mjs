import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateCompanion} from '../volume.mjs';
const a=JSON.parse(await readFile(new URL('../cases/normal-head/manifest.json',import.meta.url)));
const b=JSON.parse(await readFile(new URL('../cases/normal-head/bone/manifest.json',import.meta.url)));
test('only matching companion identity, versions, checksum and physical grid are accepted',()=>{
 assert.equal(validateCompanion(a,b),b);
 for(const key of ['id','version','checkpointVersion','sha256'])assert.throws(()=>validateCompanion(a,{...b,[key]:'mismatched'}),/companion/i);
 assert.throws(()=>validateCompanion(a,{...b,originLPS:[0,0,0]}),/align/i);
});

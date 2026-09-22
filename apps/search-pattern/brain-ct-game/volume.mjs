export function validateManifest(m){
 for(const name of ['id','version','checkpointVersion'])if(typeof m[name]!=='string'||!m[name])throw Error(`Missing ${name}`);
 if(m.encoding!=='gzip-i16le-hu')throw Error('Unsupported volume encoding');
 if(!Array.isArray(m.dimensions)||m.dimensions.length!==3||m.dimensions.some(x=>!Number.isSafeInteger(x)||x<1))throw Error('Invalid dimensions');
 if(m.dimensions.reduce((a,b)=>a*b,1)>160_000_000)throw Error('Volume size exceeds limit');
 if(!Array.isArray(m.spacing)||m.spacing.length!==3||m.spacing.some(x=>!Number.isFinite(x)||x<=0))throw Error('Invalid spacing');
 if(!Array.isArray(m.originLPS)||m.originLPS.length!==3||m.originLPS.some(x=>!Number.isFinite(x)))throw Error('Invalid origin');
 if(typeof m.volumeUrl!=='string'||!/^[\w./-]+$/.test(m.volumeUrl)||m.volumeUrl.includes('..'))throw Error('Invalid volume path');
 if(!/^[0-9a-f]{64}$/.test(m.sha256))throw Error('Missing volume checksum');
 return m;
}
export async function loadVolume(manifestUrl,{fetcher=fetch,onProgress=()=>{}}={}){
 const response=await fetcher(manifestUrl,{cache:'no-store'});if(!response.ok)throw Error(`Case metadata: HTTP ${response.status}`);
 const manifest=validateManifest(await response.json());const expected=manifest.dimensions.reduce((a,b)=>a*b,2);
 const res=await fetcher(new URL(manifest.volumeUrl,manifestUrl));if(!res.ok)throw Error(`CT data: HTTP ${res.status}`);
 if(typeof DecompressionStream==='undefined')throw Error('This browser does not support gzip decoding. Use current Chrome, Edge, or Firefox.');
 const reader=res.body.pipeThrough(new DecompressionStream('gzip')).getReader();const raw=new Uint8Array(expected);let used=0;
 try{while(true){const {done,value}=await reader.read();if(done)break;if(used+value.length>expected)throw Error('Decoded volume size exceeds metadata');raw.set(value,used);used+=value.length;onProgress(used/expected);}}
 catch(e){await reader.cancel().catch(()=>{});throw e;}
 if(used!==expected)throw Error('Decoded volume length does not match metadata');
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==manifest.sha256)throw Error('CT data checksum mismatch. Retry the download.');
 const data=new DataView(raw.buffer),values=new Int16Array(expected/2);
 for(let i=0;i<values.length;i++)values[i]=data.getInt16(i*2,true);
 return {manifest,values};
}


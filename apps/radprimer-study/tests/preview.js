'use strict';
function phantom(group, image, annotated) {
  const canvas = document.createElement('canvas'); canvas.width = group ? 1000 : 800; canvas.height = 1000;
  const ctx = canvas.getContext('2d'); ctx.fillStyle = '#090c0f'; ctx.fillRect(0,0,canvas.width,canvas.height);
  const center = canvas.width/2;
  ctx.save(); ctx.translate(center,470); ctx.rotate(group ? .12 : -.08);
  const glow = ctx.createRadialGradient(0,0,20,0,0,360); glow.addColorStop(0,'#b7bdc1'); glow.addColorStop(.65,'#505a61'); glow.addColorStop(1,'#11191f');
  ctx.fillStyle=glow; ctx.beginPath();ctx.ellipse(0,0,250,360,0,0,Math.PI*2);ctx.fill();
  for(let ring=0;ring<8;ring++){
    ctx.strokeStyle=ring%2?'#929da4':'#303b43';ctx.lineWidth=7;
    ctx.beginPath();ctx.ellipse(0,0,65+ring*21,100+ring*29,0,0,Math.PI*2);ctx.stroke();
  }
  ctx.fillStyle='#1c2931';ctx.fillRect(-44,-200,88,400);ctx.fillStyle='#c3cace';ctx.fillRect(-29,-187,58,374);
  ctx.fillStyle='#56656e';ctx.beginPath();ctx.arc(group?90:-90,image?75:-75,52,0,Math.PI*2);ctx.fill();
  if(annotated){ctx.strokeStyle='#52c8e7';ctx.lineWidth=7;ctx.beginPath();ctx.arc(group?90:-90,image?75:-75,65,0,Math.PI*2);ctx.stroke();}
  ctx.restore();ctx.fillStyle='#99adb8';ctx.font='24px Arial';ctx.fillText('SYNTHETIC • '+(group?'LATERAL':'FRONTAL')+' '+(image+1),30,48);
  ctx.font='20px Arial';ctx.fillText('Layout test image / '+(annotated?'annotations':'original'),30,955);
  return canvas.toDataURL('image/png');
}
async function seed(count) {
  const cases=[];
  for(let n=0;n<count;n++){
    const stem=n?'Compare the same synthetic shape across two views. Which feature remains consistent?':'Review the two synthetic views. Which geometric shape is outlined in both images?';
    const answers=['Circle','Square','Triangle'].map((text,index)=>({id:'synthetic-'+n+'-'+index,text,selected:false,correctness:index?'incorrect':'correct',explanation:index?'This option does not match the outline in the synthetic example.':'The same circular outline is visible in both views. The images are generated only for layout testing.'}));
    cases.push({schema:1,id:await RadCore.caseId(stem,answers),stem,answers,sourceUrl:'',questionLabel:'Synthetic case '+(n+1),sourceLabel:'Layout preview',author:'',answered:true,teachingPoint:'Compare the views while keeping the images visible. This is original test content, not clinical teaching material.',notes:'Remember this specific visual feature.',highlights:[],tier:'review',ankiStatus:'none',savedAt:new Date(Date.now()-n*60000).toISOString(),updatedAt:RadCore.now(),archived:false,dueAt:null,reviewedAt:null,
      groups:[0,1].map(g=>({id:'synthetic-group-'+g,title:g?'Lateral view':'Frontal view',images:[0,1].map(i=>({id:'synthetic-'+g+'-'+i,alt:'Synthetic '+(g?'lateral':'frontal')+' image '+(i+1),caption:'Synthetic '+(g?'lateral':'frontal')+' image '+(i+1)+': the circular outline is highlighted in the annotated version. Compare with the other group.',original:phantom(g,i,false),annotated:phantom(g,i,true),annotationExpected:true,originalUrl:'',annotatedUrl:'',error:''}))}))});
  }
  await RadDB.importBackup({schema:1,format:'radprimer-library',cases}); location.href='../extension/library.html';
}
document.querySelector('#one').onclick=()=>seed(1).catch(e=>document.querySelector('#result').textContent=e.message);
document.querySelector('#multiple').onclick=()=>seed(2).catch(e=>document.querySelector('#result').textContent=e.message);

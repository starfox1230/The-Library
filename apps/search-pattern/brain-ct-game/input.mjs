export function normalizeWheel(event,carry=0){
 const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?400:1);
 const sum=carry+delta,raw=Math.trunc(sum/40),steps=Math.max(-4,Math.min(4,raw));
 return {steps,carry:Math.abs(raw)>4?0:sum-raw*40};
}
export function isGameShortcut(event){return !event.ctrlKey&&!event.metaKey&&!event.altKey&&!event.target?.isContentEditable&&!['INPUT','SELECT','TEXTAREA','BUTTON'].includes(event.target?.tagName);}
export function isClick(start,end){return Math.hypot(end[0]-start[0],end[1]-start[1])<=4;}

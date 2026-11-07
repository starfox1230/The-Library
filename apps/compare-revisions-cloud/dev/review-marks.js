// Case annotations live only in the document. Never persist clinical data in browser storage.
const reviewMetadata=JSON.parse($('review-metadata').textContent||'{}');
$('feedback-notice').hidden=!reviewMetadata.feedback_only;
let markRevision=0,downloadedRevision=0,markMessage='',feedbackCase=null,feedbackFocus=null;
function marksFor(c){
 if(!c.review_marks||typeof c.review_marks!=='object')c.review_marks={};
 const m=c.review_marks;
 m.favorite=m.favorite===true;m.flagged=m.flagged===true;
 m.comment=typeof m.comment==='string'?m.comment.slice(0,2000):'';
 return m;
}
for(const c of cases)marksFor(c);
function markChanged(){markRevision++;markMessage='';updateMarkTools();}
function updateMarkTools(){
 const stars=cases.filter(c=>marksFor(c).favorite).length,flags=cases.filter(c=>marksFor(c).flagged).length;
 $('mark-counts').textContent='★ Marked for later: '+stars+' · ⚑ Project feedback: '+flags;
 $('export-feedback').textContent='Download feedback ('+flags+')';
 $('export-feedback').disabled=!flags||cases.some(c=>['queued','processing'].includes(c.status));
 $('mark-status').textContent=markMessage||(markRevision>downloadedRevision?
  'Changes are not included in a downloaded copy yet. Download an updated review to keep them.':
  'Marks and comments stay in this open page until you download an updated copy.');
 $('mark-filters').replaceChildren(filterChip('favorite','★ Marked for later ('+stars+')'),filterChip('flagged','⚑ Project feedback ('+flags+')'));
 if(!exportedReview)$('export-review').textContent=stars||flags||markRevision?'Download updated review':'Download review HTML';
}
function refreshMarkRow(id){
 const key=id.slice(id.indexOf('-')+1),anchor=$('case-'+key),before=anchor?.getBoundingClientRect().top;
 renderAndFocus(id);
 const after=$('case-'+key)?.getBoundingClientRect().top;
 if(Number.isFinite(before)&&Number.isFinite(after))window.scrollBy(0,after-before);
}
function caseMarkTools(c,key){
 const m=marksFor(c),tools=el('div','case-mark-tools');
 const star=button('','case-mark',()=>{m.favorite=!m.favorite;markChanged();refreshMarkRow('favorite-'+key);$('announcement').textContent=m.favorite?'Marked for later. Download an updated review to keep your marks.':'Mark for later removed.';});
 star.id='favorite-'+key;star.title='Mark this case to revisit. Download an updated review to keep your marks.';
 star.setAttribute('aria-label','Mark case '+caseLabel(c)+' for later');star.setAttribute('aria-pressed',String(m.favorite));
 star.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z"/></svg>';
 const flag=button('','case-mark',()=>{
  if(!m.flagged){m.flagged=true;markChanged();refreshMarkRow('feedback-'+key);}
  feedbackCase=c;feedbackFocus='feedback-'+key;
  $('feedback-title').textContent='Project feedback · '+(members(c).length>1?'Cases ':'Case ')+caseLabel(c);
  $('feedback-comment').value=m.comment;$('feedback-dialog').showModal();
 });
 flag.id='feedback-'+key;flag.title='Include this case in feedback for Sterling. Nothing is sent automatically.';
 flag.setAttribute('aria-label','Project feedback for case '+caseLabel(c));flag.setAttribute('aria-pressed',String(m.flagged));
 flag.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 21V3m0 1c5-3 9 3 14 0v10c-5 3-9-3-14 0"/></svg>';
 tools.append(star,flag);return tools;
}
$('feedback-comment').addEventListener('input',()=>{if(feedbackCase){marksFor(feedbackCase).comment=$('feedback-comment').value;markChanged();}});
$('feedback-done').addEventListener('click',()=>$('feedback-dialog').close());
$('feedback-remove').addEventListener('click',()=>{
 if(feedbackCase){const m=marksFor(feedbackCase);m.flagged=false;m.comment='';markChanged();}
 $('feedback-dialog').close();
});
$('feedback-dialog').addEventListener('close',()=>{const id=feedbackFocus;feedbackCase=null;feedbackFocus=null;refreshMarkRow(id);});
function resolvedTheme(){return $('theme-toggle').getAttribute('aria-checked')==='true'?'dark':'light';}
function downloadHTML(html,filename){
 const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'})),link=el('a');
 link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
function downloadNotice(feedback,full=true,revision=markRevision){
 if(!feedback&&full)downloadedRevision=revision;
 markMessage=feedback?'Feedback download started—not sent. Attach it manually to your approved work email. Download an updated review to keep all marks.':
  (markRevision===revision?'Updated-copy download started. The original file is unchanged; open the downloaded copy next time.':'Download started. More recent changes still need a new updated copy.');
 if(!feedback&&!full)markMessage='Filtered-copy download started. Marks outside that selection are not included.';
 updateMarkTools();
}
function downloadOfflineReview(feedback=false){
 const records=feedback?cases.filter(c=>marksFor(c).flagged):cases;
 if(!records.length)return;
 const clone=document.documentElement.cloneNode(true);
 clone.dataset.theme=resolvedTheme();clone.querySelector('#cr-app').dataset.theme=resolvedTheme();
 clone.querySelector('#theme-value').setAttribute('value',resolvedTheme());
 clone.querySelector('#combined-view').toggleAttribute('checked',combinedView);
 clone.querySelector('#combined-view-value').setAttribute('value',combinedView?'1':'0');
 clone.querySelector('#cr-app').dataset.reviewMode=reviewMode;
 clone.querySelector('#review-data').textContent=JSON.stringify(records).replaceAll('<','\\u003c');
 clone.querySelector('#lookup-data').textContent=JSON.stringify(feedback?[]:lookupRows.map(lookupPayload)).replaceAll('<','\\u003c');
 clone.querySelector('#review-metadata').textContent=JSON.stringify({...reviewMetadata,feedback_only:feedback}).replaceAll('<','\\u003c');
 clone.querySelector('#case-list').replaceChildren();clone.querySelectorAll('.accession-peek').forEach(n=>n.remove());
 clone.querySelector('#feedback-dialog').removeAttribute('open');clone.querySelector('#feedback-comment').textContent='';
 clone.querySelector('#feedback-title').textContent='Project feedback';
 clone.querySelector('#search').setAttribute('value','');
 // Rebuild all clinical content from the selected JSON only; no hidden unflagged case DOM survives.
 downloadHTML('<!doctype html>\n'+clone.outerHTML,feedback?'clinical-feedback.html':'clinical-review.html');
 downloadNotice(feedback);
}
$('export-feedback').addEventListener('click',()=>{
 if(exportedReview)downloadOfflineReview(true);
 {% if not exported_review | default(false) %}else downloadLiveReview(true);{% endif %}
});

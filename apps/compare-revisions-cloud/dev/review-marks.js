// Case annotations live only in the document. Never persist clinical data in browser storage.
const reviewMetadata=JSON.parse($('review-metadata').textContent||'{}');
$('feedback-notice').hidden=!reviewMetadata.feedback_only;
let markRevision=0,feedbackCase=null,feedbackFocus=null,reviewToastTimer=null,reviewDownloadBusy=false;
let markKeyboardInput=false;
document.addEventListener('pointerdown',()=>{markKeyboardInput=false;});
document.addEventListener('keydown',()=>{markKeyboardInput=true;});
const starIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z"/></svg>';
const flagIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 21V3m0 1c5-3 9 3 14 0v10c-5 3-9-3-14 0"/></svg>';
function marksFor(c){
 if(!c.review_marks||typeof c.review_marks!=='object')c.review_marks={};
 const m=c.review_marks;
 m.favorite=m.favorite===true;m.flagged=m.flagged===true;
 m.comment=typeof m.comment==='string'?m.comment.slice(0,2000):'';
 return m;
}
for(const c of cases)marksFor(c);
function markChanged(){markRevision++;updateMarkTools();}
function hideReviewToast(){
 clearTimeout(reviewToastTimer);reviewToastTimer=null;$('review-toast').hidden=true;
}
function showReviewToast(message='Changes are only saved when you download an updated copy.',download=true){
 const toast=$('review-toast'),action=$('review-toast-download');
 ($('feedback-dialog').open?$('feedback-dialog'):$('review-toast-host')).append(toast);
 $('review-toast-message').textContent=message;
 if(!download&&document.activeElement===action)($('feedback-dialog').open?$('feedback-done'):$(exportedReview?'save-review':'export-review')).focus({preventScroll:true});
 action.hidden=!download;action.disabled=reviewDownloadBusy||cases.some(c=>['queued','processing'].includes(c.status));
 toast.hidden=false;clearTimeout(reviewToastTimer);
 const expire=()=>{if(toast.contains(document.activeElement)){reviewToastTimer=setTimeout(expire,1000);return;}hideReviewToast();};
 reviewToastTimer=setTimeout(expire,4000);
}
function markFilter(key,count){
 const favorite=key==='favorite',label=(favorite?'Marked for later':'Project feedback')+' ('+count+')';
 const chip=filterChip(key,'','mark-filter '+(favorite?'favorite-filter':'feedback-filter'),label);
 chip.innerHTML=favorite?starIcon:flagIcon;chip.append(el('span','',count));return chip;
}
function updateMarkTools(){
 const stars=cases.filter(c=>marksFor(c).favorite).length,flags=cases.filter(c=>marksFor(c).flagged).length;
 $('export-feedback').textContent='Download feedback ('+flags+')';
 const busy=reviewDownloadBusy||cases.some(c=>['queued','processing'].includes(c.status));
 $('export-feedback').disabled=!flags||busy;$('review-toast-download').disabled=busy;
 $('mark-filters').replaceChildren(markFilter('favorite',stars),markFilter('flagged',flags));
 if(!exportedReview)$('export-review').textContent=stars||flags||markRevision?'Download updated review':'Download review HTML';
}
function refreshMarkRow(id){
 const key=id.slice(id.indexOf('-')+1),anchor=$('case-'+key),before=anchor?.getBoundingClientRect().top;
 // Pointer clicks must not acquire a keyboard-style square focus outline
 // merely because the row was rebuilt. Restore focus for keyboard navigation.
 render();if(markKeyboardInput)$(id)?.focus({preventScroll:true});
 const after=$('case-'+key)?.getBoundingClientRect().top;
 if(Number.isFinite(before)&&Number.isFinite(after))window.scrollBy(0,after-before);
}
function caseMarkTools(c,key){
 const m=marksFor(c),tools=el('div','case-mark-tools');
 const star=button('','case-mark',()=>{m.favorite=!m.favorite;markChanged();refreshMarkRow('favorite-'+key);showReviewToast();$('announcement').textContent=m.favorite?'Marked for later.':'Mark for later removed.';});
 star.id='favorite-'+key;star.title='Mark this case for later.';
 star.setAttribute('aria-label','Mark case '+caseLabel(c)+' for later');star.setAttribute('aria-pressed',String(m.favorite));
 star.innerHTML=starIcon;
 const flag=button('','case-mark',()=>{
  if(!m.flagged){m.flagged=true;markChanged();refreshMarkRow('feedback-'+key);}
  feedbackCase=c;feedbackFocus='feedback-'+key;
  $('feedback-title').textContent='Project feedback · '+(members(c).length>1?'Cases ':'Case ')+caseLabel(c);
  $('feedback-comment').value=m.comment;$('feedback-dialog').showModal();showReviewToast();
 });
 flag.id='feedback-'+key;flag.title='Include this case in the feedback download. Nothing is sent automatically.';
 flag.setAttribute('aria-label','Project feedback for case '+caseLabel(c));flag.setAttribute('aria-pressed',String(m.flagged));
 flag.innerHTML=flagIcon;
 tools.append(star,flag);return tools;
}
$('feedback-comment').addEventListener('input',()=>{if(feedbackCase){marksFor(feedbackCase).comment=$('feedback-comment').value;markChanged();}});
$('feedback-done').addEventListener('click',()=>$('feedback-dialog').close());
$('feedback-remove').addEventListener('click',()=>{
 if(feedbackCase){const m=marksFor(feedbackCase);m.flagged=false;m.comment='';markChanged();}
 $('feedback-dialog').close();showReviewToast();
});
$('feedback-dialog').addEventListener('close',()=>{const id=feedbackFocus;feedbackCase=null;feedbackFocus=null;$('review-toast-host').append($('review-toast'));refreshMarkRow(id);});
$('review-toast-download').addEventListener('click',()=>{
 if(exportedReview)downloadOfflineReview(false);
 {% if not exported_review | default(false) %}else downloadLiveReview(false,true);{% endif %}
});
$('more-filters').addEventListener('keydown',event=>{if(event.key==='Escape'){$('more-filters').open=false;$('more-filters-label').focus();}});
function positionMoreFilters(){
 if(!$('more-filters').open)return;
 const menu=$('status-filters');menu.style.left='';menu.style.right='';
 if(menu.getBoundingClientRect().left<12){menu.style.left='0';menu.style.right='auto';}
}
$('more-filters').addEventListener('toggle',positionMoreFilters);
window.addEventListener('resize',positionMoreFilters);
document.addEventListener('pointerdown',event=>{if(!event.target.closest('#more-filters'))$('more-filters').open=false;});
function resolvedTheme(){return $('theme-toggle').getAttribute('aria-checked')==='true'?'dark':'light';}
function downloadHTML(html,filename){
 const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'})),link=el('a');
 link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
function downloadNotice(feedback,full=true,revision=markRevision){
 let message=feedback?'Feedback download started—not sent. Attach it manually to your approved work email.':
  (markRevision===revision?'Updated-copy download started. The original file is unchanged; open the downloaded copy next time.':'Download started. More recent changes still need a new updated copy.');
 if(!feedback&&!full)message='Filtered-copy download started. Marks outside that selection are not included.';
 showReviewToast(message,false);updateMarkTools();
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
 clone.querySelector('#review-toast-host').append(clone.querySelector('#review-toast'));
 clone.querySelector('#review-toast').hidden=true;
 clone.querySelector('#review-toast-message').textContent='';
 clone.querySelector('#search').setAttribute('value','');
 // Rebuild all clinical content from the selected JSON only; no hidden unflagged case DOM survives.
 downloadHTML('<!doctype html>\n'+clone.outerHTML,feedback?'clinical-feedback.html':'clinical-review.html');
 downloadNotice(feedback);
}
$('export-feedback').addEventListener('click',()=>{
 if(exportedReview)downloadOfflineReview(true);
 {% if not exported_review | default(false) %}else downloadLiveReview(true);{% endif %}
});

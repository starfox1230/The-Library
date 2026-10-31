/* App-style touch interactions. Keep one-finger scrolling and form controls native. */
(() => {
  'use strict';
  const editable='input,textarea,select,[contenteditable]:not([contenteditable="false"])';
  const element=node=>node?.nodeType===1?node:node?.parentElement;
  const canEdit=node=>Boolean(element(node)?.closest(editable));
  const clearUISelection=()=>{const selection=window.getSelection();if(selection?.rangeCount&&!canEdit(selection.anchorNode)&&!canEdit(selection.focusNode))selection.removeAllRanges();};
  document.addEventListener('selectstart',event=>{if(!canEdit(event.target)&&event.cancelable)event.preventDefault();});
  document.addEventListener('selectionchange',clearUISelection);
  document.addEventListener('pointerdown',event=>{if(!canEdit(event.target))clearUISelection();},true);
  document.addEventListener('dragstart',event=>{if(!canEdit(event.target)&&event.cancelable)event.preventDefault();});

  const preventZoom = event => { if (event.cancelable) event.preventDefault(); };
  document.addEventListener('contextmenu', event => {
    if (!event.target.closest('input,textarea,[contenteditable="true"],[contenteditable=""]')) preventZoom(event);
  });
  // WebKit may ignore viewport scale limits, so also cancel its pinch gestures.
  for (const type of ['gesturestart', 'gesturechange', 'gestureend']) {
    document.addEventListener(type, preventZoom, { passive: false });
  }
  document.addEventListener('dblclick', event => {
    if (!event.target.closest('input,textarea,[contenteditable="true"],[contenteditable=""]')) preventZoom(event);
  }, { passive: false });
  for (const type of ['touchstart', 'touchmove']) {
    document.addEventListener(type, event => {
      if (event.touches.length > 1) preventZoom(event);
    }, { passive: false });
  }
  // Trackpad pinch is delivered as a Ctrl+wheel gesture in Chromium.
  document.addEventListener('wheel', event => {
    if (event.ctrlKey) preventZoom(event);
  }, { passive: false });
})();

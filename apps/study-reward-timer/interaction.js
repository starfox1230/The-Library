/* App-style touch interactions. Keep one-finger scrolling and form controls native. */
(() => {
  'use strict';
  const preventZoom = event => { if (event.cancelable) event.preventDefault(); };
  // WebKit may ignore viewport scale limits, so also cancel its pinch gestures.
  for (const type of ['gesturestart', 'gesturechange', 'gestureend', 'dblclick']) {
    document.addEventListener(type, preventZoom, { passive: false });
  }
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

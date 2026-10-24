/* Only this app's static assets are cached. The ledger stays in localStorage. */
const CACHE = 'afterglow-static-v9';
const ASSETS = ['./', 'index.html', 'style.css?v=9', 'engine.js?v=9', 'interaction.js?v=9', 'haptics.js?v=9', 'gestures.js?v=9', 'haptic-editor.js?v=9', 'theme.js?v=9', 'theme.css?v=9', 'app.js?v=9', 'icon.svg', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'icon-maskable.png', 'site.webmanifest'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS.map(asset => new Request(new URL(asset, self.registration.scope), {cache:'reload'})))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('afterglow-static-') && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || !url.href.startsWith(self.registration.scope)) return;
  // Network first prevents a stale cached UI after a GitHub Pages update.
  event.respondWith(fetch(event.request, {cache:'no-cache'}).then(response => {
    if (response.ok && ASSETS.some(asset => new URL(asset, self.registration.scope).pathname === url.pathname)) {
      const copy = response.clone();
      event.waitUntil(caches.open(CACHE).then(cache => cache.put(event.request, copy)));
    }
    return response;
  }).catch(async () => (await caches.match(event.request)) || (event.request.mode === 'navigate' ? await caches.match(new URL('index.html', self.registration.scope)) : Response.error())));
});

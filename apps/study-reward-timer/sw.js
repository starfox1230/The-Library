/* Only this app's static assets are cached. The ledger stays in localStorage. */
const CACHE = 'afterglow-static-v1';
const ASSETS = ['./', 'index.html', 'style.css', 'engine.js', 'app.js', 'icon.svg', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'icon-maskable.png', 'site.webmanifest'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('afterglow-static-') && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || !url.href.startsWith(self.registration.scope)) return;
  // Network first prevents a stale cached UI after a GitHub Pages update.
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok && ASSETS.some(asset => new URL(asset, self.registration.scope).pathname === url.pathname)) {
      const copy = response.clone();
      event.waitUntil(caches.open(CACHE).then(cache => cache.put(event.request, copy)));
    }
    return response;
  }).catch(async () => (await caches.match(event.request)) || (event.request.mode === 'navigate' ? await caches.match(new URL('index.html', self.registration.scope)) : Response.error())));
});

// GTU-ITR Portal Zero-Downtime Service Worker
const CACHE_NAME = 'gtu-standby-v1';
const STANDBY_FORM_URL = '/static/standby_register.html';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        STANDBY_FORM_URL,
        '/static/gtu_logo.png'
      ]);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Intercept registration URLs
  if (url.pathname.includes('/register') && event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(async () => {
        // Network error / server down -> Serve cached standby form on same URL
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(STANDBY_FORM_URL);
        if (cachedResponse) {
          return cachedResponse;
        }
        return new Response('Server Offline. Standby form loading failed.', { status: 503 });
      })
    );
  }
});

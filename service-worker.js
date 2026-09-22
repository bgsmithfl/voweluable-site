// Voweluable service worker
// Bump CACHE_NAME on every deploy that changes index.html or any cached asset,
// so returning players get the new version instead of a stale cached one.
const CACHE_NAME = 'voweluable-v15';

const APP_SHELL = [
  '/',
  '/index.html',
  '/site.webmanifest',
  '/favicon.ico',
  '/favicon-16.png',
  '/favicon-32.png',
  '/favicon-48.png',
  '/favicon-180.png',
  '/favicon-192.png',
  '/favicon-512.png',
  '/social-share.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .catch(() => {}) // don't fail install if one asset is briefly unavailable
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

// Stale-while-revalidate: serve instantly from cache when available (fast
// repeat loads, works offline), while quietly refreshing the cache from the
// network in the background so the next visit gets the latest version.
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const networkFetch = fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          }
          return response;
        })
        .catch(() => cached);
      return cached || networkFetch;
    })
  );
});

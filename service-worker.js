// Voweluable service worker
// Bump CACHE_NAME on every deploy that changes index.html or any cached asset,
// so returning players get the new version instead of a stale cached one.
const CACHE_NAME = 'voweluable-v16';

// Static assets that rarely change — safe to serve cache-first for speed.
const APP_SHELL = [
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

// Is this a request for the game page itself (HTML)?
function isPageRequest(request) {
  if (request.mode === 'navigate') return true;
  const url = new URL(request.url);
  return url.pathname === '/' || url.pathname.endsWith('.html');
}

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  // NETWORK-FIRST for the game page: an online player ALWAYS gets today's
  // rules and pricing. Only fall back to cache when the network is unreachable
  // (offline). This prevents a returning player from being served a stale,
  // outdated copy of the game that plays under old pricing.
  if (isPageRequest(event.request)) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() =>
          // Offline: serve the last-known page, or the cached root as a fallback.
          caches.match(event.request).then((cached) => cached || caches.match('/'))
        )
    );
    return;
  }

  // CACHE-FIRST for static assets (icons, manifest): fast, offline-friendly,
  // and refreshed in the background so the next load stays current.
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const networkFetch = fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => cached);
      return cached || networkFetch;
    })
  );
});

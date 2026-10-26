// 매크로 대시보드 서비스워커
// 대시보드(HTML)는 '네트워크 우선' → 항상 최신, 오프라인일 때만 캐시.
// 정적 자산(아이콘·매니페스트)은 '캐시 우선 + 백그라운드 갱신'.
const CACHE = 'macro-dashboard-v2';
const ASSETS = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS).catch(() => {})));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const accept = req.headers.get('accept') || '';
  const isDoc = req.mode === 'navigate' || accept.includes('text/html');

  if (isDoc) {
    // 네트워크 우선: 최신 대시보드를 받아오고, 실패(오프라인)하면 캐시.
    e.respondWith(
      fetch(req)
        .then((resp) => {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return resp;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match('index.html')))
    );
  } else {
    // 정적 자산: 캐시 우선, 뒤에서 갱신.
    e.respondWith(
      caches.open(CACHE).then((c) =>
        c.match(req).then((cached) => {
          const net = fetch(req)
            .then((resp) => { c.put(req, resp.clone()); return resp; })
            .catch(() => cached);
          return cached || net;
        })
      )
    );
  }
});

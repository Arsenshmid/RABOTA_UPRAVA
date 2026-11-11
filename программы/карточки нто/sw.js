// Карточки 76п — офлайн-кэш (stale-while-revalidate)
const CACHE = "nto76-v1";
const ASSETS = ["./", "./index.html"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // GitHub API и всё внешнее — только сеть, не кэшируем
  if (url.origin !== location.origin) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(req);
    const net = fetch(req).then((res) => {
      if (res && res.ok && res.type === "basic") cache.put(req, res.clone());
      return res;
    }).catch(() => null);
    if (cached) return cached;      // офлайн и быстро: из кэша, обновление в фоне
    const res = await net;
    return res || new Response("Оффлайн: открой сайт один раз при интернете, дальше он заработает из кэша.", {
      status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" }
    });
  })());
});

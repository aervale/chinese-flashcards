/* Service worker: offline app shell + runtime caching of audio/images. */
const CACHE = "chinese-flashcards-v2";
const CORE = [
  "./",
  "index.html",
  "texts.js",
  "manifest.webmanifest",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/apple-touch-icon.png",
  "img/city1.jpg",
  "img/city2.jpg",
  "img/city3.jpg"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.allSettled(CORE.map(u => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return; // let cross-origin (online TTS) pass through
  e.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req).then(resp => {
        // runtime-cache successful same-origin GETs (audio clips become offline once played)
        if (resp && resp.ok && (resp.type === "basic" || resp.type === "default")) {
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
        }
        return resp;
      }).catch(() => hit);
    })
  );
});

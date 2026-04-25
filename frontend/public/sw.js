/* Bytloop POS service worker.
 *
 * Strategy:
 *   - Static app shell + same-origin GET assets: stale-while-revalidate —
 *     cashiers load instantly on flaky Wi-Fi, updates fetch in background.
 *   - API (same-origin /api/* and cross-origin to NEXT_PUBLIC_API_BASE_URL):
 *     network-first with no caching of mutating requests. GET reads get a
 *     last-resort cached fallback so the cashier can still see the last
 *     known product list while offline.
 *   - Writes (POST/PATCH/PUT/DELETE): pass through. The app-layer IndexedDB
 *     queue (src/lib/offline/queue.ts) handles replay, not the SW — doing it
 *     here too would race and double-enqueue. Idempotency keys protect either
 *     path but app-layer control lets the operator see the queue via
 *     /ops/offline-queue.
 *
 * Versioned cache name: bumping CACHE_VERSION invalidates stale assets on
 * the next activate. Do this whenever the bundle fingerprint strategy
 * changes — Next.js hashes filenames so you rarely need to.
 */

const CACHE_VERSION = "v1";
const SHELL_CACHE = `bytloop-shell-${CACHE_VERSION}`;
const API_GET_CACHE = `bytloop-api-${CACHE_VERSION}`;

// Bare minimum for the app shell. Anything else is filled on demand via SWR.
const SHELL_ASSETS = ["/", "/dashboard", "/pos", "/offline.html", "/manifest.webmanifest"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) =>
      cache.addAll(
        SHELL_ASSETS.map(
          (path) => new Request(path, { credentials: "same-origin" }),
        ),
      ).catch(() => {
        // Shell asset miss isn't fatal — SWR will fill them next navigation.
      }),
    ),
  );
  // Activate a new SW immediately so version bumps take effect on reload.
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((k) => !k.endsWith(CACHE_VERSION))
          .map((k) => caches.delete(k)),
      );
      await self.clients.claim();
    })(),
  );
});

function isApiRequest(url) {
  if (url.pathname.startsWith("/api/")) return true;
  // Cross-origin API calls route through NEXT_PUBLIC_API_BASE_URL, which at
  // build time could be any host. Heuristic: non-GET or `/auth/`/`/orders/`
  // etc. against an origin other than this one. We keep it conservative:
  // treat any cross-origin request that advertises JSON as API.
  if (url.origin !== self.location.origin) {
    return true;
  }
  return false;
}

function isMutation(method) {
  return method === "POST" || method === "PATCH" || method === "PUT" || method === "DELETE";
}

async function networkFirstWithCacheFallback(request) {
  const cache = await caches.open(API_GET_CACHE);
  try {
    const fresh = await fetch(request);
    if (fresh.ok && request.method === "GET") {
      // Clone before handing off — response body is a one-shot stream.
      cache.put(request, fresh.clone()).catch(() => {});
    }
    return fresh;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) {
      // Tag the replay so the app knows it's stale.
      const headers = new Headers(cached.headers);
      headers.set("x-sw-stale", "true");
      return new Response(await cached.clone().text(), {
        status: cached.status,
        statusText: cached.statusText,
        headers,
      });
    }
    throw err;
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(SHELL_CACHE);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone()).catch(() => {});
      return response;
    })
    .catch(() => null);
  return cached ?? (await networkPromise) ?? fetch(request);
}

async function offlineShell() {
  const cache = await caches.open(SHELL_CACHE);
  return (
    (await cache.match("/offline.html")) ??
    new Response(
      "<!DOCTYPE html><title>Offline</title><h1>Offline</h1><p>Sales are being queued locally.</p>",
      { status: 503, headers: { "content-type": "text/html" } },
    )
  );
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Never touch mutations — the in-app queue owns those.
  if (isMutation(request.method)) return;

  // Navigations (document requests): try network, fall back to shell, then
  // to a friendly offline page as last resort.
  if (request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          return await fetch(request);
        } catch {
          const cache = await caches.open(SHELL_CACHE);
          return (await cache.match(request)) ?? (await offlineShell());
        }
      })(),
    );
    return;
  }

  if (isApiRequest(url)) {
    event.respondWith(networkFirstWithCacheFallback(request));
    return;
  }

  // Static assets (JS/CSS/images/fonts) — SWR is ideal here.
  event.respondWith(staleWhileRevalidate(request));
});

// When the runtime tells us the IndexedDB queue has items, we can try to
// wake up the main thread — but since the app's sync loop already polls,
// this is mostly redundant. Kept for future Background Sync API wiring.
self.addEventListener("sync", (event) => {
  if (event.tag === "drain-offline-queue") {
    // No-op: the app handles draining. Present so the registration call
    // in the app doesn't throw when scheduling.
  }
});

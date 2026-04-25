/**
 * Service worker lifecycle. Call ``registerServiceWorker`` once at app boot.
 * Safe no-op in dev (SW only registers in production bundles) and during SSR.
 */

export async function registerServiceWorker(): Promise<void> {
  if (typeof window === "undefined") return;
  if (!("serviceWorker" in navigator)) return;
  // Disable in dev — the Next.js dev server serves fresh bundles each reload
  // and a stale SW will serve the old chunks forever.
  if (process.env.NODE_ENV !== "production") return;

  try {
    const reg = await navigator.serviceWorker.register("/sw.js", { scope: "/" });

    // Re-check every 30 min so long-running tablets pick up deploys.
    window.setInterval(() => {
      void reg.update();
    }, 30 * 60 * 1000);

    // Ask for a background-sync registration so the browser can wake us
    // when connectivity returns. Not all browsers support it (Safari) —
    // the app-level poll in src/lib/offline/sync.ts is the belt-and-braces.
    const syncManager = (
      reg as ServiceWorkerRegistration & {
        sync?: { register: (tag: string) => Promise<void> };
      }
    ).sync;
    if (syncManager) {
      try {
        await syncManager.register("drain-offline-queue");
      } catch {
        // Permission denied or unsupported — fine.
      }
    }
  } catch {
    // Registration failures shouldn't crash the app. Logged by the browser.
  }
}

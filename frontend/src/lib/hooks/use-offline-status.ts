"use client";

import { useEffect, useState } from "react";

import { countDeadLettered, countPending } from "@/lib/offline/queue";

/**
 * Live view of the offline state — online/offline + pending + dead-lettered
 * counts. Polls the IndexedDB queue on a short interval so the banner stays
 * fresh without wiring a pub/sub across every enqueue site.
 */
export function useOfflineStatus(): {
  readonly online: boolean;
  readonly pending: number;
  readonly deadLettered: number;
} {
  // Match SSR: always `true` until mounted, then read `navigator.onLine`.
  // Otherwise server renders no banner and offline clients render the banner first paint → hydration error.
  const [online, setOnline] = useState(true);
  const [pending, setPending] = useState(0);
  const [deadLettered, setDeadLettered] = useState(0);

  useEffect(() => {
    setOnline(navigator.onLine);
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      try {
        const [p, d] = await Promise.all([countPending(), countDeadLettered()]);
        if (!cancelled) {
          setPending(p);
          setDeadLettered(d);
        }
      } catch {
        // IndexedDB hiccups — don't crash the UI.
      }
    };
    void refresh();
    const id = window.setInterval(refresh, 5_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return { online, pending, deadLettered };
}

"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useRef } from "react";

import { useCartStore } from "@/lib/stores/cart-store";

/** Reset cart and bounce to welcome after this much inactivity (ms). */
const IDLE_MS = 60_000;

const RESET_EVENTS: readonly (keyof WindowEventMap)[] = [
  "pointerdown",
  "pointermove",
  "keydown",
  "touchstart",
  "wheel",
];

export function KioskShell({ children }: { readonly children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const clear = useCartStore((s) => s.clear);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    // Welcome + checkout screens never reset (idle there just means no one
    // has walked up yet — that's fine). Only arm the timer on product /
    // cart screens.
    const armable = pathname?.startsWith("/kiosk") && pathname !== "/kiosk";
    if (!armable) return;

    const schedule = () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = window.setTimeout(() => {
        clear();
        router.push("/kiosk");
      }, IDLE_MS);
    };

    schedule();
    for (const event of RESET_EVENTS) {
      window.addEventListener(event, schedule, { passive: true });
    }
    return () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
      for (const event of RESET_EVENTS) {
        window.removeEventListener(event, schedule);
      }
    };
  }, [pathname, router, clear]);

  return (
    <div
      className="min-h-screen w-full overflow-x-hidden bg-background text-foreground"
      // Kiosk: soft-swallow context menu + text selection so a fat-finger
      // doesn't open dev tools / "copy link" dialogs. The browser still
      // respects `--kiosk` flag which is what actually locks it down.
      onContextMenu={(e) => e.preventDefault()}
      style={{ userSelect: "none", WebkitUserSelect: "none" }}
    >
      {children}
    </div>
  );
}

/**
 * Kiosk route-group layout.
 *
 * Stripped-down chrome: no sidebar, no staff links, full-screen. Wraps the
 * tree in an idle watcher that resets the cart and returns to the welcome
 * screen after inactivity. Exit requires a staff PIN via `/kiosk/exit`.
 *
 * Unlike ``(auth)`` this layout deliberately does NOT require auth — the
 * kiosk boots directly into self-serve. Security boundary: the staff PIN
 * and the tenant subdomain of the URL. Kiosks should run on locked-down
 * Chromium (`--kiosk --disable-pinch`) so the user can't navigate away.
 */

import type { Metadata } from "next";
import type { ReactNode } from "react";

import { KioskShell } from "@/components/modules/kiosk/kiosk-shell";

/** Kiosk entry URLs are not catalog pages for search engines. */
export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function KioskLayout({ children }: { readonly children: ReactNode }) {
  return <KioskShell>{children}</KioskShell>;
}

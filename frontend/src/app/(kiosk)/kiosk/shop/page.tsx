import type { Metadata } from "next";

import { KioskProductGrid } from "@/components/modules/kiosk/kiosk-product-grid";
import { KioskCartSummary } from "@/components/modules/kiosk/kiosk-cart-summary";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Shop",
  path: "/kiosk/shop",
  noindex: true,
});

export default function KioskShopPage() {
  return (
    <section className="flex min-h-screen flex-col lg:flex-row">
      <div className="flex-1 overflow-y-auto p-6">
        <h1 className="mb-4 text-2xl font-semibold tracking-tight">Menu</h1>
        <KioskProductGrid />
      </div>
      <aside className="w-full border-t border-border bg-surface p-6 lg:w-96 lg:border-l lg:border-t-0">
        <KioskCartSummary />
      </aside>
    </section>
  );
}

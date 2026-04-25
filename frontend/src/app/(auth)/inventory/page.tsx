import type { Metadata } from "next";

import { InventoryList } from "@/components/modules/inventory/inventory-list";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Inventory",
  path: "/inventory",
  noindex: true,
});

export default function InventoryPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Inventory</h1>
        <p className="text-sm text-muted-foreground">
          Stock levels across your locations. Low-stock rows are flagged; transfer
          or adjust inline.
        </p>
      </header>
      <InventoryList />
    </section>
  );
}

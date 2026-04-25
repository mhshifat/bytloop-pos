import type { Metadata } from "next";

import { FurnitureOrdersHub } from "@/components/modules/furniture/furniture-orders-hub";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Furniture & custom orders",
  path: "/verticals/furniture",
  noindex: true,
});

export default function FurniturePage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Furniture &amp; custom orders</h1>
        <p className="text-sm text-muted-foreground">
          Quote custom work, run production, mark ready, and mark delivered. Link to
          customer orders when the sale is booked separately.
        </p>
      </header>
      <FurnitureOrdersHub />
    </section>
  );
}

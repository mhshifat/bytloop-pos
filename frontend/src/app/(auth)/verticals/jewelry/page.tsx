import type { Metadata } from "next";

import { MetalRatesEditor } from "@/components/modules/jewelry/metal-rates-editor";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Jewelry",
  path: "/verticals/jewelry",
  noindex: true,
});

export default function JewelryPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Jewelry</h1>
        <p className="text-sm text-muted-foreground">
          Today&apos;s metal rates per (metal × karat). Product-level attributes
          (weight, wastage, making charge, certificate) live on each product&apos;s
          detail page.
        </p>
      </header>
      <MetalRatesEditor />
    </section>
  );
}

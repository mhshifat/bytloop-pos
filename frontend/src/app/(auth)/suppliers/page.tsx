import type { Metadata } from "next";

import { SuppliersSection } from "@/components/modules/procurement/suppliers-section";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Suppliers",
  path: "/suppliers",
  noindex: true,
});

export default function SuppliersPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Suppliers</h1>
        <p className="text-sm text-muted-foreground">Your procurement contact list.</p>
      </header>
      <SuppliersSection />
    </section>
  );
}

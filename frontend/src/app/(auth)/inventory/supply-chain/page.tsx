import type { Metadata } from "next";
import Link from "next/link";

import { SupplyChainPanel } from "@/components/modules/inventory/supply-chain-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Supply chain",
  path: "/inventory/supply-chain",
  noindex: true,
});

export default function SupplyChainPage() {
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/inventory">← Back to inventory</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Supply chain</h1>
        <p className="text-sm text-muted-foreground">
          Reorder recommendations, supplier mappings, and automated draft purchase orders.
        </p>
      </header>
      <SupplyChainPanel />
    </section>
  );
}


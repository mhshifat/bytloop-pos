import type { Metadata } from "next";
import Link from "next/link";

import { PoCreateForm } from "@/components/modules/procurement/po-create-form";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "New purchase order",
  path: "/purchase-orders/new",
  noindex: true,
});

export default function NewPurchaseOrderPage() {
  return (
    <section className="mx-auto max-w-4xl space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/purchase-orders">← Back to purchase orders</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">New purchase order</h1>
        <p className="text-sm text-muted-foreground">
          Send to supplier, then receive against it as stock arrives.
        </p>
      </header>
      <PoCreateForm />
    </section>
  );
}

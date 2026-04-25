import type { Metadata } from "next";
import Link from "next/link";
import { Plus } from "lucide-react";

import { PurchaseOrdersList } from "@/components/modules/procurement/purchase-orders-list";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Purchase orders",
  path: "/purchase-orders",
  noindex: true,
});

export default function PurchaseOrdersPage() {
  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Purchase orders</h1>
          <p className="text-sm text-muted-foreground">
            Track stock you&apos;ve ordered from suppliers.
          </p>
        </div>
        <Button asChild>
          <Link href="/purchase-orders/new" className="flex items-center gap-2">
            <Plus size={14} /> New purchase order
          </Link>
        </Button>
      </header>
      <PurchaseOrdersList />
    </section>
  );
}

import type { Metadata } from "next";
import Link from "next/link";

import { ReceiveForm } from "@/components/modules/procurement/receive-form";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Receive stock",
  path: "/purchase-orders",
  noindex: true,
});

type PageProps = {
  readonly params: Promise<{ readonly purchaseOrderId: string }>;
};

export default async function PurchaseOrderDetailPage({ params }: PageProps) {
  const { purchaseOrderId } = await params;
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/purchase-orders">← Back to purchase orders</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Receive stock</h1>
        <p className="text-sm text-muted-foreground">
          Enter received quantities per line. Inventory is updated atomically.
        </p>
      </header>
      <ReceiveForm purchaseOrderId={purchaseOrderId} />
    </section>
  );
}

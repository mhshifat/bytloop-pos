import type { Metadata } from "next";
import Link from "next/link";

import { OrderDetail } from "@/components/modules/sales/order-detail";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Order detail",
  path: "/orders",
  noindex: true,
});

type Props = {
  readonly params: Promise<{ readonly orderId: string }>;
};

export default async function OrderDetailPage({ params }: Props) {
  const { orderId } = await params;
  return (
    <section className="mx-auto max-w-3xl space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/orders">← Back to orders</Link>
      </Button>
      <OrderDetail orderId={orderId} />
    </section>
  );
}

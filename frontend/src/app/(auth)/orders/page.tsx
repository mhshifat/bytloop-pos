import type { Metadata } from "next";
import { Download } from "lucide-react";

import { OrdersList } from "@/components/modules/sales/orders-list";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const metadata: Metadata = buildMetadata({
  title: "Orders",
  path: "/orders",
  noindex: true,
});

export default function OrdersPage() {
  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Orders</h1>
          <p className="text-sm text-muted-foreground">All recent sales.</p>
        </div>
        <Button asChild variant="outline" size="sm">
          <a href={`${API_BASE}/orders/export.csv`} download>
            <Download size={14} /> Export CSV
          </a>
        </Button>
      </header>
      <OrdersList />
    </section>
  );
}

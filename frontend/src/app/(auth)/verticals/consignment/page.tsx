import type { Metadata } from "next";

import { ConsignmentHub } from "@/components/modules/consignment/consignment-hub";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Thrift & consignment",
  path: "/verticals/consignment",
  noindex: true,
});

export default function ConsignmentPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Thrift & consignment</h1>
        <p className="text-sm text-muted-foreground">
          Consignors, floor listings, returns, and payouts. Mark-sold is typically tied to
          POS; use the API for advanced flows.
        </p>
      </header>
      <ConsignmentHub />
    </section>
  );
}

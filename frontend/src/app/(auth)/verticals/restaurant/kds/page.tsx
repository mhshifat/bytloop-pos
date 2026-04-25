import type { Metadata } from "next";

import { KdsBoard } from "@/components/modules/restaurant/kds-board";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Kitchen display",
  path: "/verticals/restaurant/kds",
  noindex: true,
});

export default function KdsPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Kitchen display</h1>
        <p className="text-sm text-muted-foreground">
          Tickets fired from the POS land here in real time.
        </p>
      </header>
      <KdsBoard />
    </section>
  );
}

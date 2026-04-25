import type { Metadata } from "next";

import { TablesGrid } from "@/components/modules/restaurant/tables-grid";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Tables",
  path: "/verticals/restaurant/tables",
  noindex: true,
});

export default function TablesPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Tables</h1>
        <p className="text-sm text-muted-foreground">
          Dining room layout. Tap a table to seat a party.
        </p>
      </header>
      <TablesGrid />
    </section>
  );
}

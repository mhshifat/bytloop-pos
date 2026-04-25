import type { Metadata } from "next";

import { StationRoutesEditor } from "@/components/modules/restaurant/station-routes-editor";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Station routing",
  path: "/verticals/restaurant/routes",
  noindex: true,
});

export default function StationRoutesPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Station routing</h1>
        <p className="text-sm text-muted-foreground">
          Map each dish to the station that prepares it (kitchen, bar, dessert…)
          and its course order. The KDS uses these rules when firing an order.
        </p>
      </header>
      <StationRoutesEditor />
    </section>
  );
}

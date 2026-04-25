import type { Metadata } from "next";

import { OfflineQueueInspector } from "@/components/modules/ops/offline-queue-inspector";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Offline queue",
  path: "/ops/offline-queue",
  noindex: true,
});

export default function OfflineQueuePage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Offline queue</h1>
        <p className="text-sm text-muted-foreground">
          Mutations queued on this device while offline. Dead-lettered items
          need manual review — retry after fixing the underlying cause, or
          discard if the sale was already entered another way.
        </p>
      </header>
      <OfflineQueueInspector />
    </section>
  );
}

import type { Metadata } from "next";

import { PluginMarketplace } from "@/components/modules/admin/plugin-marketplace";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Plugins",
  path: "/plugins",
  noindex: true,
});

export default function PluginsPage() {
  return (
    <section className="space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Plugins</h1>
        <p className="text-sm text-muted-foreground">
          Extend your POS with hooks into sales, customers, inventory, and
          more. Toggle to enable — changes take effect on the next event.
        </p>
      </header>
      <PluginMarketplace />
    </section>
  );
}

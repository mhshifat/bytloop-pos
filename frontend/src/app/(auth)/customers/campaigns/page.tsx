import type { Metadata } from "next";
import Link from "next/link";

import { CampaignsPanel } from "@/components/modules/customers/campaigns-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Campaign triggers",
  path: "/customers/campaigns",
  noindex: true,
});

export default function CustomerCampaignsPage() {
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/customers">← Back to customers</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Campaign triggers</h1>
        <p className="text-sm text-muted-foreground">
          Configure automated churn-risk email cadences (SMTP) for your segments.
        </p>
      </header>
      <CampaignsPanel />
    </section>
  );
}


import type { Metadata } from "next";
import Link from "next/link";

import { ShelfAuditPanel } from "@/components/modules/inventory/shelf-audit-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Shelf label price audit",
  path: "/inventory/shelf-audit",
  noindex: true,
});

export default function ShelfAuditPage() {
  return (
    <section className="mx-auto max-w-4xl space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/inventory">← Back to inventory</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Shelf label price audit</h1>
        <p className="text-sm text-muted-foreground">
          Upload a shelf photo, extract label prices, and compare them with POS prices.
        </p>
      </header>
      <ShelfAuditPanel />
    </section>
  );
}


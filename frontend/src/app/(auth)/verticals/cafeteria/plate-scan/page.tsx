import type { Metadata } from "next";
import Link from "next/link";

import { CafeteriaPlateScanPanel } from "@/components/modules/cafeteria/cafeteria-plate-scan-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Cafeteria plate scan",
  path: "/verticals/cafeteria/plate-scan",
  noindex: true,
});

export default function CafeteriaPlateScanPage() {
  return (
    <section className="mx-auto max-w-4xl space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/pos">← Back to POS</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Cafeteria plate scan (MVP)</h1>
        <p className="text-sm text-muted-foreground">
          Upload a tray photo to get draft cart suggestions, then confirm before ringing up.
        </p>
      </header>
      <CafeteriaPlateScanPanel />
    </section>
  );
}


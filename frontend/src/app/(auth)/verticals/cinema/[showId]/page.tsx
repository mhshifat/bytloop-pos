import type { Metadata } from "next";
import Link from "next/link";

import { SeatMap } from "@/components/modules/cinema/seat-map";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Show",
  path: "/verticals/cinema",
  noindex: true,
});

type PageProps = {
  readonly params: Promise<{ readonly showId: string }>;
};

export default async function ShowDetailPage({ params }: PageProps) {
  const { showId } = await params;
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/verticals/cinema">← Back to shows</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Seat map</h1>
        <p className="text-sm text-muted-foreground">
          Click to hold or sell. Sold seats are locked.
        </p>
      </header>
      <SeatMap showId={showId} />
    </section>
  );
}

import type { Metadata } from "next";
import Link from "next/link";

import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Resort",
  path: "/verticals/resort",
  noindex: true,
});

/**
 * Tier B profile `hospitality_resort` shares the hotel PMS-style module (see docs/verticals-coverage.md).
 */
export default function ResortPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Resort</h1>
        <p className="text-sm text-muted-foreground">
          Resort operations in this app use the same <strong>Hotel</strong> vertical (rooms, nightly
          rates, reservations). Set <strong>Business type</strong> to <strong>Resort</strong> in
          Settings for POS/mode copy; use the link below for property operations.
        </p>
        <p className="pt-2">
          <Link
            className="inline-flex items-center text-sm font-medium text-primary underline"
            href="/verticals/hotel"
          >
            Open Hotel &amp; rooms module &rarr;
          </Link>
        </p>
      </header>
    </section>
  );
}

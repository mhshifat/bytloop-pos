"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { isApiError } from "@/lib/api/error";
import { listProducts } from "@/lib/api/catalog";
import { formatMoney } from "@/lib/utils/money";

/**
 * Apparel module hub: pick a product to edit size × color matrix (Tier A partial per docs/verticals-coverage.md).
 */
export default function ApparelHubPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["products", { apparelHub: true }],
    queryFn: () => listProducts({ pageSize: 100, page: 1 }),
  });

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Apparel &mdash; variant matrix</h1>
        <p className="text-sm text-muted-foreground">
          Open a product to generate size &times; color SKUs, assign barcodes, and track per-variant
          stock. The POS can scan a variant when business type is <strong>Apparel</strong>.
        </p>
        <p className="pt-1 text-sm">
          <Link className="text-primary underline" href="/products">
            All products
          </Link>{" "}
          &middot;{" "}
          <Link className="text-primary underline" href="/pos">
            Open POS
          </Link>
        </p>
      </header>
      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No products"
          description="Add a product, then return here to open its variant matrix."
        />
      ) : (
        <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((p) => (
            <li key={p.id}>
              <Link
                href={`/verticals/apparel/${p.id}`}
                className="flex flex-col rounded-lg border border-border bg-card p-4 text-left transition hover:bg-muted/30"
              >
                <span className="text-sm font-medium text-foreground">{p.name}</span>
                <span className="mt-1 text-xs text-muted-foreground">SKU {p.sku}</span>
                <span className="mt-2 text-sm font-semibold tabular-nums">
                  {formatMoney(p.priceCents, p.currency)}
                </span>
                <span className="mt-2 text-xs text-primary">Open variant matrix &rarr;</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

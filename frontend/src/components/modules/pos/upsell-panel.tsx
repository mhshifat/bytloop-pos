"use client";

import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/shared/ui/button";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { nextBestOffers } from "@/lib/api/personalization";
import { useCartStore } from "@/lib/stores/cart-store";
import { formatMoney } from "@/lib/utils/money";

export function UpsellPanel() {
  const lines = useCartStore((s) => s.lines);
  const addLine = useCartStore((s) => s.addLine);
  const anchor = lines[lines.length - 1]?.productId ?? null;

  const { data, isLoading } = useQuery({
    queryKey: ["p13n", "next-best-offers", anchor],
    queryFn: () => nextBestOffers({ productId: anchor!, limit: 4 }),
    enabled: Boolean(anchor),
    staleTime: 1000 * 60 * 5,
  });

  if (!anchor) return null;
  if (isLoading) {
    return (
      <div className="border-t border-border px-4 py-3">
        <SkeletonCard lines={2} />
      </div>
    );
  }
  const items = data?.items ?? [];
  if (items.length === 0) return null;

  return (
    <div className="border-t border-border px-4 py-3">
      <p className="text-xs font-medium text-muted-foreground">Often bought with</p>
      <div className="mt-2 grid gap-2">
        {items.map((p) => (
          <div key={p.productId} className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{p.name}</p>
              <p className="text-xs text-muted-foreground">
                {p.sku} · {formatMoney(p.priceCents, p.currency)}
              </p>
            </div>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() =>
                addLine({
                  productId: p.productId,
                  name: p.name,
                  unitPriceCents: p.priceCents,
                  currency: p.currency,
                })
              }
            >
              Add
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}


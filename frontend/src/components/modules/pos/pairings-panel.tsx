"use client";

import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/shared/ui/button";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { getProduct } from "@/lib/api/catalog";
import { getPairings } from "@/lib/api/pairings";
import { VerticalProfile } from "@/lib/enums/vertical-profile";
import { useCartStore } from "@/lib/stores/cart-store";
import { formatMoney } from "@/lib/utils/money";

export function PairingsPanel(props: { readonly verticalProfile: string }) {
  const lines = useCartStore((s) => s.lines);
  const addLine = useCartStore((s) => s.addLine);
  const anchor = lines[lines.length - 1]?.productId ?? null;

  const enabled = props.verticalProfile === VerticalProfile.FNB_RESTAURANT && Boolean(anchor);
  const q = useQuery({
    queryKey: ["p13n", "pairings", anchor],
    queryFn: () => getPairings({ foodProductId: anchor! }),
    enabled,
    staleTime: 1000 * 60 * 10,
  });

  const ids = q.data?.suggestedDrinkProductIds ?? [];

  const prodsQ = useQuery({
    queryKey: ["p13n", "pairings", "products", ids.join(",")],
    queryFn: async () => Promise.all(ids.map((id) => getProduct(id))),
    enabled: enabled && ids.length > 0,
  });

  if (!enabled) return null;
  if (q.isLoading) {
    return (
      <div className="border-t border-border px-4 py-3">
        <SkeletonCard lines={2} />
      </div>
    );
  }
  if (!q.data || ids.length === 0) return null;

  return (
    <div className="border-t border-border px-4 py-3">
      <p className="text-xs font-medium text-muted-foreground">Suggested pairings</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{q.data.rationale}</p>
      <div className="mt-2 grid gap-2">
        {(prodsQ.data ?? []).map((p) => (
          <div key={p.id} className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{p.name}</p>
              <p className="text-xs text-muted-foreground">{formatMoney(p.priceCents, p.currency)}</p>
            </div>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() =>
                addLine({
                  productId: p.id,
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


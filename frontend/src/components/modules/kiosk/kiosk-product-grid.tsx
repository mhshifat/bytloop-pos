"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { CategoryPicker } from "@/components/shared/category-picker";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SearchFilter } from "@/components/shared/search-filter";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Card } from "@/components/shared/ui/card";
import { isApiError } from "@/lib/api/error";
import { listProducts } from "@/lib/api/catalog";
import { useCurrency } from "@/lib/hooks/use-currency";
import { useCartStore } from "@/lib/stores/cart-store";
import { formatMoney } from "@/lib/utils/money";

export function KioskProductGrid() {
  const { currency } = useCurrency();
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const addLine = useCartStore((s) => s.addLine);

  const { data, isLoading, error } = useQuery({
    queryKey: ["kiosk", "products", { search, categoryId }],
    queryFn: () =>
      listProducts({
        search: search || undefined,
        categoryId: categoryId ?? undefined,
        pageSize: 60,
      }),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <SearchFilter value={search} onChange={setSearch} placeholder="Search menu…" />
        <CategoryPicker value={categoryId} onChange={setCategoryId} />
      </div>

      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState title="Nothing matches" description="Try another search." />
      ) : (
        <div className="grid auto-rows-fr grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
          {data.items.map((p) => (
            <Card
              key={p.id}
              role="button"
              tabIndex={0}
              aria-label={`Add ${p.name} to cart`}
              onClick={() =>
                addLine({
                  productId: p.id,
                  name: p.name,
                  unitPriceCents: p.priceCents,
                  currency: p.currency,
                })
              }
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  addLine({
                    productId: p.id,
                    name: p.name,
                    unitPriceCents: p.priceCents,
                    currency: p.currency,
                  });
                }
              }}
              className="flex min-h-[7rem] cursor-pointer flex-col justify-between gap-2 p-4 transition-transform active:scale-[0.98] hover:border-primary/60"
            >
              <div className="text-base font-medium leading-tight">{p.name}</div>
              <div className="text-lg font-semibold tabular-nums">
                {formatMoney(p.priceCents, p.currency || currency)}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

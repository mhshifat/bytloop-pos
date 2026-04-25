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
import { useLocale } from "next-intl";
import { useTranslatedText } from "@/lib/hooks/use-translated-text";
import { useCartStore } from "@/lib/stores/cart-store";
import { formatMoney } from "@/lib/utils/money";

export function KioskProductGrid() {
  const { currency } = useCurrency();
  const locale = useLocale();
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
            <KioskProductCard key={p.id} locale={locale} product={p} currencyFallback={currency} onAdd={() => addLine({
              productId: p.id,
              name: p.name,
              unitPriceCents: p.priceCents,
              currency: p.currency,
            })} />
          ))}
        </div>
      )}
    </div>
  );
}

function KioskProductCard({
  product,
  onAdd,
  currencyFallback,
  locale,
}: {
  readonly product: { readonly id: string; readonly name: string; readonly description: string | null; readonly priceCents: number; readonly currency: string };
  readonly onAdd: () => void;
  readonly currencyFallback: string;
  readonly locale: string;
}) {
  const nameQ = useTranslatedText(product.name, locale);
  const descQ = useTranslatedText(product.description, locale);

  return (
            <Card
              role="button"
              tabIndex={0}
              aria-label={`Add ${product.name} to cart`}
              onClick={onAdd}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onAdd();
                }
              }}
              className="flex min-h-[7rem] cursor-pointer flex-col justify-between gap-2 p-4 transition-transform active:scale-[0.98] hover:border-primary/60"
            >
              <div className="space-y-1">
                <div className="text-base font-medium leading-tight">
                  {nameQ.data ?? product.name}
                </div>
                {product.description ? (
                  <div className="line-clamp-2 text-xs text-muted-foreground">
                    {descQ.data ?? product.description}
                  </div>
                ) : null}
              </div>
              <div className="text-lg font-semibold tabular-nums">
                {formatMoney(product.priceCents, product.currency || currencyFallback)}
              </div>
            </Card>
  );
}

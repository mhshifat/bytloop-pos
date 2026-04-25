"use client";

import { Card } from "@/components/shared/ui/card";
import type { Product } from "@/lib/api/catalog";
import { formatMoney } from "@/lib/utils/money";

type ProductGridProps = {
  readonly products: readonly Product[];
  readonly onSelect: (product: Product) => void;
};

export function ProductGrid({ products, onSelect }: ProductGridProps) {
  return (
    <div className="grid auto-rows-fr grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((product) => (
        <Card
          key={product.id}
          tabIndex={0}
          role="button"
          aria-label={`Add ${product.name} to cart`}
          onClick={() => onSelect(product)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onSelect(product);
            }
          }}
          className="flex cursor-pointer flex-col justify-between gap-2 p-3 transition-colors hover:border-primary/60"
        >
          <div className="min-h-[2.5rem] text-sm font-medium leading-tight">{product.name}</div>
          <div className="text-xs text-muted-foreground">{product.sku}</div>
          <div className="text-base font-semibold">
            {formatMoney(product.priceCents, product.currency)}
          </div>
        </Card>
      ))}
    </div>
  );
}

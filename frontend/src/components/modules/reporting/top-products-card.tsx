"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { InlineError } from "@/components/shared/errors";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { isApiError } from "@/lib/api/error";
import { getTopProducts } from "@/lib/api/reports";
import { useCurrency } from "@/lib/hooks/use-currency";

export function TopProductsCard() {
  const { formatMoney } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", "top-products", 30, 5],
    queryFn: () => getTopProducts({ days: 30, limit: 5 }),
  });

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Top products · 30 days
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-20" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No sales in the last 30 days yet.
          </p>
        ) : (
          <ul className="space-y-2">
            {data.map((p) => (
              <li
                key={p.productId}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <Link
                  href={`/products/${p.productId}`}
                  className="min-w-0 flex-1 truncate hover:underline"
                  title={p.name}
                >
                  {p.name}
                </Link>
                <span className="tabular-nums text-xs text-muted-foreground">
                  {p.unitsSold} sold
                </span>
                <span className="tabular-nums font-medium">
                  {formatMoney(p.revenueCents)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

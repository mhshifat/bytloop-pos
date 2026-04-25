"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { isApiError } from "@/lib/api/error";
import { listOrders } from "@/lib/api/sales";
import { orderStatusLabel } from "@/lib/enums/order-status";
import { formatMoney } from "@/lib/utils/money";

export function RecentOrdersCard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["orders", "recent"],
    queryFn: () => listOrders({ page: 1, pageSize: 5 }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Recent orders
        </CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href="/orders">View all</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-20" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Ring up your first sale at the POS terminal.
          </p>
        ) : (
          <ul className="space-y-2">
            {data.items.map((o) => (
              <li key={o.id} className="flex items-center justify-between text-sm">
                <Link
                  href={`/orders/${o.id}`}
                  className="font-mono text-xs hover:underline"
                >
                  {o.number}
                </Link>
                <div className="flex items-center gap-3">
                  <EnumBadge
                    value={o.status}
                    getLabel={orderStatusLabel}
                    variant="outline"
                  />
                  <span className="tabular-nums">
                    {formatMoney(o.totalCents, o.currency)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

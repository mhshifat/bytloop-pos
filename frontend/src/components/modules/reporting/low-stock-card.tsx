"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import Link from "next/link";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { listInventoryLevels } from "@/lib/api/catalog";
import { isApiError } from "@/lib/api/error";

export function LowStockCard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["inventory", "levels", { page: 1, pageSize: 5 }],
    queryFn: () => listInventoryLevels({ page: 1, pageSize: 5 }),
  });

  const lowStock =
    data?.items.filter(
      (l) => l.reorderPoint > 0 && l.quantity <= l.reorderPoint,
    ) ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <AlertTriangle size={14} className="text-amber-400" aria-hidden="true" />
          Low stock
        </CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href="/inventory">View all</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-20" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : lowStock.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nothing to reorder right now.</p>
        ) : (
          <ul className="space-y-2">
            {lowStock.map((level) => (
              <li
                key={level.id}
                className="flex items-center justify-between text-sm"
              >
                <span>{level.productName}</span>
                <span className="tabular-nums text-amber-400">
                  {level.quantity} left
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

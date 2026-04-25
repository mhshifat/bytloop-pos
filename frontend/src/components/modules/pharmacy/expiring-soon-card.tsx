"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";

import { EntityLabel } from "@/components/shared/entity-label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { listExpiringBatches } from "@/lib/api/pharmacy";

export function ExpiringSoonCard() {
  const { data, isLoading } = useQuery({
    queryKey: ["pharmacy", "expiring", 90],
    queryFn: () => listExpiringBatches(90),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Expiring within 90 days
        </CardTitle>
        {data && data.length > 0 ? (
          <AlertTriangle size={16} className="text-amber-400" aria-hidden="true" />
        ) : null}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-20" />
        ) : !data || data.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nothing expiring soon.</p>
        ) : (
          <ul className="space-y-1.5">
            {data.map((b) => (
              <li
                key={b.id}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <EntityLabel id={b.productId} entity="product" />
                <span className="font-mono text-xs text-muted-foreground">
                  #{b.batchNo}
                </span>
                <span className="tabular-nums text-xs">{b.quantityRemaining} left</span>
                <span className="tabular-nums text-xs text-amber-400">
                  {new Date(b.expiryDate).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

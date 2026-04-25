"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { EntityLabel } from "@/components/shared/entity-label";
import { InlineError } from "@/components/shared/errors";
import { Badge } from "@/components/shared/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { Slider } from "@/components/shared/ui/slider";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { getChurnRisk } from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";
import { useCurrency } from "@/lib/hooks/use-currency";

export function ChurnRiskList() {
  const { formatMoney } = useCurrency();
  const [threshold, setThreshold] = useState<number>(0.6);

  const { data, isLoading, error } = useQuery({
    queryKey: ["ai", "churn-risk", threshold],
    queryFn: () => getChurnRisk(threshold),
  });

  const sorted = useMemo(() => {
    if (!data) return [];
    return [...data.customers].sort(
      (a, b) => b.churnProbability - a.churnProbability,
    );
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-3 text-sm font-medium text-muted-foreground">
          <span>Churn risk</span>
          <div className="flex min-w-[220px] items-center gap-3">
            <span className="text-xs">Threshold</span>
            <Slider
              value={[threshold]}
              min={0.3}
              max={0.9}
              step={0.05}
              onValueChange={(v) => {
                if (v[0] !== undefined) setThreshold(v[0]);
              }}
              className="w-40"
            />
            <span className="tabular-nums text-xs">
              {Math.round(threshold * 100)}%
            </span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : sorted.length === 0 ? (
          <EmptyState
            title="No at-risk customers"
            description="No customers exceed the selected churn threshold."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Days since last order</TableHead>
                <TableHead>Orders</TableHead>
                <TableHead>Total spent</TableHead>
                <TableHead>Churn probability</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((c) => (
                <TableRow key={c.customerId}>
                  <TableCell>
                    <Link
                      href={`/customers/${c.customerId}`}
                      className="hover:underline"
                    >
                      <EntityLabel id={c.customerId} entity="customer" />
                    </Link>
                  </TableCell>
                  <TableCell className="tabular-nums">
                    {c.daysSinceLastOrder}
                  </TableCell>
                  <TableCell className="tabular-nums">{c.orderCount}</TableCell>
                  <TableCell className="tabular-nums">
                    {formatMoney(c.totalSpentCents)}
                  </TableCell>
                  <TableCell>
                    <ChurnBadge value={c.churnProbability} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function ChurnBadge({ value }: { readonly value: number }) {
  const pct = `${Math.round(value * 100)}%`;
  if (value >= 0.75) {
    return (
      <Badge className="bg-red-500/20 text-red-300 border-red-500/40">
        {pct}
      </Badge>
    );
  }
  if (value >= 0.5) {
    return (
      <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/40">
        {pct}
      </Badge>
    );
  }
  return <Badge variant="secondary">{pct}</Badge>;
}

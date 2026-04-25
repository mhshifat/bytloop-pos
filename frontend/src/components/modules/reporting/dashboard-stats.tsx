"use client";

import { useQuery } from "@tanstack/react-query";

import { InlineError } from "@/components/shared/errors";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { isApiError } from "@/lib/api/error";
import { getDashboardReport } from "@/lib/api/reports";
import { useCurrency } from "@/lib/hooks/use-currency";

export function DashboardStats() {
  const { formatMoney } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", "dashboard"],
    queryFn: () => getDashboardReport(),
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  }
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data) return null;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      <Stat label="Revenue today" value={formatMoney(data.today.revenueCents)} />
      <Stat label="Orders today" value={String(data.today.orderCount)} />
      <Stat
        label="Revenue · 7 days"
        value={formatMoney(data.last7Days.revenueCents)}
      />
      <Stat label="Customers" value={String(data.customerCount)} />
      <Stat
        label="Low stock"
        value={String(data.lowStockCount)}
        emphasized={data.lowStockCount > 0}
      />
    </div>
  );
}

function Stat({
  label,
  value,
  emphasized = false,
}: {
  readonly label: string;
  readonly value: string;
  readonly emphasized?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p
          className={`text-3xl font-semibold tabular-nums ${
            emphasized ? "text-amber-400" : ""
          }`}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}

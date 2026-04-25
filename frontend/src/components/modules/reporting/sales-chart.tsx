"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { InlineError } from "@/components/shared/errors";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { isApiError } from "@/lib/api/error";
import { getSalesByDay } from "@/lib/api/reports";

type PointRow = {
  readonly day: string;
  readonly revenue: number;
  readonly orders: number;
};

export function SalesChart() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", "sales-by-day"],
    queryFn: () => getSalesByDay(14),
  });

  const rows: PointRow[] = useMemo(() => {
    return (data ?? []).map((p) => ({
      day: new Date(p.day).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      }),
      revenue: Number((p.revenueCents / 100).toFixed(2)),
      orders: p.orderCount,
    }));
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Revenue · last 14 days
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-52 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : rows.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Charge a sale to start seeing the trend.
          </p>
        ) : (
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="sales-gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis
                  dataKey="day"
                  stroke="#a1a1aa"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#a1a1aa"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  width={50}
                />
                <Tooltip
                  contentStyle={{
                    background: "#111113",
                    border: "1px solid #27272a",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  formatter={(v, name) => {
                    const n = v == null ? 0 : Number(v);
                    return [
                      name === "revenue" ? `BDT ${n.toFixed(2)}` : `${n} orders`,
                      name === "revenue" ? "Revenue" : "Orders",
                    ] as [string, string];
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="url(#sales-gradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

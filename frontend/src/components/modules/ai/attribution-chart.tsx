"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/shared/ui/card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { getAttribution } from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";
import { useCurrency } from "@/lib/hooks/use-currency";

type Row = {
  readonly channel: string;
  readonly revenue: number;
  readonly orders: number;
};

export function AttributionChart() {
  const { formatMoney } = useCurrency();
  const [windowDays, setWindowDays] = useState<number>(30);

  const { data, isLoading, error } = useQuery({
    queryKey: ["ai", "attribution", windowDays],
    queryFn: () => getAttribution(windowDays),
  });

  const rows: Row[] = useMemo(() => {
    if (!data) return [];
    return data.channels.map((c) => ({
      channel: c.channel,
      revenue: Number((c.attributedRevenueCents / 100).toFixed(2)),
      orders: c.attributedOrders,
    }));
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-3 text-sm font-medium text-muted-foreground">
          <span>Marketing attribution</span>
          <div className="flex items-end gap-2">
            <Label htmlFor="attribution-window" className="text-xs">
              Window (days)
            </Label>
            <Input
              id="attribution-window"
              type="number"
              min={1}
              max={365}
              value={windowDays}
              onChange={(e) => {
                const n = Number(e.target.value);
                if (Number.isFinite(n)) {
                  setWindowDays(Math.min(365, Math.max(1, Math.floor(n))));
                }
              }}
              className="h-8 w-24"
            />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : rows.length === 0 ? (
          <EmptyState
            title="No attribution data yet"
            description="Campaign touches are captured as customers arrive via UTM links."
          />
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={rows}
                layout="vertical"
                margin={{ top: 4, right: 48, left: 16, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#27272a"
                  horizontal={false}
                />
                <XAxis
                  type="number"
                  stroke="#a1a1aa"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="channel"
                  stroke="#a1a1aa"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  width={110}
                />
                <Tooltip
                  contentStyle={{
                    background: "#111113",
                    border: "1px solid #27272a",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  formatter={(value, _name, item) => {
                    const orders =
                      (item?.payload as Row | undefined)?.orders ?? 0;
                    return [
                      `${formatMoney(Math.round(Number(value) * 100))} · ${orders} orders`,
                      "Attributed",
                    ];
                  }}
                />
                <Bar dataKey="revenue" fill="#6366f1" radius={[0, 4, 4, 0]}>
                  <LabelList
                    dataKey="orders"
                    position="right"
                    formatter={(value: unknown) => `${String(value)} orders`}
                    fill="#a1a1aa"
                    fontSize={11}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

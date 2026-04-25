"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/shared/ui/card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import { Skeleton } from "@/components/shared/ui/skeleton";
import {
  type ForecastAccuracy,
  type ForecastMethod,
  getForecast,
  getForecastAccuracy,
} from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";
import { useCurrency } from "@/lib/hooks/use-currency";

type ChartRow = {
  readonly day: string;
  readonly revenue: number;
};

export function ForecastChart() {
  const { formatMoney } = useCurrency();
  const [method, setMethod] = useState<ForecastMethod>("seasonal_naive");
  const [horizonDays, setHorizonDays] = useState<number>(14);
  const [historyDays, setHistoryDays] = useState<number>(90);

  const { data, isLoading, error } = useQuery({
    queryKey: ["ai", "forecast", method, horizonDays, historyDays],
    queryFn: () =>
      getForecast({ method, horizonDays, historyDays }),
  });

  const accuracy = useMutation<ForecastAccuracy>({
    mutationFn: () => getForecastAccuracy({ historyDays }),
  });

  const rows: ChartRow[] = useMemo(() => {
    if (!data) return [];
    return data.points.map((p) => ({
      day: new Date(p.day).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      }),
      revenue: Number((p.forecastRevenueCents / 100).toFixed(2)),
    }));
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-3 text-sm font-medium text-muted-foreground">
          <span>Revenue forecast</span>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1">
              <Label htmlFor="forecast-method" className="text-xs">
                Method
              </Label>
              <Select
                value={method}
                onValueChange={(v) => setMethod(v as ForecastMethod)}
              >
                <SelectTrigger id="forecast-method" size="sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="seasonal_naive">Seasonal-naive</SelectItem>
                  <SelectItem value="prophet">Prophet</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="forecast-horizon" className="text-xs">
                Horizon (days)
              </Label>
              <Input
                id="forecast-horizon"
                type="number"
                min={1}
                max={90}
                value={horizonDays}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  if (Number.isFinite(n)) {
                    setHorizonDays(Math.min(90, Math.max(1, Math.floor(n))));
                  }
                }}
                className="h-8 w-24"
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="forecast-history" className="text-xs">
                History (days)
              </Label>
              <Input
                id="forecast-history"
                type="number"
                min={7}
                max={365}
                value={historyDays}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  if (Number.isFinite(n)) {
                    setHistoryDays(Math.min(365, Math.max(7, Math.floor(n))));
                  }
                }}
                className="h-8 w-24"
              />
            </div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : rows.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Not enough history to forecast yet.
          </p>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={rows}
                margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#27272a"
                  vertical={false}
                />
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
                  width={60}
                />
                <Tooltip
                  contentStyle={{
                    background: "#111113",
                    border: "1px solid #27272a",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  formatter={(v) => [
                    formatMoney(Math.round(Number(v) * 100)),
                    "Forecast",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <Button
            type="button"
            variant="outline"
            size="xs"
            onClick={() => accuracy.mutate()}
            disabled={accuracy.isPending}
          >
            {accuracy.isPending ? "Comparing…" : "Compare accuracy"}
          </Button>
          {accuracy.data ? (
            <span className="tabular-nums">
              Seasonal-naive: {formatMape(accuracy.data.seasonal_naive)} MAPE
              {" · "}
              Prophet: {formatMape(accuracy.data.prophet)} MAPE
            </span>
          ) : null}
          {accuracy.error && isApiError(accuracy.error) ? (
            <span className="text-red-400">{accuracy.error.message}</span>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function formatMape(v: number | null): string {
  if (v === null || !Number.isFinite(v)) return "—";
  return `${Math.round(v * 100)}%`;
}

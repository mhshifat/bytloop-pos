"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { Badge } from "@/components/shared/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/shared/ui/card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Skeleton } from "@/components/shared/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { getAnomalies } from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";
import { useCurrency } from "@/lib/hooks/use-currency";

export function AnomalyList() {
  const { formatMoney } = useCurrency();
  const [windowDays, setWindowDays] = useState<number>(60);

  const { data, isLoading, error } = useQuery({
    queryKey: ["ai", "anomalies", windowDays],
    queryFn: () => getAnomalies(windowDays),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-3 text-sm font-medium text-muted-foreground">
          <span>Sales anomalies</span>
          <div className="flex items-end gap-2">
            <Label htmlFor="anomaly-window" className="text-xs">
              Window (days)
            </Label>
            <Input
              id="anomaly-window"
              type="number"
              min={7}
              max={365}
              value={windowDays}
              onChange={(e) => {
                const n = Number(e.target.value);
                if (Number.isFinite(n)) {
                  setWindowDays(Math.min(365, Math.max(7, Math.floor(n))));
                }
              }}
              className="h-8 w-24"
            />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.anomalies.length === 0 ? (
          <EmptyState
            title="No anomalies detected"
            description="Your sales look healthy."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>When</TableHead>
                <TableHead>Revenue</TableHead>
                <TableHead>Severity</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.anomalies.map((a) => (
                <TableRow key={a.timestamp}>
                  <TableCell className="tabular-nums">
                    {new Date(a.timestamp).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </TableCell>
                  <TableCell className="tabular-nums">
                    {formatMoney(a.revenueCents)}
                  </TableCell>
                  <TableCell>
                    <SeverityBadge value={a.severity} />
                    {a.note ? (
                      <span className="ml-2 text-xs text-muted-foreground">
                        {a.note}
                      </span>
                    ) : null}
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

function SeverityBadge({ value }: { readonly value: number }) {
  const pct = `${Math.round(value * 100)}%`;
  if (value >= 0.7) {
    return (
      <Badge className="bg-red-500/20 text-red-300 border-red-500/40">
        {pct}
      </Badge>
    );
  }
  if (value >= 0.3) {
    return (
      <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/40">
        {pct}
      </Badge>
    );
  }
  return <Badge variant="secondary">{pct}</Badge>;
}

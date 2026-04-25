"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { Badge } from "@/components/shared/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { type BenchmarkPoint, getBenchmark } from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";

export function BenchmarkCard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["ai", "benchmark"],
    queryFn: () => getBenchmark(),
  });

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Peer benchmark
          {data?.vertical ? (
            <span className="ml-2 text-xs text-muted-foreground/80">
              · {data.vertical}
            </span>
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.points.length === 0 ? (
          <EmptyState
            title="Not enough peer data yet"
            description="We need 5+ peer tenants on the same business type."
          />
        ) : (
          <>
            {data.insight ? (
              <div className="flex items-start gap-2 rounded-md border border-border bg-muted/30 p-3 text-sm">
                <Sparkles
                  size={14}
                  className="mt-0.5 shrink-0 text-primary"
                  aria-hidden="true"
                />
                <p className="text-muted-foreground">{data.insight}</p>
              </div>
            ) : null}
            <ul className="space-y-3">
              {data.points.map((p) => (
                <BenchmarkRow key={p.metric} point={p} />
              ))}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function BenchmarkRow({ point }: { readonly point: BenchmarkPoint }) {
  const values = [
    point.tenantValue,
    point.peerP25,
    point.peerMedian,
    point.peerP75,
  ].filter((v) => Number.isFinite(v));
  const max = Math.max(1, ...values);
  const p25Pct = (point.peerP25 / max) * 100;
  const p75Pct = (point.peerP75 / max) * 100;
  const medianPct = (point.peerMedian / max) * 100;
  const tenantPct = Math.max(0, Math.min(100, (point.tenantValue / max) * 100));

  return (
    <li className="space-y-1.5">
      <div className="flex items-center justify-between gap-2 text-sm">
        <span className="font-medium">{point.metric}</span>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-[10px]">
            n={point.sampleSize}
          </Badge>
          <span className="tabular-nums text-xs text-muted-foreground">
            you {formatNumber(point.tenantValue)} · peer median{" "}
            {formatNumber(point.peerMedian)}
          </span>
        </div>
      </div>
      <div
        className="relative h-4 w-full rounded-full bg-muted"
        role="img"
        aria-label={`${point.metric}: tenant value ${point.tenantValue}, peer median ${point.peerMedian}`}
      >
        <div
          className="absolute top-0 h-full rounded-full bg-muted-foreground/30"
          style={{
            left: `${p25Pct}%`,
            width: `${Math.max(0, p75Pct - p25Pct)}%`,
          }}
          title={`Peer p25–p75: ${formatNumber(point.peerP25)}–${formatNumber(point.peerP75)}`}
        />
        <div
          className="absolute top-0 h-full w-0.5 bg-muted-foreground"
          style={{ left: `${medianPct}%` }}
          title={`Peer median: ${formatNumber(point.peerMedian)}`}
        />
        <div
          className="absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full border-2 border-background bg-primary"
          style={{
            left: `calc(${tenantPct}% - 6px)`,
          }}
          title={`You: ${formatNumber(point.tenantValue)}`}
        />
      </div>
    </li>
  );
}

function formatNumber(n: number): string {
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

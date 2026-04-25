"use client";

import { useQuery } from "@tanstack/react-query";

import { InlineError } from "@/components/shared/errors";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { getLifetimeValue } from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";
import { useCurrency } from "@/lib/hooks/use-currency";

type LtvCardProps = {
  readonly customerId: string;
};

export function LtvCard({ customerId }: LtvCardProps) {
  const { formatMoney } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ["ai", "ltv", customerId],
    queryFn: () => getLifetimeValue(customerId),
    enabled: Boolean(customerId),
  });

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Lifetime value
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-28 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data ? null : (
          <LtvBody
            past={data.past12moCents}
            predicted={data.predicted12moCents}
            confidence={data.confidence}
            formatMoney={formatMoney}
          />
        )}
      </CardContent>
    </Card>
  );
}

function LtvBody({
  past,
  predicted,
  confidence,
  formatMoney,
}: {
  readonly past: number;
  readonly predicted: number;
  readonly confidence: number;
  readonly formatMoney: (cents: number) => string;
}) {
  const ratio = past > 0 ? predicted / past : predicted > 0 ? Infinity : 1;
  const tone: "green" | "neutral" | "red" =
    ratio > 1.2 ? "green" : ratio < 0.8 ? "red" : "neutral";

  const dotClass =
    tone === "green"
      ? "bg-emerald-400"
      : tone === "red"
        ? "bg-red-400"
        : "bg-muted-foreground";
  const valueClass =
    tone === "green"
      ? "text-emerald-300"
      : tone === "red"
        ? "text-red-300"
        : "text-foreground";

  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between">
        <span className="text-xs uppercase tracking-wide text-muted-foreground">
          Past 12mo spend
        </span>
        <span className="tabular-nums font-medium">{formatMoney(past)}</span>
      </div>
      <div className="space-y-1">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
          <span className={`inline-block h-2 w-2 rounded-full ${dotClass}`} />
          Predicted next 12mo spend
        </div>
        <p className={`text-3xl font-semibold tabular-nums ${valueClass}`}>
          {formatMoney(predicted)}
        </p>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-xs uppercase tracking-wide text-muted-foreground">
          Confidence
        </span>
        <span className="tabular-nums font-medium">
          {Math.round(confidence * 100)}%
        </span>
      </div>
    </div>
  );
}

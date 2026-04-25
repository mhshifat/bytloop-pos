"use client";

import { useQuery } from "@tanstack/react-query";

import { InlineError } from "@/components/shared/errors";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { isApiError } from "@/lib/api/error";
import { getPaymentBreakdown } from "@/lib/api/reports";
import { paymentMethodLabel } from "@/lib/enums/payment-method";
import { useCurrency } from "@/lib/hooks/use-currency";

export function PaymentBreakdownCard() {
  const { formatMoney } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", "payment-breakdown", 30],
    queryFn: () => getPaymentBreakdown(30),
  });

  const total = data?.reduce((sum, p) => sum + p.amountCents, 0) ?? 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Payment mix · 30 days
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-20" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No completed payments yet.
          </p>
        ) : (
          <ul className="space-y-2">
            {data.map((p) => {
              const share = total > 0 ? p.amountCents / total : 0;
              return (
                <li key={p.method} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span>{paymentMethodLabel(p.method)}</span>
                    <span className="tabular-nums font-medium">
                      {formatMoney(p.amountCents)}
                    </span>
                  </div>
                  <div
                    className="h-1 overflow-hidden rounded-full bg-muted"
                    role="progressbar"
                    aria-valuenow={Math.round(share * 100)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div
                      className="h-full bg-primary"
                      style={{ width: `${Math.round(share * 100)}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

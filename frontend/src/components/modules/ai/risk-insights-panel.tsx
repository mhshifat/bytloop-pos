"use client";

import { useQuery } from "@tanstack/react-query";

import { getCashDrawerRisk, getRefundVoidAbuse, getSoftposAnomalies } from "@/lib/api/ai-risk";
import { Button } from "@/components/shared/ui/button";

function JsonCard(props: { readonly title: string; readonly data: unknown; readonly isLoading?: boolean; readonly error?: unknown }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium">{props.title}</p>
      </div>
      {props.isLoading ? (
        <p className="mt-2 text-sm text-muted-foreground">Loading…</p>
      ) : props.error ? (
        <p className="mt-2 text-sm text-destructive">Failed to load.</p>
      ) : (
        <pre className="mt-3 max-h-[22rem] overflow-auto rounded-md bg-muted p-3 text-xs">
          {JSON.stringify(props.data, null, 2)}
        </pre>
      )}
    </div>
  );
}

export function RiskInsightsPanel() {
  const refundVoid = useQuery({
    queryKey: ["ai-risk", "refund-void-abuse"],
    queryFn: () => getRefundVoidAbuse({ days: 30 }),
  });
  const drawer = useQuery({
    queryKey: ["ai-risk", "cash-drawer"],
    queryFn: () => getCashDrawerRisk({ days: 90 }),
  });
  const softpos = useQuery({
    queryKey: ["ai-risk", "softpos-anomalies"],
    queryFn: () => getSoftposAnomalies({ minutes: 60 }),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            void refundVoid.refetch();
            void drawer.refetch();
            void softpos.refetch();
          }}
        >
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <JsonCard title="Refund/void abuse (30d)" data={refundVoid.data} isLoading={refundVoid.isLoading} error={refundVoid.error} />
        <JsonCard title="Cash drawer discrepancies (90d)" data={drawer.data} isLoading={drawer.isLoading} error={drawer.error} />
        <JsonCard title="SoftPOS anomalies (60m)" data={softpos.data} isLoading={softpos.isLoading} error={softpos.error} />
      </div>
    </div>
  );
}

